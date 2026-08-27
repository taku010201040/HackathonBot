################################
# Common Variables
################################

variable "common" {
  default = {
    "server_name" = "DISRUPT AI Hackathon"
  }
}

variable "discord_token" {
  type = string
  sensitive = true
}
