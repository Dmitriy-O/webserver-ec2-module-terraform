# Public NAT Gateway for private database instances.
# Both HTTP and DB subnets are located in us-east-1a.

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.environment}-db-nat"
  }
}

resource "aws_nat_gateway" "db" {
  allocation_id     = aws_eip.nat.id
  subnet_id         = aws_subnet.http.id
  connectivity_type = "public"

  # Ensure the public subnet has internet routing before creating NAT.
  depends_on = [
    aws_internet_gateway.gw,
    aws_route_table_association.http,
  ]

  tags = {
    Name = "${var.environment}-db-nat"
  }
}
