# Week 12 — Task 1: automated environment provisioning

## Implementation

The existing GitHub Actions pipeline was extended to support test and
production. Both environments use shared Terraform code with separate
variable files, backend configurations, VPC CIDRs and resource names.

State is stored under separate S3 keys. Bucket versioning, encryption
and public-access blocking are enabled. S3 lock files protect concurrent
state operations. GitHub Actions concurrency groups are environment-specific.

Manual workflow inputs select the environment and plan/apply/destroy action.
Successful apply operations are followed by the existing post-apply Terratest.

## Confirmed local verification

| Environment | Add | Change | Destroy |
|---|---:|---:|---:|
| test | 14 | 0 | 0 |
| production | 14 | 0 | 0 |

Backend initialization and planning succeeded for both environments.
Terraform formatting and validation also passed.

## Challenges and resolutions

Running Terraform from the repository root did not load the configuration.
Using -chdir=infrastructure selects the correct working directory.

An unset DEPLOY_ENV produced an invalid variables-file path.
Local commands now use explicit environment filenames.

The original SSH key-pair name would conflict between environments.
Names now include the environment prefix.

Separate TF_DATA_DIR directories keep local backend settings independent.

## CI verification

| Operation | Result | Run |
|---|---|---|
| test apply | 14 resources created; all three Terratest checks passed | [45066034858](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45066034858) |
| test destroy | 14 resources deleted | [45067773576](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45067773576) |
| production apply | 13 remaining resources created; all three Terratest checks passed | [45067962325](https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/45067962325) |

The initial production apply reached the regional VPC quota after creating
the SSH key pair. The test environment was destroyed through the pipeline
to release a quota slot. A fresh production apply reused the existing key
pair from state and completed successfully.

Both environments were verified sequentially. Simultaneous operation and
post-deployment no-change plans have not been demonstrated in these runs.

The current Terratest checks infrastructure: VPCs, subnets, instance
placement and database network isolation. It does not verify MariaDB
service readiness.

## Cleanup approach

The manual destroy action removes the selected environment.
Automatic expiry is a possible extension for temporary environments.
