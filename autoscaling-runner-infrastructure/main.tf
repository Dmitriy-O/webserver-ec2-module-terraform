locals {
  name      = "week12-autoscaling-runner"
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

resource "aws_security_group" "runner" {
  name        = local.name
  description = "Outbound access for ephemeral GitHub Actions runners"
  vpc_id      = local.vpc_id
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

resource "aws_launch_template" "runner" {
  name_prefix            = "${local.name}-"
  image_id               = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  update_default_version = true

  network_interfaces {
    device_index                = 0
    associate_public_ip_address = true
    delete_on_termination       = true
    security_groups             = [aws_security_group.runner.id]
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  block_device_mappings {
    device_name = data.aws_ami.ubuntu.root_device_name

    ebs {
      volume_type           = "gp3"
      volume_size           = 30
      encrypted             = true
      delete_on_termination = true
    }
  }

  credit_specification {
    cpu_credits = "standard"
  }

  user_data = filebase64("${path.module}/../runner-infrastructure/bootstrap.sh")

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name        = local.name
      Project     = "week12"
      Environment = "ci"
      ManagedBy   = "Terraform"
    }
  }

  depends_on = [
    aws_vpc_security_group_egress_rule.http,
    aws_vpc_security_group_egress_rule.https,
  ]
}

resource "aws_autoscaling_group" "runner" {
  name                      = local.name
  min_size                  = 0
  max_size                  = 2
  desired_capacity          = 0
  vpc_zone_identifier       = [local.subnet_id]
  health_check_type         = "EC2"
  health_check_grace_period = 300
  wait_for_capacity_timeout = "0"

  launch_template {
    id      = aws_launch_template.runner.id
    version = aws_launch_template.runner.latest_version
  }

  tag {
    key                 = "Name"
    value               = local.name
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = "week12"
    propagate_at_launch = true
  }

  lifecycle {
    ignore_changes = [desired_capacity]

    precondition {
      condition     = data.aws_subnet.selected.vpc_id == local.vpc_id
      error_message = "The selected subnet must belong to the configured VPC."
    }
  }
}
