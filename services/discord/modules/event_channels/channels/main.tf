################################
# Category
################################

resource "discord_category_channel" "main" {
  server_id = var.server.id
  name = "--- ${var.event.name} ---"
  position = 2
}


################################
# Text Channels
################################

resource "discord_text_channel" "tech_selection" {
  server_id = var.server.id
  name = "🔧｜技術選定"
  category = discord_category_channel.main.id
  position = 1
}

resource "discord_text_channel" "development" {
  server_id = var.server.id
  name = "💻｜開発"
  category = discord_category_channel.main.id
  position = 2
}

resource "discord_text_channel" "presentation" {
  server_id = var.server.id
  name = "📊｜発表"
  category = discord_category_channel.main.id
  position = 3
}

resource "discord_text_channel" "document" {
  server_id = var.server.id
  name = "📃｜資料"
  category = discord_category_channel.main.id
  position = 4
}

resource "discord_text_channel" "webhook" {
  server_id = var.server.id
  name = "🔔｜webhook"
  category = discord_category_channel.main.id
  position = 5
}
