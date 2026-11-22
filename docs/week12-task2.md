# Week 12 — Task 2: self-hosted runner

## Infrastructure

Runner infrastructure is managed separately in runner-infrastructure/.
It uses the existing RootVPC and its public subnet in us-east-1a.

The runner uses t3.micro, Ubuntu 24.04 x86_64, a 30 GiB encrypted gp3
root volume and 2 GiB swap. SSH ingress is restricted to the administrator
IPv4 address. The original t3a.small choice was rejected by the account's
Free Tier restrictions.

State: week12/runner/terraform.tfstate.

## Installation

1. Apply runner-infrastructure/ using the local AWS profile.
2. Run install-runner.sh on the EC2 host as root.
3. Generate a registration token in GitHub Settings → Actions → Runners.
4. Run config.sh as the actions user in /opt/actions-runner.
5. Use runner name week12-ec2-runner and custom label week12.
6. Install and start the service with svc.sh using the actions user.
7. Verify that GitHub shows the runner online and idle.

Registration tokens are entered interactively and are not stored in Git
or Terraform configuration.

## Pipeline usage

Select the week12-task2-self-hosted-runner branch and choose the runner,
environment and operation in the manual workflow form.

Self-hosted execution is selected only for workflow_dispatch.
Other events use GitHub-hosted runners by default.

## Troubleshooting

- Offline: inspect svc.sh status and the runner's _diag logs.
- Queued: check labels, service status and whether the runner is busy.
- SSH unavailable: check the current administrator IP and EC2 health.
- High memory pressure: inspect free -h, swap usage and kernel OOM logs.
- Slow execution: inspect CPU credit balance and distinguish cache states.

## Performance and cost comparison

Run the same commit, environment and action on both runner types.
Record queue time, execution time, cache conditions and failures.
