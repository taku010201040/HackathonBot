variable "sample_event" {
  type = map(string)
  default = {
    name = "Sample Event"
  }
}

variable "discord_server_id" {
  type = string
  sensitive = false
}

variable "gitlab_remote_state_address" {
  type = string
  sensitive = false
}

variable "gitlab_username" {
  type = string
  sensitive = true
}

variable "gitlab_access_token" {
  type = string
  sensitive = true
}
