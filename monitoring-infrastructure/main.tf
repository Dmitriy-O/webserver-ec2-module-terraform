locals {
  name = "week13-monitoring"
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
    name   = "state"
    values = ["available"]
  }
}

resource "aws_vpc" "this" {
  cidr_block           = "10.130.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = local.name
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = local.name
  }
}

resource "aws_subnet" "public" {
  availability_zone       = "us-east-1a"
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.130.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name}-public"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${local.name}-public"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "node" {
  name_prefix = "${local.name}-"
  description = "SSH and Kubernetes API from the administrator only"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = local.name
  }
}

resource "aws_vpc_security_group_ingress_rule" "admin" {
  for_each = {
    ssh            = 22
    kubernetes_api = 6443
  }

  security_group_id = aws_security_group.node.id
  description       = each.key
  cidr_ipv4         = var.admin_cidr
  ip_protocol       = "tcp"
  from_port         = each.value
  to_port           = each.value
}

resource "aws_vpc_security_group_egress_rule" "outbound" {
  security_group_id = aws_security_group.node.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_key_pair" "admin" {
  key_name   = local.name
  public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
}

resource "aws_eip" "node" {
  domain = "vpc"

  tags = {
    Name = local.name
  }

  depends_on = [aws_internet_gateway.this]
}

resource "aws_instance" "node" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "m7i-flex.large"
  subnet_id                   = aws_subnet.public.id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.node.id]
  key_name                    = aws_key_pair.admin.key_name
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    public_ip   = aws_eip.node.public_ip
    k3s_version = var.k3s_version
  })

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }


  root_block_device {
    volume_size           = 50
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = local.name
  }

  depends_on = [aws_route_table_association.public]
}

resource "aws_eip_association" "node" {
  instance_id   = aws_instance.node.id
  allocation_id = aws_eip.node.id
}
