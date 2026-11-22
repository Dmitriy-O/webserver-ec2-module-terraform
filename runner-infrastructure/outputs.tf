output "instance_id" {
  description = "Runner EC2 instance ID."
  value       = aws_instance.runner.id
}

output "public_ip" {
  description = "Runner public IPv4 address."
  value       = aws_instance.runner.public_ip
}
