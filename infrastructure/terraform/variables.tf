variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name for resources"
  type        = string
  default     = "aws-asg-webapp"
}

variable "instance_type" {
  description = "EC2 instance size"
  type        = string
  default     = "t3.micro"
}
