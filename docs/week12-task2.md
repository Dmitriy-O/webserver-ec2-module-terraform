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

## Verified benchmark

Implementation commit: `4bd711982128a27dd91143849c4939be80ec5ef5`.

Both runner types executed the same production benchmark:
formatting, validation, TFLint, Trivy, backend initialization,
a no-change Terraform plan and Terratest.

The benchmark never executes Terraform apply or destroy.
A plan containing changes stops the benchmark.

All six measured executions succeeded. Network, EC2Hosts and
DatabasePrivate passed. All plans reported No changes.

## Performance comparison

Each value is the sum of the two job durations calculated from GitHub
started_at and completed_at timestamps. Setup and cleanup are included;
queue time and gaps between jobs are excluded.

| Sample | GitHub-hosted | EC2 self-hosted |
| --- | ---: | ---: |
| 1 | [71 seconds](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45082921948) | [141 seconds](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45082965749) |
| 2 | [80 seconds](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45087104991) | [138 seconds](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45087120182) |
| 3 | [77 seconds](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45087137865) | [137 seconds](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45087154830) |
| Median | 77 seconds | 138 seconds |

The first successful production benchmark on each runner type was
treated as warm-up and excluded:
GitHub-hosted run 45082798862 and self-hosted run 45082868311.

The self-hosted median was 138 / 77 = approximately 1.79 times the
hosted median. No performance improvement was demonstrated.

Go and Trivy caches were restored on both runner types. Around the UTC
date change, Trivy restored the previous day's cache through a fallback
key before saving the new daily key.

Limitations: only three measured runs per type; workflow executions
partly overlapped; CPU-credit balance was not recorded; hardware and
persistent local caches differ. These results describe this lab's
checks/planning/test workload, not initial provisioning speed or all
possible CI workloads.

Cancelled runs, the failed test-environment benchmark and the earlier
apply runs with different resource changes were excluded.

## Team and capacity assumptions

The cost scenario assumes 5 developers and 2 QA engineers, with
20 executions per working day over 22 working days: 440 runs/month.

One registered runner executes one job at a time. The t3.micro worker
completed the lab with limited Go parallelism and swap, but this does
not establish capacity for simultaneous heavy QA suites or builds.

## Cost comparison

Pricing reviewed on 23 November 2026. Currency: USD.
AWS region: us-east-1. Values are estimates before taxes, credits,
Free Tier benefits and additional usage-based charges.

| Always-on self-hosted component | Calculation | Monthly estimate |
| --- | --- | ---: |
| t3.micro Linux | 730 hours x $0.0104 | $7.592 |
| Public IPv4 | 730 hours x $0.005 | $3.650 |
| 30 GiB gp3 | 30 x $0.08 | $2.400 |
| Infrastructure subtotal | | $13.642 |

This is approximately $13.64/month before maintenance, data transfer,
S3 requests, snapshots or optional logging. Task 1 application resources
are separate. This estimate is not an observed AWS invoice.

Standard GitHub-hosted usage is free for this public repository.
Therefore, self-hosting has not demonstrated monetary savings here.

For a hypothetical private repository, the paid standard Linux x64 rate
is $0.006/minute. Each hosted job in the measured series lasted under
one minute; rounding each job separately gives two minutes per run.

If that duration also holds for the private runner configuration:
440 runs x 2 minutes x $0.006 = $5.28/month before included compute.
Private hosted hardware can differ, so this runtime transfer is an
assumption, not a measured private-repository result.

An illustrative maintenance allowance of one engineer-hour/month at
$20/hour raises self-hosted cost to about $33.64/month before extras.
Initial setup labor is excluded.

## Recommendation

Keep hosted execution as the default for this public repository.
The self-hosted option demonstrates control over the execution
environment and successful workflow integration, but this configuration
did not demonstrate faster execution or lower cost.

Self-hosting may be useful for private-network access or custom tooling.
Evaluate those benefits alongside measured capacity and maintenance.
Autoscaling is addressed separately in Task 3.

## Pricing sources

- [GitHub billing](https://docs.github.com/en/actions/concepts/billing-and-usage)
- [GitHub runner rates](https://docs.github.com/en/billing/reference/actions-runner-pricing)
- [AWS T3 rates](https://aws.amazon.com/ec2/instance-types/t3/)
- [AWS IPv4 rates](https://aws.amazon.com/vpc/pricing/)
- [AWS gp3 rates](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-storage-compare-volume-types.html)
