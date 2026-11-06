output "alb_dns_name" {
  description = "Application Load Balancer DNS Endpoint"
  value       = aws_lb.app_alb.dns_name
}

output "application_url" {
  description = "Live HTTP URL for the web application"
  value       = "http://${aws_lb.app_alb.dns_name}"
}

output "asg_name" {
  description = "Auto Scaling Group Name"
  value       = aws_autoscaling_group.app_asg.name
}
