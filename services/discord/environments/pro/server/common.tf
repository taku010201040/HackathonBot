################################
# Common Variables
################################

variable "common" {
  default = {
    "server_name" = "Sample Discord Terraform"
  }
}

variable "discord_token" {
  type = string
  sensitive = true
}
