################################
# Server
################################

module "server" {
  source = "../../../modules/server/server"

  common = var.common
  discord_server_id = var.discord_server_id
}
