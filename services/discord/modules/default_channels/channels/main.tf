################################
# Category
################################

resource "discord_category_channel" "text" {
  server_id = var.server.id
  name = "--- テキストチャンネル ---"
  position = 1
}

resource "discord_category_channel" "voice" {
  server_id = var.server.id
  name = "--- ボイスチャンネル ---"
  position = 999
}


################################
# Text Channels
################################

resource "discord_text_channel" "general" {
  server_id = var.server.id
  name = "💬｜一般"
  category = discord_category_channel.text.id
  position = 0
}

resource "discord_text_channel" "idea_cloud" {
  server_id = var.server.id
  name = "☁｜アイデアクラウド"
  category = discord_category_channel.text.id
  position = 10
}

resource "discord_text_channel" "chat" {
  server_id = var.server.id
  name = "🗣｜雑談"
  category = discord_category_channel.text.id
  position = 999
}


################################
# Voice Channels
################################

resource "discord_text_channel" "listen" {
  server_id = var.server.id
  name = "👂｜聴き専"
  category = discord_category_channel.voice.id
  position = 0
}

resource "discord_text_channel" "notification" {
  server_id = var.server.id
  name = "☎｜通話通知"
  category = discord_category_channel.voice.id
  position = 1
}

resource "discord_voice_channel" "general" {
  server_id = var.server.id
  name = "💬｜一般"
  category = discord_category_channel.voice.id
  position = 10
}

resource "discord_voice_channel" "work" {
  server_id = var.server.id
  name = "💻｜作業"
  category = discord_category_channel.voice.id
  position = 11
}

resource "discord_voice_channel" "voice" {
  server_id = var.server.id
  name = "🗣｜雑談"
  category = discord_category_channel.voice.id
  position = 12
}

resource "discord_voice_channel" "no_notification" {
  server_id = var.server.id
  name = "🔕｜通知なし"
  category = discord_category_channel.voice.id
  position = 13
}
