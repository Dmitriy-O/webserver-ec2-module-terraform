resource "aws_key_pair" "user_key" {
  key_name   = "${local.name_prefix}-key"
  public_key = var.public_key
}
