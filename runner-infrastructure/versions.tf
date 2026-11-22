terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.73.0"
    }
  }

  backend "s3" {
    bucket       = "week11-tfstate-047472448571-dmitriy-o"
    key          = "week12/runner/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = ["047472448571"]

  default_tags {
    tags = {
      Project     = "week12"
      Environment = "ci"
      ManagedBy   = "Terraform"
    }
  }
}
