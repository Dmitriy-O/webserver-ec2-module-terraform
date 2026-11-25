variable "admin_cidr" {
  description = "Your current public IPv4 address followed by /32."
  type        = string

  validation {
    condition = (
      can(cidrnetmask(var.admin_cidr)) &&
      endswith(var.admin_cidr, "/32")
    )
    error_message = "Provide one valid IPv4 address as x.x.x.x/32."
  }
}

variable "ssh_public_key_path" {
  description = "Absolute path to the public SSH key."
  type        = string
}

variable "k3s_version" {
  description = "Pinned K3s release."
  type        = string
  default     = "v1.37.2+k3s1"
}
