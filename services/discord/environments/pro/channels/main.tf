################################
# Default Channels
################################

module "default_channels" {
  source = "../../../modules/default_channels/channels"

  common = var.common
  server = data.terraform_remote_state.server.outputs.server
}


################################
# Event Channels
################################

module "sample_event_channels" {
  source = "../../../modules/event_channels/channels"

  common = var.common
  server = data.terraform_remote_state.server.outputs.server
  event = var.sample_event
}
