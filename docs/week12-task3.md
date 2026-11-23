# Week 12 — Task 3: autoscaling GitHub Actions runners

Verified on 23 November 2026.
Implementation commit: `8f4fa4f56fe6fce5d9f56956f0c0914cc594be14`.

## Implementation

The existing Terraform workflow supports runner=autoscaling and invokes
.github/workflows/autoscaling-pool.yml.

A GitHub-hosted preparation job provisions the requested capacity.
One or two ephemeral EC2 runners execute the existing CI checks.
A GitHub-hosted cleanup job returns the pool to zero after completion,
including when CI fails.

Capacity is derived from the number of CI jobs requested by this workflow.
This is bounded workflow-driven scaling, not a repository-wide queue scaler.

## Infrastructure

- Terraform root: autoscaling-runner-infrastructure/.
- State key: week12/runner-autoscaling/terraform.tfstate.
- ASG: week12-autoscaling-runner.
- Capacity: minimum 0, maximum 2.
- Existing RootVPC and public subnet in us-east-1a.
- Ubuntu 24.04 x86_64, t3.micro, 30 GiB encrypted gp3 and 2 GiB swap.
- Outbound HTTP/HTTPS; no inbound rules for the temporary workers.
- Separate temporary Launch Template for each workflow execution.
- No EC2 instance profile; orchestration uses hosted-job AWS credentials.

Terraform manages the baseline infrastructure. The workflow controls
desired capacity and the temporary Launch Template selection.

## Registration and credentials

RUNNER_ADMIN_TOKEN is a repository secret with permission to manage
repository runners. It is used only by the hosted orchestration jobs.

The controller obtains a short-lived registration token and configures
each worker with --ephemeral and a unique execution label.
The registration token is placed in the temporary EC2 user data,
not committed to Git or managed in Terraform state.

Each worker processes one job. Cleanup terminates the pool, restores
the base Launch Template and removes the temporary template.

## How to run

1. Ensure production exists and has a no-change Terraform plan.
   If needed, use runner=github-hosted, environment=production, action=apply.
2. Open Week 12 Terraform and select this branch.
3. Choose runner=autoscaling, environment=production and action=benchmark.
4. Select parallel_jobs=1 or 2.
5. Wait for preparation, CI and cleanup to complete.
6. Confirm DesiredCapacity=0 and an empty ASG instance list.

The autoscaling mode accepts benchmark only. It runs checks and
read-only infrastructure tests without applying application changes.

## Verified executions

| Workers | Workflow run | Startup to online | CI job durations | Cleanup |
| --- | --- | --- | --- | --- |
| 1 | [45094098330](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45094098330) | 364 seconds | 1195 seconds | Success; ASG empty |
| 2 | [45095534094](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45095534094) | 343 seconds | 490 and 679 seconds | Success; ASG empty |

Startup is measured by the controller until all requested runners
are observed online. It includes provisioning, software installation
and registration, but excludes the preceding hosted Terraform preflight.

CI durations include job setup and post-job steps.
The two-worker CI jobs both started at 01:55:25 UTC on different instances:

- i-03a4503c25c19d2d1
- i-079a54ceae7bc9af5

All three worker jobs passed formatting, validation, TFLint, Trivy,
no-change planning and the Network, EC2Hosts and DatabasePrivate
Terratest subtests.

Both cleanup jobs confirmed Desired=0 and Instances=0 and reported
removal of the temporary Launch Template.

## Setup speed and availability comparison

The persistent Task 2 runner has one execution slot and can accept jobs
while it is online. Its original cold startup was not benchmarked.

The Task 3 pool demonstrated one or two simultaneous execution slots.
Starting from zero required approximately six minutes in these samples.
Returning to zero removes idle worker capacity, so subsequent executions
must wait for provisioning again.

The second workflow waited for the previous workflow to release the shared
pool. That wait is separate from the reported controller startup duration.

These runs demonstrate parallel availability and automatic scale-in.
They do not establish high availability: the pool uses one Availability Zone,
and no host-failure recovery test was performed.

## Measurement limitations

Only one execution was measured at each capacity.
The first worker missed Trivy and Go caches; the second execution restored
them. CPU-credit balance was not recorded.

Therefore, the differing CI durations do not prove a scaling-related
speedup or equivalent per-worker performance. The combined CI job also
differs from the two-job structure used for Task 2 timing measurements.

## Challenges and fixes

- IAM role and CloudWatch log-group creation were denied.
  Orchestration was moved to hosted jobs without creating those resources.
- Production had been destroyed after Task 2.
  It was recreated before the no-change benchmark.
- AWS selected us-east-1e for the DB subnet and rejected t3.micro there.
  The DB subnet was pinned to the supported us-east-1a zone.
- Autoscaling with action=apply was rejected by input validation.
  Application provisioning and runner benchmarking use separate modes.

## Operational limitations

Cleanup uses an always() job on a hosted runner.
Force-cancellation or control-plane failure may still require manual
cleanup with scripts/autoscaling_pool.py stop for the affected run key.

The ephemeral runner pool is separate from the application environment
and the persistent Task 2 runner. Emptying this ASG does not delete those
other resources.
