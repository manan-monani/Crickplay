# ============================================
# Variables
# ============================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "crickplay"
}

# --- Networking ---
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

# --- EC2 ---
variable "ec2_instance_type" {
  description = "EC2 instance type for app server"
  type        = string
  default     = "t3.large" # 2 vCPU, 8GB RAM — enough for Docker stack
}

variable "ec2_key_name" {
  description = "Name of the SSH key pair to create"
  type        = string
  default     = "crickplay-key"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH access (your IP)"
  type        = string
  default     = "0.0.0.0/0" # Restrict this in production!
}

# --- RDS ---
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # Free tier eligible
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "crickplay"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "crickplay_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

# --- ElastiCache ---
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro" # Free tier eligible
}
