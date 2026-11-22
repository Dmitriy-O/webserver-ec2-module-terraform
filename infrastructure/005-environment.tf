variable "environment" {
  description = "Deployment environment."
  type        = string

  validation {
    condition     = contains(["test", "production"], var.environment)
    error_message = "Environment must be test or production."
  }
}

locals {
  name_prefix = "week12-${var.environment}"
}
