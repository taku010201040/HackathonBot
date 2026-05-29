################################
# Server
################################

module "server" {
  source = "../../../modules/server/server"

  common = var.common
  discord_server_id = var.discord_server_id
}

################################
# Roles
################################

module "hackathon_roles" {
  source = "../../../modules/hackathon_roles/roles"

  common = var.common
  server = module.server.server
}
