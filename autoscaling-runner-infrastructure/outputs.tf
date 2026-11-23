output "autoscaling_group_name" {
  value = aws_autoscaling_group.runner.name
}

output "launch_template_id" {
  value = aws_launch_template.runner.id
}
