################################
# ADMIN ROLES
################################
resource "discord_role" "admin_core" {
  server_id   = var.server.id
  name        = "👑 運営統括"
  permissions = 8 # Administrator
  color       = 15158332 # Red
  hoist       = true
  mentionable = true
}
resource "discord_role" "admin_member" {
  server_id   = var.server.id
  name        = "🤝 運営メンバー"
  color       = 15158332
  hoist       = true
  mentionable = true
}
resource "discord_role" "admin_plan" {
  server_id   = var.server.id
  name        = "📜 企画・進行班"
  color       = 15158332
  hoist       = true
  mentionable = true
}
resource "discord_role" "admin_pr" {
  server_id   = var.server.id
  name        = "📰 広報班"
  color       = 15158332
  hoist       = true
  mentionable = true
}
resource "discord_role" "admin_ext" {
  server_id   = var.server.id
  name        = "🌍 外部連携班"
  color       = 15158332
  hoist       = true
  mentionable = true
}
resource "discord_role" "staff" {
  server_id   = var.server.id
  name        = "🎗️ スタッフ"
  color       = 15158332
  hoist       = true
  mentionable = true
}

################################
# PARTNERS
################################
resource "discord_role" "sponsor" {
  server_id   = var.server.id
  name        = "🏢 協賛スポンサー"
  color       = 1752220 # Gold
  hoist       = true
  mentionable = true
}
resource "discord_role" "mentor" {
  server_id   = var.server.id
  name        = "👨‍🏫 メンター"
  color       = 3447003 # Blue
  hoist       = true
  mentionable = true
}
resource "discord_role" "judge" {
  server_id   = var.server.id
  name        = "🏆 審査員"
  color       = 3447003
  hoist       = true
  mentionable = true
}

################################
# PARTICIPANTS
################################
resource "discord_role" "participant_p1" {
  server_id   = var.server.id
  name        = "🧑‍🎓 参加者（Phase1）"
  color       = 3066993 # Green
  hoist       = true
  mentionable = true
}
resource "discord_role" "participant_p2" {
  server_id   = var.server.id
  name        = "🧑‍🎓 参加者（Phase2）"
  color       = 3066993
  hoist       = true
  mentionable = true
}
resource "discord_role" "participant_p3" {
  server_id   = var.server.id
  name        = "🧑‍🎓 参加者（Phase3）"
  color       = 3066993
  hoist       = true
  mentionable = true
}

################################
# SKILL TAGS (Not Hoisted)
################################
resource "discord_role" "skill_design" {
  server_id   = var.server.id
  name        = "🎨 デザイン"
  color       = 15277667 # Pink
  hoist       = false
  mentionable = false
}
resource "discord_role" "skill_eng" {
  server_id   = var.server.id
  name        = "💻 エンジニア"
  color       = 1146986 # Dark Cyan
  hoist       = false
  mentionable = false
}
resource "discord_role" "skill_biz" {
  server_id   = var.server.id
  name        = "📊 ビジネス・企画"
  color       = 3447003 # Blue
  hoist       = false
  mentionable = false
}

################################
# EXTRA ROLES
################################
resource "discord_role" "guest" {
  server_id   = var.server.id
  name        = "👀 ゲスト・見学者"
  color       = 9807270 # Grey
  hoist       = true
  mentionable = true
}
resource "discord_role" "award" {
  server_id   = var.server.id
  name        = "🏆 アワード受賞者"
  color       = 1752220 # Gold
  hoist       = true
  mentionable = true
}
resource "discord_role" "mute" {
  server_id   = var.server.id
  name        = "🔇 ミュート（発言制限）"
  color       = 0 # Default
  hoist       = false
  mentionable = false
}

################################
# GENDER ROLES
################################
resource "discord_role" "gender_male" {
  server_id   = var.server.id
  name        = "🚹 男"
  color       = 3447003 # Blue
  hoist       = false
  mentionable = false
}
resource "discord_role" "gender_female" {
  server_id   = var.server.id
  name        = "🚺 女"
  color       = 15277667 # Pink
  hoist       = false
  mentionable = false
}

################################
# GRAD YEAR ROLES
################################
resource "discord_role" "grad_27" {
  server_id   = var.server.id
  name        = "🎓 27卒"
  color       = 9807270 # Grey
  hoist       = false
  mentionable = false
}
resource "discord_role" "grad_28" {
  server_id   = var.server.id
  name        = "🎓 28卒"
  color       = 9807270 # Grey
  hoist       = false
  mentionable = false
}
resource "discord_role" "grad_29" {
  server_id   = var.server.id
  name        = "🎓 29卒"
  color       = 9807270 # Grey
  hoist       = false
  mentionable = false
}
resource "discord_role" "grad_30" {
  server_id   = var.server.id
  name        = "🎓 30卒"
  color       = 9807270 # Grey
  hoist       = false
  mentionable = false
}

################################
# AI TOOLS ROLES
################################
resource "discord_role" "ai_chatgpt" { server_id = var.server.id, name = "🤖 ChatGPT", hoist = false, mentionable = false }
resource "discord_role" "ai_claude" { server_id = var.server.id, name = "🤖 Claude", hoist = false, mentionable = false }
resource "discord_role" "ai_gemini" { server_id = var.server.id, name = "🤖 Gemini", hoist = false, mentionable = false }
resource "discord_role" "ai_notion" { server_id = var.server.id, name = "🤖 Notion AI", hoist = false, mentionable = false }
resource "discord_role" "ai_copilot" { server_id = var.server.id, name = "🤖 GitHub Copilot", hoist = false, mentionable = false }
resource "discord_role" "ai_cursor" { server_id = var.server.id, name = "🤖 Cursor", hoist = false, mentionable = false }
resource "discord_role" "ai_midjourney" { server_id = var.server.id, name = "🤖 Midjourney", hoist = false, mentionable = false }
resource "discord_role" "ai_sd" { server_id = var.server.id, name = "🤖 Stable Diffusion", hoist = false, mentionable = false }

################################
# PROGRAMMING LANGUAGES ROLES
################################
resource "discord_role" "lang_python" { server_id = var.server.id, name = "💻 Python", hoist = false, mentionable = false }
resource "discord_role" "lang_js" { server_id = var.server.id, name = "💻 JavaScript", hoist = false, mentionable = false }
resource "discord_role" "lang_ts" { server_id = var.server.id, name = "💻 TypeScript", hoist = false, mentionable = false }
resource "discord_role" "lang_go" { server_id = var.server.id, name = "💻 Go", hoist = false, mentionable = false }
resource "discord_role" "lang_rust" { server_id = var.server.id, name = "💻 Rust", hoist = false, mentionable = false }
resource "discord_role" "lang_cpp" { server_id = var.server.id, name = "💻 C++", hoist = false, mentionable = false }
resource "discord_role" "lang_java" { server_id = var.server.id, name = "💻 Java", hoist = false, mentionable = false }
resource "discord_role" "lang_ruby" { server_id = var.server.id, name = "💻 Ruby", hoist = false, mentionable = false }
resource "discord_role" "lang_php" { server_id = var.server.id, name = "💻 PHP", hoist = false, mentionable = false }
resource "discord_role" "lang_htmlcss" { server_id = var.server.id, name = "💻 HTML/CSS", hoist = false, mentionable = false }
