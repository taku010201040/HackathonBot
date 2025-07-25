################################
# Discord Server
################################

resource "discord_managed_server" "main" {
  server_id = var.discord_server_id
  name = var.common.server_name
  default_message_notifications = 0
}
