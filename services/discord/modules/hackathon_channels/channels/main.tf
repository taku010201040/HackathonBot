################################
# 1. WELCOME & ONBOARDING
################################
resource "discord_category_channel" "welcome" {
  server_id = var.server.id
  name      = "🚀 WELCOME & ONBOARDING"
  position  = 1
}

resource "discord_text_channel" "welcome_hello" {
  server_id = var.server.id
  name      = "🏁｜ようこそ"
  category  = discord_category_channel.welcome.id
  position  = 1
}

resource "discord_text_channel" "welcome_role" {
  server_id = var.server.id
  name      = "✅｜ロール付与"
  category  = discord_category_channel.welcome.id
  position  = 2
}

resource "discord_text_channel" "welcome_guide" {
  server_id = var.server.id
  name      = "🗺️｜歩き方ガイド"
  category  = discord_category_channel.welcome.id
  position  = 3
}

################################
# 2. ANNOUNCEMENTS
################################
resource "discord_category_channel" "announcements" {
  server_id = var.server.id
  name      = "📢 ANNOUNCEMENTS"
  position  = 2
}

resource "discord_text_channel" "announce_all" {
  server_id = var.server.id
  name      = "🔔｜全体アナウンス"
  category  = discord_category_channel.announcements.id
  position  = 1
}

resource "discord_text_channel" "announce_calendar" {
  server_id = var.server.id
  name      = "📅｜イベントカレンダー"
  category  = discord_category_channel.announcements.id
  position  = 2
}

resource "discord_text_channel" "announce_award" {
  server_id = var.server.id
  name      = "🏆｜審査・アワード情報"
  category  = discord_category_channel.announcements.id
  position  = 3
}

resource "discord_text_channel" "announce_sponsor" {
  server_id = var.server.id
  name      = "🎁｜協賛企業からのお知らせ"
  category  = discord_category_channel.announcements.id
  position  = 4
}

################################
# 3. COMMUNITY & NETWORKING
################################
resource "discord_category_channel" "community" {
  server_id = var.server.id
  name      = "💬 COMMUNITY & NETWORKING"
  position  = 3
}

resource "discord_text_channel" "comm_intro" {
  server_id = var.server.id
  name      = "👋｜自己紹介"
  category  = discord_category_channel.community.id
  position  = 1
}

resource "discord_text_channel" "comm_lounge" {
  server_id = var.server.id
  name      = "☕｜雑談ラウンジ"
  category  = discord_category_channel.community.id
  position  = 2
}

resource "discord_text_channel" "comm_news" {
  server_id = var.server.id
  name      = "📰｜ai・テックニュース"
  category  = discord_category_channel.community.id
  position  = 3
}

resource "discord_text_channel" "comm_resource" {
  server_id = var.server.id
  name      = "📚｜役立ちリソース共有"
  category  = discord_category_channel.community.id
  position  = 4
}

resource "discord_text_channel" "comm_photo" {
  server_id = var.server.id
  name      = "📸｜写真・スクショ共有"
  category  = discord_category_channel.community.id
  position  = 5
}

################################
# 4. TEAM BUILDING
################################
resource "discord_category_channel" "team_building" {
  server_id = var.server.id
  name      = "🤝 TEAM BUILDING"
  position  = 4
}

resource "discord_text_channel" "tb_recruit" {
  server_id = var.server.id
  name      = "🤝｜メンバー募集"
  category  = discord_category_channel.team_building.id
  position  = 1
}

resource "discord_text_channel" "tb_join" {
  server_id = var.server.id
  name      = "🙋‍♀️｜チーム加入希望"
  category  = discord_category_channel.team_building.id
  position  = 2
}

resource "discord_text_channel" "tb_idea" {
  server_id = var.server.id
  name      = "💡｜アイデア共有・壁打ち"
  category  = discord_category_channel.team_building.id
  position  = 3
}

################################
# 5. SUPPORT & HELPDESK
################################
resource "discord_category_channel" "support" {
  server_id = var.server.id
  name      = "❓ SUPPORT & HELPDESK"
  position  = 5
}

resource "discord_text_channel" "supp_qa" {
  server_id = var.server.id
  name      = "❓｜運営への質問"
  category  = discord_category_channel.support.id
  position  = 1
}

resource "discord_text_channel" "supp_tech_ai" {
  server_id = var.server.id
  name      = "🛠️｜技術サポート_ai"
  category  = discord_category_channel.support.id
  position  = 2
}

resource "discord_text_channel" "supp_tech_nocode" {
  server_id = var.server.id
  name      = "🛠️｜技術サポート_ノーコード"
  category  = discord_category_channel.support.id
  position  = 3
}

resource "discord_text_channel" "supp_sos" {
  server_id = var.server.id
  name      = "🆘｜sos窓口"
  category  = discord_category_channel.support.id
  position  = 4
}

################################
# 6. SPONSORS & MENTORS
################################
resource "discord_category_channel" "sponsors" {
  server_id = var.server.id
  name      = "🏢 SPONSORS & MENTORS"
  position  = 6
}

resource "discord_text_channel" "sp_mentor" {
  server_id = var.server.id
  name      = "👨‍🏫｜メンター紹介"
  category  = discord_category_channel.sponsors.id
  position  = 1
}

resource "discord_text_channel" "sp_booking" {
  server_id = var.server.id
  name      = "🙋‍♂️｜メンタリング予約"
  category  = discord_category_channel.sponsors.id
  position  = 2
}

resource "discord_text_channel" "sp_booth" {
  server_id = var.server.id
  name      = "🏢｜スポンサーブース"
  category  = discord_category_channel.sponsors.id
  position  = 3
}

################################
# 7. ADMIN
################################
resource "discord_category_channel" "admin" {
  server_id = var.server.id
  name      = "🔒 ADMIN：運営専用"
  position  = 7
}

resource "discord_text_channel" "ad_pm" {
  server_id = var.server.id
  name      = "👑｜pm-全体指示"
  category  = discord_category_channel.admin.id
  position  = 1
}

resource "discord_text_channel" "ad_plan" {
  server_id = var.server.id
  name      = "📊｜企画班-進行"
  category  = discord_category_channel.admin.id
  position  = 2
}

resource "discord_text_channel" "ad_plan_doc" {
  server_id = var.server.id
  name      = "📊｜企画班-台本・資料"
  category  = discord_category_channel.admin.id
  position  = 3
}

resource "discord_text_channel" "ad_pr_sns" {
  server_id = var.server.id
  name      = "📢｜広報班-sns・lp"
  category  = discord_category_channel.admin.id
  position  = 4
}

resource "discord_text_channel" "ad_pr_analysis" {
  server_id = var.server.id
  name      = "📢｜広報班-集客分析"
  category  = discord_category_channel.admin.id
  position  = 5
}

resource "discord_text_channel" "ad_ext_sp" {
  server_id = var.server.id
  name      = "🤝｜外部連携-スポンサー"
  category  = discord_category_channel.admin.id
  position  = 6
}

resource "discord_text_channel" "ad_ext_mentor" {
  server_id = var.server.id
  name      = "🤝｜外部連携-メンター"
  category  = discord_category_channel.admin.id
  position  = 7
}

resource "discord_text_channel" "ad_budget" {
  server_id = var.server.id
  name      = "💸｜予算・経費"
  category  = discord_category_channel.admin.id
  position  = 8
}

resource "discord_text_channel" "ad_trouble" {
  server_id = var.server.id
  name      = "🚨｜トラブル・リスク管理"
  category  = discord_category_channel.admin.id
  position  = 9
}

resource "discord_text_channel" "ad_bot_notion" {
  server_id = var.server.id
  name      = "🤖｜bot-notion通知"
  category  = discord_category_channel.admin.id
  position  = 10
}

resource "discord_text_channel" "ad_bot_form" {
  server_id = var.server.id
  name      = "🤖｜bot-form-entry"
  category  = discord_category_channel.admin.id
  position  = 11
}

################################
# 8. TEAM WORKSPACES
################################
resource "discord_category_channel" "team_01" {
  server_id = var.server.id
  name      = "📂 TEAM-01"
  position  = 8
}

resource "discord_text_channel" "t1_text" {
  server_id = var.server.id
  name      = "💬｜テキスト相談"
  category  = discord_category_channel.team_01.id
  position  = 1
}
resource "discord_text_channel" "t1_memo" {
  server_id = var.server.id
  name      = "📝｜アイデアメモ"
  category  = discord_category_channel.team_01.id
  position  = 2
}
resource "discord_voice_channel" "t1_voice1" {
  server_id = var.server.id
  name      = "🔊｜ボイス会議"
  category  = discord_category_channel.team_01.id
  position  = 3
}
resource "discord_voice_channel" "t1_voice2" {
  server_id = var.server.id
  name      = "🔊｜サブ会議室"
  category  = discord_category_channel.team_01.id
  position  = 4
}

resource "discord_category_channel" "team_02" {
  server_id = var.server.id
  name      = "📂 TEAM-02"
  position  = 9
}

resource "discord_text_channel" "t2_text" {
  server_id = var.server.id
  name      = "💬｜テキスト相談"
  category  = discord_category_channel.team_02.id
  position  = 1
}
resource "discord_text_channel" "t2_memo" {
  server_id = var.server.id
  name      = "📝｜アイデアメモ"
  category  = discord_category_channel.team_02.id
  position  = 2
}
resource "discord_voice_channel" "t2_voice1" {
  server_id = var.server.id
  name      = "🔊｜ボイス会議"
  category  = discord_category_channel.team_02.id
  position  = 3
}
resource "discord_voice_channel" "t2_voice2" {
  server_id = var.server.id
  name      = "🔊｜サブ会議室"
  category  = discord_category_channel.team_02.id
  position  = 4
}

resource "discord_category_channel" "team_03" {
  server_id = var.server.id
  name      = "📂 TEAM-03"
  position  = 10
}

resource "discord_text_channel" "t3_text" {
  server_id = var.server.id
  name      = "💬｜テキスト相談"
  category  = discord_category_channel.team_03.id
  position  = 1
}
resource "discord_text_channel" "t3_memo" {
  server_id = var.server.id
  name      = "📝｜アイデアメモ"
  category  = discord_category_channel.team_03.id
  position  = 2
}
resource "discord_voice_channel" "t3_voice1" {
  server_id = var.server.id
  name      = "🔊｜ボイス会議"
  category  = discord_category_channel.team_03.id
  position  = 3
}
resource "discord_voice_channel" "t3_voice2" {
  server_id = var.server.id
  name      = "🔊｜サブ会議室"
  category  = discord_category_channel.team_03.id
  position  = 4
}
