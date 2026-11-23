#!/usr/bin/env python3
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

REGION = "us-east-1"
ACCOUNT = "047472448571"
GROUP = "week12-autoscaling-runner"
BASE_TEMPLATE = "lt-048fe32fd592ace1d"
REPO = "Dmitriy-O/webserver-ec2-module-terraform"
ROOT = Path(__file__).resolve().parents[1]


def aws(*args):
    p = subprocess.run(
        ["aws", "--region", REGION, "--no-cli-pager", "--output", "json", *args],
        text=True, capture_output=True,
    )
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return json.loads(p.stdout) if p.stdout.strip() else {}


def github(path, method="GET"):
    token = os.environ["RUNNER_ADMIN_TOKEN"]
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/runners{path}",
        data=b"{}" if method == "POST" else None,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body) if body else {}


def group():
    groups = aws(
        "autoscaling", "describe-auto-scaling-groups",
        "--auto-scaling-group-names", GROUP,
    )["AutoScalingGroups"]
    if len(groups) != 1:
        raise RuntimeError("Expected exactly one configured ASG")
    return groups[0]


def runners(label):
    result = []
    for page in range(1, 101):
        batch = github(f"?per_page=100&page={page}")["runners"]
        result.extend(
            r for r in batch
            if label in [x["name"] for x in r["labels"]]
        )
        if len(batch) < 100:
            return result
    raise RuntimeError("Runner pagination limit exceeded")


def userdata(key, label, token):
    scripts = [
        ROOT / "runner-infrastructure/bootstrap.sh",
        ROOT / "runner-infrastructure/install-runner.sh",
    ]
    body = "\n".join(p.read_text().rstrip() for p in scripts)
    body += f"""
RUN_KEY={shlex.quote(key)}
REGISTRATION_TOKEN={shlex.quote(token)}
METADATA_TOKEN=$(curl -fsS --retry 3 --max-time 15 -X PUT \\
  -H 'X-aws-ec2-metadata-token-ttl-seconds: 300' \\
  http://169.254.169.254/latest/api/token)
INSTANCE_ID=$(curl -fsS --retry 3 --max-time 15 \\
  -H "X-aws-ec2-metadata-token: $METADATA_TOKEN" \\
  http://169.254.169.254/latest/meta-data/instance-id)
cd /opt/actions-runner
sudo -H -u actions ./config.sh --unattended \\
  --url https://github.com/{REPO} \\
  --token "$REGISTRATION_TOKEN" \\
  --name "w12-$RUN_KEY-$INSTANCE_ID" \\
  --labels "week12-autoscale,{label}" --work _work --ephemeral
unset REGISTRATION_TOKEN
sudo -H -u actions ./run.sh
echo 'Ephemeral runner finished; awaiting hosted workflow cleanup.'
"""
    if len(body.encode()) > 16384:
        raise RuntimeError("EC2 user data exceeds 16 KiB")
    return base64.b64encode(body.encode()).decode()


def start(key, count):
    started = time.monotonic()
    state = group()
    if state["DesiredCapacity"] or state["Instances"] or state["MinSize"] != 0:
        raise RuntimeError("Pool is not empty; refusing to replace existing workers")
    if state["MaxSize"] != 2:
        raise RuntimeError("Expected ASG maximum size of two")

    label = f"week12-asg-{key}"
    token = github("/registration-token", "POST")["token"]
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::add-mask::{token}", flush=True)

    data = aws(
        "ec2", "describe-launch-template-versions",
        "--launch-template-id", BASE_TEMPLATE,
        "--versions", "$Default",
    )["LaunchTemplateVersions"][0]["LaunchTemplateData"]

    if data.get("IamInstanceProfile"):
        raise RuntimeError("Base template unexpectedly contains an instance profile")
    data["UserData"] = userdata(key, label, token)

    with tempfile.TemporaryDirectory() as directory:
        payload = Path(directory) / "launch.json"
        payload.write_text(json.dumps(data))
        payload.chmod(0o600)
        template = aws(
            "ec2", "create-launch-template",
            "--launch-template-name", f"week12-asg-run-{key}",
            "--launch-template-data", f"file://{payload}",
            "--tag-specifications",
            "ResourceType=launch-template,Tags=[{Key=Project,Value=week12},{Key=Environment,Value=ci}]",
        )["LaunchTemplate"]

    aws(
        "autoscaling", "update-auto-scaling-group",
        "--auto-scaling-group-name", GROUP,
        "--launch-template",
        f"LaunchTemplateId={template['LaunchTemplateId']},Version=1",
        "--desired-capacity", str(count),
    )

    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        online = [r for r in runners(label) if r["status"] == "online"]
        print(f"Online runners: {len(online)}/{count}", flush=True)
        if len(online) == count:
            seconds = round(time.monotonic() - started)
            outputs = {
                "label": label,
                "startup_seconds": str(seconds),
                "count": str(count),
                "matrix": json.dumps(list(range(1, count + 1))),
            }
            if os.environ.get("GITHUB_OUTPUT"):
                with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                    for name, value in outputs.items():
                        output.write(f"{name}={value}\n")
            print(f"Pool ready: {count} runners in {seconds} seconds", flush=True)
            return
        time.sleep(15)

    raise RuntimeError("Runner startup exceeded 15 minutes; cleanup is required")


def stop(key):
    name = f"week12-asg-run-{key}"
    label = f"week12-asg-{key}"
    state = group()
    current_id = state["LaunchTemplate"]["LaunchTemplateId"]
    current = aws(
        "ec2", "describe-launch-templates",
        "--launch-template-ids", current_id,
    )["LaunchTemplates"][0]

    if current["LaunchTemplateName"] == name:
        aws(
            "autoscaling", "update-auto-scaling-group",
            "--auto-scaling-group-name", GROUP,
            "--desired-capacity", "0", "--min-size", "0",
        )
        deadline = time.monotonic() + 600
        while group()["Instances"]:
            if time.monotonic() > deadline:
                raise RuntimeError("Timed out waiting for ASG scale-in")
            time.sleep(10)
        aws(
            "autoscaling", "update-auto-scaling-group",
            "--auto-scaling-group-name", GROUP,
            "--launch-template",
            f"LaunchTemplateId={BASE_TEMPLATE},Version=$Default",
        )
    elif state["DesiredCapacity"] or state["Instances"]:
        raise RuntimeError("Pool belongs to another run; refusing to stop it")

    templates = aws(
        "ec2", "describe-launch-templates",
        "--filters", f"Name=launch-template-name,Values={name}",
    )["LaunchTemplates"]

    for template in templates:
        if template["LaunchTemplateId"] == group()["LaunchTemplate"]["LaunchTemplateId"]:
            raise RuntimeError("Refusing to delete a template still assigned to the ASG")
        aws(
            "ec2", "delete-launch-template",
            "--launch-template-id", template["LaunchTemplateId"],
        )

    if os.environ.get("RUNNER_ADMIN_TOKEN"):
        for runner in runners(label):
            if runner["busy"]:
                raise RuntimeError("Matching runner is unexpectedly busy")
            github(f"/{runner['id']}", "DELETE")

    print("Cleanup complete: pool empty; per-run launch template removed.", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["start", "stop"])
    parser.add_argument("--run-key", required=True)
    parser.add_argument("--count", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9]+-[0-9]+", args.run_key):
        parser.error("run-key must be RUN_ID-RUN_ATTEMPT")
    if aws("sts", "get-caller-identity")["Account"] != ACCOUNT:
        raise RuntimeError("Unexpected AWS account")

    if args.operation == "start":
        start(args.run_key, args.count)
    else:
        stop(args.run_key)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, urllib.error.URLError) as error:
        sys.exit(str(error))
