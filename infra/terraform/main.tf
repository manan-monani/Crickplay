# ============================================
# Crickplay — AWS Infrastructure (Terraform)
# ============================================
# Cost-optimized dev/staging environment
# Region: ap-south-1 (Mumbai)
# ============================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Local state for now (can move to S3 backend later)
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "crickplay"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
