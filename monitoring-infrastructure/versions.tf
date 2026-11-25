terraform {
  required_version = ">= 1.11, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.73.0"
    }
  }
}

provider "aws" {
  region              = "us-east-1"
  profile             = "terraform_lab_user"
  allowed_account_ids = ["047472448571"]

  default_tags {
    tags = {
      Project   = "week13-monitoring"
      ManagedBy = "Terraform"
      Purpose   = "monitoring-lab"
    }
  }
}
