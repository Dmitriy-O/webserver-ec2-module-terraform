output "public_ip" {
  value = aws_eip.node.public_ip
}

output "instance_id" {
  value = aws_instance.node.id
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/week13-monitoring ubuntu@${aws_eip.node.public_ip}"
}
