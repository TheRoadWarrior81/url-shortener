variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Your root domain name"
  type        = string
}

variable "subdomain" {
  description = "Subdomain for the URL shortener"
  type        = string
  default     = "short"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "url-shortener"
}