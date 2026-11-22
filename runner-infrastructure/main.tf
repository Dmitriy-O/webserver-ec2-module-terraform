variable "ssh_public_key" {
  description = "Public SSH key for runner administration."
  type        = string
}

variable "admin_cidr" {
  description = "Administrator public IPv4 address in /32 notation."
  type        = string

  validation {
    condition = (
      can(cidrnetmask(var.admin_cidr)) &&
      endswith(var.admin_cidr, "/32")
    )
    error_message = "Use one IPv4 address with a /32 prefix."
  }
}

variable "instance_type" {
  description = "EC2 instance type for the self-hosted runner."
  type        = string
  default     = "t3.micro"
}

locals {
  name      = "week12-actions-runner"
  vpc_id    = "vpc-0b957aca7f342cac6"
  subnet_id = "subnet-0a7318510fd7d4586"
}

data "aws_subnet" "selected" {
  id = local.subnet_id
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "runner" {
  key_name   = "${local.name}-key"
  public_key = var.ssh_public_key
}

resource "aws_security_group" "runner" {
  name        = local.name
  description = "Network access for the GitHub Actions runner"
  vpc_id      = local.vpc_id

  tags = {
    Name = local.name
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.runner.id
  description       = "SSH from the administrator IPv4 address"
  cidr_ipv4         = var.admin_cidr
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "http" {
  security_group_id = aws_security_group.runner.id
  description       = "HTTP package downloads"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.runner.id
  description       = "GitHub, AWS APIs and HTTPS downloads"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_instance" "runner" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = aws_key_pair.runner.key_name
  vpc_security_group_ids      = [aws_security_group.runner.id]

  user_data                   = file("${path.module}/bootstrap.sh")
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    encrypted             = true
    delete_on_termination = true
  }

  credit_specification {
    cpu_credits = "standard"
  }

  lifecycle {
    precondition {
      condition     = data.aws_subnet.selected.vpc_id == local.vpc_id
      error_message = "The selected subnet must belong to the configured VPC."
    }
  }

  depends_on = [
    aws_vpc_security_group_egress_rule.http,
    aws_vpc_security_group_egress_rule.https,
  ]

  tags = {
    Name = local.name
  }
}
