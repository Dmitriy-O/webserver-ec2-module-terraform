# Automated environment provisioning

This project provisions test and production environments through GitHub
Actions and Terraform. Each configured environment contains one VPC,
two subnets, one HTTP EC2 instance and one DB EC2 instance.

See [the Task 1 report](docs/week12-task1.md) for verified runs and quota recovery.

## Week 12: multiple environments

The GitHub Actions workflow is defined in
`.github/workflows/terraform.yml`.

Supported environments:

| Environment | Configuration | S3 state key |
|---|---|---|
| test | infrastructure/environments/test.tfvars | week12/test/terraform.tfstate |
| production | infrastructure/environments/production.tfvars | week12/production/terraform.tfstate |

Both environments use the same Terraform code with separate configuration,
VPCs, instance names, SSH key-pair names and Terraform state.

### Prerequisites

- Access to the AWS account and the configured S3 backend bucket.
- Terraform and AWS CLI for local operations.
- GitHub repository secrets: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.
- GitHub Environments named test and production.

The backend bucket must have versioning, encryption and public-access
blocking enabled. Backend access requires listing the relevant bucket
prefix, reading/writing state, and reading/writing/deleting lock objects.

### Pipeline usage

Pushes to main and week12-* branches run checks and plan for test.
Pull requests to main run configuration checks.

For a manual operation, open GitHub Actions, select the workflow,
select the project branch, choose environment and action, then run it.

Actions:
- plan: inspect proposed changes.
- apply: create/update the selected environment, then run Terratest.
- destroy: delete resources tracked by the selected environment state.

Operations for the same environment share a concurrency group.
S3 lock files also coordinate Terraform clients outside GitHub Actions.

### Adding another environment

1. Add an environment configuration under infrastructure/environments/.
2. Add a matching .s3.tfbackend file with a new, unique state key.
3. Add the environment to the validation in 005-environment.tf.
4. Add it to the workflow_dispatch environment choices.
5. Add a targeted .gitignore exception for its non-secret .tfvars file.
6. Create the matching GitHub Environment and configure access.
7. Ensure IAM permissions cover its state and lock paths.
8. Run plan, review the changes, then apply and verify.

Keep credentials outside committed configuration.

### Local operations

Always run Terraform with -chdir=infrastructure from the repository root.
Pass matching .tfvars and .s3.tfbackend files.
Set TF_DATA_DIR to an environment-specific directory under
infrastructure/.terraform/.

### Cleanup

Run the workflow manually with action=destroy and the selected environment.
Repeat for the other environment when it is no longer needed.

Keep the backend bucket while any managed infrastructure remains.
