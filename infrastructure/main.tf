provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "week12"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
