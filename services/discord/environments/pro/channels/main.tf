################################
# Hackathon Channels
################################

module "hackathon_channels" {
  source = "../../../modules/hackathon_channels/channels"

  common = var.common
  server = data.terraform_remote_state.server.outputs.server
}
