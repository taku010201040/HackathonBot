terraform {
  required_providers {
    discord = {
      source = "Lucky3028/discord"
      version = "2.1.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

################################
# Networks Remote State
################################

data "terraform_remote_state" "server" {
  backend = "local"
  
  config = {
    path = "../server/terraform.tfstate"
  }
}
