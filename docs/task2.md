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
