# Task 2 — Terraform quality and security checks

TFLint and Trivy run in the checks job before Terraform planning.
Failure of a check prevents the AWS job from running.

EC2 instances require IMDSv2 and encrypted root volumes.
SSH ingress is restricted to the VPC CIDR.
Database port 3306 accepts traffic from the web security group.

Two resource-level exceptions for AVD-AWS-0104 allow outbound TCP
80 and 443 for Ubuntu package repositories. These rules permit
connections to public IP addresses on the specified ports.
Other outbound access is limited to the required database connection.

Trivy blocks findings with HIGH and CRITICAL severity.

## Post-apply Terratest

After a successful manual apply, the workflow runs:
go test -v -count=1 -timeout 10m ./...

The tests read Terraform outputs and inspect actual AWS resources:
- Network: VPC and subnet CIDRs, subnet membership.
- EC2Hosts: HTTP and DB instances are running in the expected subnets.
- DatabasePrivate: DB instances have no public addresses and port 3306
  accepts traffic only from the web security group.

All three tests passed:
https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/44979303927

Manual destroy successfully removed all 18 managed resources:
https://github.com/Dmitriy-O/webserver-ec2-module-terraform/actions/runs/44979694299
