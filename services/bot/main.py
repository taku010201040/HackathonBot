# -*- coding: utf-8 -*-
import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from deep_translator import GoogleTranslator

import sqlite3
import datetime
from discord.ext import tasks
import google.generativeai as genai
import asyncio

DB_PATH = "bot_data.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id INTEGER, send_at TEXT, message TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS event_reminders (event_id TEXT PRIMARY KEY, reminded_at TEXT)')
    conn.commit()
    conn.close()
init_db()

try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    generation_config = {"temperature": 0.2}
except:
    pass

def get_knowledge_context():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT content FROM knowledge')
    rows = c.fetchall()
    conn.close()
    return "\n---\n".join([r[0] for r in rows])

async def ask_gemini(prompt: str) -> str:
    if not os.getenv("GEMINI_API_KEY"):
        return "Gemini APIキーが設定されていません。"
    context = get_knowledge_context()
    system_instruction = f"あなたはハッカソンのサポートAIです。以下のナレッジを参考にして回答してください。\n【ナレッジ】\n{context}"
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction, generation_config=generation_config)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AIエラー: {e}"


load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_SERVER_ID')

class RoleDropdown(discord.ui.Select):
    def __init__(self, placeholder: str, options: list[discord.SelectOption], min_values=0, max_values=1, custom_id=None, row=None):
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, custom_id=custom_id, row=row)

    async def callback(self, interaction: discord.Interaction):
        # 即座に処理中状態にしてタイムアウト（3秒制限）を防止
        await interaction.response.defer(ephemeral=True)
        
        selected_role_names = self.values
        added = []
        removed = []
        for name in selected_role_names:
            role = discord.utils.get(interaction.guild.roles, name=name)
            if role:
                if role in interaction.user.roles:
                    removed.append(role)
                else:
                    added.append(role)
        if added:
            await interaction.user.add_roles(*added)
        if removed:
            await interaction.user.remove_roles(*removed)
        
        msg = f"{self.placeholder.replace('▼ ', '')} を更新しました！\n"
        if added:
            msg += f"✅ 追加: " + ", ".join([r.name for r in added]) + "\n"
        if removed:
            msg += f"❌ 解除: " + ", ".join([r.name for r in removed])
            
        # deferしているため、followup.send を使って完了を通知
        await interaction.followup.send(msg, ephemeral=True, silent=True)


class RuleVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="🟢 ルールに同意して参加する", style=discord.ButtonStyle.success, custom_id="rule_verify_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        participant_role = discord.utils.get(guild.roles, name="参加者")
        
        if not participant_role:
            try:
                participant_role = await guild.create_role(name="参加者")
            except Exception as e:
                await interaction.followup.send("エラー: 参加者ロールの取得/作成に失敗しました。管理者にお問い合わせください。", ephemeral=True, silent=True)
                return
                
        if participant_role in interaction.user.roles:
            await interaction.followup.send("既に登録が完了しています！すべてのチャンネルをご利用いただけます。", ephemeral=True, silent=True)
        else:
            try:
                await interaction.user.add_roles(participant_role)
                await interaction.followup.send("ルールへの同意を確認しました！「参加者」ロールが付与され、すべてのチャンネルが解放されました 🎉", ephemeral=True, silent=True)
            except Exception as e:
                await interaction.followup.send(f"ロールの付与に失敗しました: {e}", ephemeral=True, silent=True)

class MentorAcceptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="対応する", style=discord.ButtonStyle.success, custom_id="mentor_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention} メンターが対応を開始しました！", ephemeral=False)
        button.disabled = True
        button.label = f"{interaction.user.display_name}さんが対応中"
        await interaction.message.edit(view=self)

class MentorSummonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="🆘 メンターを呼ぶ", style=discord.ButtonStyle.danger, custom_id="mentor_summon")
    async def summon(self, interaction: discord.Interaction, button: discord.ui.Button):
        mentor_role = discord.utils.get(interaction.guild.roles, name="メンター")
        m = mentor_role.mention if mentor_role else "メンターの皆さん"
        await interaction.channel.send(f"{m} {interaction.user.mention} さんがヘルプを求めています！", view=MentorAcceptView())
        await interaction.response.send_message("メンターを呼び出しました。", ephemeral=True)

class BasicProfileView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.add_item(RoleDropdown(
            placeholder="▼ 役割（複数選択可）", custom_id="select_job", max_values=3, row=0,
            options=[
                discord.SelectOption(label="デザイン", value="🎨 デザイン", emoji="🎨", description="UI/UX, グラフィック等"),
                discord.SelectOption(label="エンジニア", value="💻 エンジニア", emoji="💻", description="Web, アプリ, インフラ等"),
                discord.SelectOption(label="ビジネス・企画", value="📊 ビジネス・企画", emoji="📊", description="PdM, マーケ, リサーチ等"),
            ]
        ))
        self.add_item(RoleDropdown(
            placeholder="▼ 性別を選択", custom_id="select_gender", row=1,
            options=[
                discord.SelectOption(label="男", value="🚹 男", emoji="🚹"),
                discord.SelectOption(label="女", value="🚺 女", emoji="🚺"),
            ]
        ))
        self.add_item(RoleDropdown(
            placeholder="▼ 卒業年度・属性を選択", custom_id="select_grad", row=2,
            options=[
                discord.SelectOption(label="27卒", value="🎓 27卒", emoji="🎓"),
                discord.SelectOption(label="28卒", value="🎓 28卒", emoji="🎓"),
                discord.SelectOption(label="29卒", value="🎓 29卒", emoji="🎓"),
                discord.SelectOption(label="30卒", value="🎓 30卒", emoji="🎓"),
                discord.SelectOption(label="31卒以降", value="🎓 31卒以降", emoji="🎓"),
                discord.SelectOption(label="社会人", value="💼 社会人", emoji="💼"),
            ]
        ))
        self.add_item(RoleDropdown(
            placeholder="▼ 興味ある分野・職種【IT・開発系】", custom_id="select_interest_it", max_values=15, row=3,
            options=[
                discord.SelectOption(label="フロントエンドエンジニア", value="💻 フロントエンド"),
                discord.SelectOption(label="バックエンドエンジニア", value="💻 バックエンド"),
                discord.SelectOption(label="インフラ・クラウド", value="💻 インフラ・クラウド"),
                discord.SelectOption(label="モバイルアプリエンジニア", value="💻 モバイルアプリ"),
                discord.SelectOption(label="AI・機械学習エンジニア", value="💻 AI・機械学習"),
                discord.SelectOption(label="データサイエンティスト", value="💻 データサイエンス"),
                discord.SelectOption(label="セキュリティエンジニア", value="💻 セキュリティ"),
                discord.SelectOption(label="ゲームエンジニア", value="💻 ゲームエンジニア"),
                discord.SelectOption(label="QA・テスター", value="💻 QA・テスター"),
                discord.SelectOption(label="UI/UXデザイナー", value="💻 UI/UXデザイナー"),
                discord.SelectOption(label="PdM (プロダクトマネージャー)", value="💻 PdM"),
                discord.SelectOption(label="PM (プロジェクトマネージャー)", value="💻 PM"),
                discord.SelectOption(label="SRE", value="💻 SRE"),
                discord.SelectOption(label="DevRel", value="💻 DevRel"),
                discord.SelectOption(label="社内SE・情シス", value="💻 社内SE・情シス"),
            ]
        ))
        self.add_item(RoleDropdown(
            placeholder="▼ 興味ある分野・職種【ビジネス・その他】", custom_id="select_interest_biz", max_values=22, row=4,
            options=[
                discord.SelectOption(label="営業", value="🏢 営業"),
                discord.SelectOption(label="企画・マーケティング", value="🏢 企画・マーケティング"),
                discord.SelectOption(label="人事・総務・法務", value="🏢 人事・総務・法務"),
                discord.SelectOption(label="経理・財務", value="🏢 経理・財務"),
                discord.SelectOption(label="事務・アシスタント", value="🏢 事務・アシスタント"),
                discord.SelectOption(label="コンサルティング", value="🏢 コンサルティング"),
                discord.SelectOption(label="クリエイター・デザイン", value="🏢 クリエイター・デザイン"),
                discord.SelectOption(label="メディア・マスコミ", value="🏢 メディア・マスコミ"),
                discord.SelectOption(label="研究・開発", value="🏢 研究・開発"),
                discord.SelectOption(label="製造・生産管理", value="🏢 製造・生産管理"),
                discord.SelectOption(label="建築・土木", value="🏢 建築・土木"),
                discord.SelectOption(label="医療・福祉・介護", value="🏢 医療・福祉・介護"),
                discord.SelectOption(label="教育・保育", value="🏢 教育・保育"),
                discord.SelectOption(label="金融・保険", value="🏢 金融・保険"),
                discord.SelectOption(label="不動産", value="🏢 不動産"),
                discord.SelectOption(label="販売・サービス", value="🏢 販売・サービス"),
                discord.SelectOption(label="飲食・フード", value="🏢 飲食・フード"),
                discord.SelectOption(label="運輸・物流", value="🏢 運輸・物流"),
                discord.SelectOption(label="農林水産", value="🏢 農林水産"),
                discord.SelectOption(label="公務員・団体職員", value="🏢 公務員・団体職員"),
                discord.SelectOption(label="専門職（士業等）", value="🏢 専門職（士業等）"),
                discord.SelectOption(label="その他", value="🏢 その他"),
            ]
        ))

class SkillsToolsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.add_item(RoleDropdown(
            placeholder="▼ 使用経験のある言語（複数選択可）", custom_id="select_lang", max_values=15, row=0,
            options=[
                discord.SelectOption(label="Python", value="💻 Python"),
                discord.SelectOption(label="JavaScript", value="💻 JavaScript"),
                discord.SelectOption(label="TypeScript", value="💻 TypeScript"),
                discord.SelectOption(label="Go", value="💻 Go"),
                discord.SelectOption(label="Rust", value="💻 Rust"),
                discord.SelectOption(label="C / C++", value="💻 C/C++"),
                discord.SelectOption(label="C#", value="💻 C#"),
                discord.SelectOption(label="Java", value="💻 Java"),
                discord.SelectOption(label="Ruby", value="💻 Ruby"),
                discord.SelectOption(label="PHP", value="💻 PHP"),
                discord.SelectOption(label="Swift", value="💻 Swift"),
                discord.SelectOption(label="Kotlin", value="💻 Kotlin"),
                discord.SelectOption(label="HTML/CSS", value="💻 HTML/CSS"),
                discord.SelectOption(label="SQL", value="💻 SQL"),
                discord.SelectOption(label="Dart", value="💻 Dart"),
            ]
        ))
        self.add_item(RoleDropdown(
            placeholder="▼ AI①：テキスト・開発・Google系（複数可）", custom_id="select_ai_dev", max_values=15, row=1,
            options=[
                discord.SelectOption(label="Antigravity", value="🤖 Antigravity"),
                discord.SelectOption(label="Gemini", value="🤖 Gemini"),
                discord.SelectOption(label="Google AI Studio", value="🤖 Google AI Studio"),
                discord.SelectOption(label="Vertex AI", value="🤖 Vertex AI"),
                discord.SelectOption(label="ChatGPT", value="🤖 ChatGPT"),
                discord.SelectOption(label="Claude", value="🤖 Claude"),
                discord.SelectOption(label="Perplexity", value="🤖 Perplexity"),
                discord.SelectOption(label="GitHub Copilot", value="🤖 GitHub Copilot"),
                discord.SelectOption(label="Cursor", value="🤖 Cursor"),
                discord.SelectOption(label="v0 (Vercel)", value="🤖 v0"),
                discord.SelectOption(label="Devin", value="🤖 Devin"),
                discord.SelectOption(label="Cline", value="🤖 Cline"),
                discord.SelectOption(label="Dify", value="🤖 Dify"),
                discord.SelectOption(label="Coze", value="🤖 Coze"),
                discord.SelectOption(label="Notion AI", value="🤖 Notion AI"),
            ]
        ))
        self.add_item(RoleDropdown(
            placeholder="▼ AI②：画像・動画・デザイン・自動化（複数可）", custom_id="select_ai_creative", max_values=15, row=2,
            options=[
                discord.SelectOption(label="Midjourney", value="🤖 Midjourney"),
                discord.SelectOption(label="Stable Diffusion", value="🤖 Stable Diffusion"),
                discord.SelectOption(label="DALL-E 3", value="🤖 DALL-E 3"),
                discord.SelectOption(label="Adobe Firefly", value="🤖 Adobe Firefly"),
                discord.SelectOption(label="Runway", value="🤖 Runway"),
                discord.SelectOption(label="Sora", value="🤖 Sora"),
                discord.SelectOption(label="Luma Dream Machine", value="🤖 Luma Dream Machine"),
                discord.SelectOption(label="Suno", value="🤖 Suno"),
                discord.SelectOption(label="Udio", value="🤖 Udio"),
                discord.SelectOption(label="Vrew", value="🤖 Vrew"),
                discord.SelectOption(label="HeyGen", value="🤖 HeyGen"),
                discord.SelectOption(label="Canva AI", value="🤖 Canva AI"),
                discord.SelectOption(label="Figma AI", value="🤖 Figma AI"),
                discord.SelectOption(label="Make", value="🤖 Make"),
                discord.SelectOption(label="Zapier", value="🤖 Zapier"),
            ]
        ))

class ScheduleEditModal(discord.ui.Modal, title="📅 予約メッセージの編集"):
    def __init__(self, schedule_id: int, current_send_at: str, current_message: str):
        super().__init__()
        self.schedule_id = schedule_id
        
        self.send_at_input = discord.ui.TextInput(
            label="送信日時 (YYYY-MM-DD HH:MM)",
            default=current_send_at,
            max_length=16,
            required=True
        )
        self.message_input = discord.ui.TextInput(
            label="送信メッセージ内容",
            style=discord.TextStyle.paragraph,
            default=current_message,
            required=True
        )
        self.add_item(self.send_at_input)
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        send_at_str = self.send_at_input.value.strip()
        new_msg = self.message_input.value.strip()
        
        try:
            datetime.datetime.strptime(send_at_str, "%Y-%m-%d %H:%M")
        except ValueError:
            await interaction.followup.send("エラー: 日時のフォーマットが正しくありません。例: 2026-07-30 18:00", ephemeral=True, silent=True)
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE schedules SET send_at = ?, message = ? WHERE id = ?", (send_at_str, new_msg, self.schedule_id))
        conn.commit()
        conn.close()
        
        await interaction.followup.send(f"✅ 予約メッセージ（ID: {self.schedule_id}）を更新しました！\n• 予約日時: `{send_at_str}`", ephemeral=True, silent=True)

class ScheduleActionView(discord.ui.View):
    def __init__(self, schedule_id: int, send_at: str, message: str):
        super().__init__(timeout=180)
        self.schedule_id = schedule_id
        self.send_at = send_at
        self.message = message

    @discord.ui.button(label="✏️ 予約を編集", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ScheduleEditModal(self.schedule_id, self.send_at, self.message)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🗑️ 予約を削除", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM schedules WHERE id = ?", (self.schedule_id,))
        conn.commit()
        conn.close()
        
        button.disabled = True
        button.label = "削除済み"
        await interaction.response.edit_message(content=f"🗑️ 予約メッセージ（ID: {self.schedule_id}）を取り消し・削除しました。", embed=None, view=None)

class ScheduleSelectDropdown(discord.ui.Select):
    def __init__(self, schedules_data):
        options = []
        for sid, ch_id, send_at, msg in schedules_data[:25]:
            label = f"ID:{sid} [{send_at}]"
            desc = msg[:45] + ("..." if len(msg) > 45 else "")
            options.append(discord.SelectOption(label=label, value=str(sid), description=desc))
            
        super().__init__(placeholder="▼ 編集・削除する予約を選択してください", options=options, custom_id="select_schedule")

    async def callback(self, interaction: discord.Interaction):
        sid = int(self.values[0])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, channel_id, send_at, message FROM schedules WHERE id = ?", (sid,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            await interaction.response.send_message("指定された予約メッセージは見つかりませんでした（既に送信された可能性があります）。", ephemeral=True, silent=True)
            return

        sid, ch_id, send_at, msg = row
        ch = interaction.guild.get_channel(ch_id)
        ch_name = ch.mention if ch else f"ID: {ch_id}"
        
        embed = discord.Embed(
            title=f"📅 予約メッセージ詳細 (ID: {sid})",
            color=0x5865F2
        )
        embed.add_field(name="📌 送信先チャンネル", value=ch_name, inline=True)
        embed.add_field(name="⏰ 送信予定日時", value=f"`{send_at}`", inline=True)
        embed.add_field(name="📝 メッセージ内容", value=f"```\n{msg}\n```", inline=False)
        
        view = ScheduleActionView(sid, send_at, msg)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True, silent=True)

class ScheduleManageView(discord.ui.View):
    def __init__(self, schedules_data):
        super().__init__(timeout=180)
        self.add_item(ScheduleSelectDropdown(schedules_data))

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    
    @tasks.loop(minutes=60)
    async def deadline_loop(self):
        if not GUILD_ID: return
        guild = self.get_guild(int(GUILD_ID))
        if not guild: return
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key='deadline'")
        row = c.fetchone()
        conn.close()
        
        if row:
            try:
                deadline = datetime.datetime.fromisoformat(row[0])
                now = datetime.datetime.now()
                diff = deadline - now
                hours = int(diff.total_seconds() // 3600)
                
                ch = discord.utils.find(lambda c: "⏳｜" in c.name, guild.voice_channels)
                if hours >= 0:
                    new_name = f"⏳｜残り {hours}時間"
                else:
                    new_name = "⏳｜ハッカソン終了！"
                    
                if ch and ch.name != new_name:
                    await ch.edit(name=new_name)
                elif not ch:
                    # Create one at the top
                    await guild.create_voice_channel(name=new_name, position=0)
            except Exception as e:
                print(f"Deadline loop error: {e}")
        else:
            try:
                # 提出期限が設定されていない場合は、残っているカウントダウン用VCを自動で削除
                for ch in guild.voice_channels:
                    if "⏳｜" in ch.name:
                        await ch.delete()
            except Exception as e:
                print(f"Deadline loop cleanup error: {e}")

    @tasks.loop(minutes=1)
    async def schedule_loop(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("SELECT id, channel_id, message FROM schedules WHERE send_at <= ?", (now_str,))
        rows = c.fetchall()
        for r in rows:
            sid, ch_id, msg = r
            ch = self.get_channel(ch_id)
            if ch:
                try:
                    await ch.send(msg, silent=True)
                except:
                    pass
            c.execute("DELETE FROM schedules WHERE id = ?", (sid,))
        conn.commit()
        conn.close()

    @tasks.loop(minutes=1)
    async def event_reminder_loop(self):
        if not GUILD_ID: return
        guild = self.get_guild(int(GUILD_ID))
        if not guild: return

        try:
            events = await guild.fetch_scheduled_events()
            now = datetime.datetime.now(datetime.timezone.utc)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("SELECT value FROM settings WHERE key='event_reminder_enabled'")
            enabled_row = c.fetchone()
            if enabled_row and enabled_row[0] == 'false':
                conn.close()
                return

            c.execute("SELECT value FROM settings WHERE key='event_reminder_channel_id'")
            ch_row = c.fetchone()
            c.execute("SELECT value FROM settings WHERE key='event_reminder_role_id'")
            role_row = c.fetchone()
            c.execute("SELECT value FROM settings WHERE key='event_reminder_template'")
            tpl_row = c.fetchone()
            c.execute("SELECT value FROM settings WHERE key='event_reminder_minutes_before'")
            minutes_row = c.fetchone()
            target_minutes = int(minutes_row[0]) if minutes_row else 60
            target_seconds = target_minutes * 60

            for event in events:
                if event.status != discord.EventStatus.scheduled:
                    continue

                diff = event.start_time - now
                diff_seconds = diff.total_seconds()

                if 0 <= diff_seconds <= target_seconds:
                    c.execute("SELECT 1 FROM event_reminders WHERE event_id = ?", (str(event.id),))
                    if c.fetchone() is None:
                        announce_ch = None
                        if ch_row:
                            try:
                                announce_ch = guild.get_channel(int(ch_row[0]))
                            except:
                                pass
                        if not announce_ch:
                            announce_ch = discord.utils.get(guild.text_channels, name="📢｜全体アナウンス")
                        if not announce_ch:
                            announce_ch = discord.utils.get(guild.text_channels, name="📅｜イベントカレンダー")
                        if not announce_ch:
                            announce_ch = discord.utils.find(lambda ch: "アナウンス" in ch.name, guild.text_channels)
                        if not announce_ch:
                            announce_ch = guild.system_channel

                        if announce_ch:
                            mention_str = ""
                            if role_row:
                                try:
                                    role = guild.get_role(int(role_row[0]))
                                    if role:
                                        mention_str = role.mention
                                except:
                                    pass
                            if not mention_str:
                                participant_role = discord.utils.get(guild.roles, name="参加者")
                                mention_str = participant_role.mention if participant_role else "@everyone"

                            timestamp = int(event.start_time.timestamp())
                            time_str = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"
                            location_str = event.location or "Discord内"

                            if tpl_row and tpl_row[0].strip():
                                template = tpl_row[0]
                                msg = template.replace("{name}", event.name)\
                                              .replace("{time}", time_str)\
                                              .replace("{location}", location_str)\
                                              .replace("{url}", event.url)
                                if "{role}" in msg:
                                    msg = msg.replace("{role}", mention_str)
                                else:
                                    msg = f"{mention_str}\n{msg}"
                            else:
                                msg = (
                                    f"{mention_str} 📢 **イベント開催{target_minutes}分前リマインド**\n\n"
                                    f"イベント「**{event.name}**」がまもなく開始されます！\n\n"
                                    f"📅 **開始時刻**: {time_str}\n"
                                    f"📍 **場所**: {location_str}\n"
                                    f"🔗 **詳細・参加表明はこちら**: {event.url}"
                                )

                            await announce_ch.send(msg)
                            c.execute("INSERT INTO event_reminders (event_id, reminded_at) VALUES (?, ?)", (str(event.id), now.isoformat()))
                            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Event reminder loop error: {e}")

    async def setup_hook(self):
        self.add_view(BasicProfileView())
        self.add_view(SkillsToolsView())
        self.add_view(MentorSummonView())
        self.add_view(MentorAcceptView())
        self.add_view(RuleVerifyView())
        self.deadline_loop.start()
        self.schedule_loop.start()
        self.event_reminder_loop.start()

        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

client = MyClient()

TEMPLATES = {
    "intro": """**【自己紹介テンプレート】**
```text
■ お名前（ニックネーム）：
■ 職種・得意なこと（例：デザイン、Python、企画）：
■ ハッカソンでの目標：
■ ひとこと：
```
※コピーして自己紹介チャンネルに貼り付けてください！""",
    "recruit": """**【メンバー募集テンプレート】**
```text
■ チーム名 / プロジェクト名：
■ どんなプロダクトを作りたいか：
■ 募集しているポジション（例：フロントエンジニア1名）：
■ 開発環境・ツール：
■ 連絡方法（メンションやDMなど）：
```
※コピーしてメンバー募集チャンネルに貼り付けてください！""",
    "idea": """**【アイデア共有・壁打ちテンプレート】**
```text
■ 解決したい課題：
■ ターゲット（誰に向けたものか）：
■ 解決のアイデア・機能：
■ 悩んでいること・欲しいアドバイス：
```
※コピーしてアイデア共有チャンネルに貼り付けてください！"""
}

async def ensure_channel(guild: discord.Guild, name: str, category_keyword: str, is_voice: bool = False):
    if is_voice:
        ch = discord.utils.get(guild.voice_channels, name=name)
    else:
        ch = discord.utils.get(guild.text_channels, name=name)
        
    if ch:
        return ch
        
    category = discord.utils.find(lambda c: category_keyword in c.name, guild.categories)
    
    if is_voice:
        if category:
            ch = await guild.create_voice_channel(name=name, category=category)
        else:
            ch = await guild.create_voice_channel(name=name)
    else:
        if category:
            ch = await guild.create_text_channel(name=name, category=category)
        else:
            ch = await guild.create_text_channel(name=name)
    return ch

@client.tree.command(name="setup_onboarding", description="【運営用】案内チャンネルのメッセージを自動セットアップします")
@app_commands.default_permissions(administrator=True)
async def setup_onboarding(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    results = []

    def m(ch, fallback: str) -> str:
        return ch.mention if ch else f"**{fallback}**"

    # --- チャンネルの取得・作成 ---
    lounge_ch = await ensure_channel(guild, "☕｜雑談ラウンジ", "COMMUNITY")
    sos_ch = await ensure_channel(guild, "🆘｜SOS窓口", "SUPPORT")
    rule_ch = await ensure_channel(guild, "📜｜ルール・ガイドライン", "WELCOME")
    role_ch = await ensure_channel(guild, "✅｜ロール付与", "WELCOME")
    intro_ch = await ensure_channel(guild, "👋｜自己紹介", "COMMUNITY")
    guide_ch = await ensure_channel(guild, "🗺️｜歩き方ガイド", "WELCOME")
    welcome_ch = await ensure_channel(guild, "🏁｜ようこそ", "WELCOME")
    question_ch = await ensure_channel(guild, "❓｜運営への質問", "SUPPORT")

    announce_ch = await ensure_channel(guild, "📢｜全体アナウンス", "ANNOUNCEMENTS")
    calendar_ch = await ensure_channel(guild, "📅｜イベントカレンダー", "ANNOUNCEMENTS")
    award_ch = await ensure_channel(guild, "🏆｜審査・アワード情報", "ANNOUNCEMENTS")
    sponsor_info_ch = await ensure_channel(guild, "🎁｜協賛企業からのお知らせ", "ANNOUNCEMENTS")
    
    news_ai_ch = await ensure_channel(guild, "📰｜aiテックニュース", "COMMUNITY")
    news_youth_ch = await ensure_channel(guild, "📰｜若手ニュース", "COMMUNITY")
    resource_ch = await ensure_channel(guild, "📚｜リソース共有", "COMMUNITY")
    photo_ch = await ensure_channel(guild, "📸｜写真・スクショ共有", "COMMUNITY")
    level_notify_ch = await ensure_channel(guild, "🏆｜レベル・通知", "COMMUNITY")

    recruit_ch = await ensure_channel(guild, "🤝｜メンバー募集", "TEAM BUILDING")
    join_ch = await ensure_channel(guild, "🙋‍♀️｜チーム加入希望", "TEAM BUILDING")
    idea_ch = await ensure_channel(guild, "💡｜アイデア共有・壁打ち", "TEAM BUILDING")
    
    mentor_intro_ch = await ensure_channel(guild, "👨‍🏫｜メンター紹介", "SPONSORS")
    mentor_reserve_ch = await ensure_channel(guild, "🙋‍♂️｜メンタリング予約", "SPONSORS")
    sponsor_booth_ch = await ensure_channel(guild, "🏢｜スポンサーブース", "SPONSORS")
    
    tech_ai_ch = await ensure_channel(guild, "🛠️｜技術サポート_ai", "SUPPORT")
    tech_nocode_ch = await ensure_channel(guild, "🛠️｜技術サポート_ノーコード", "SUPPORT")
    
    # コミュニティアップデートチャンネル
    community_updates_ch = await ensure_channel(guild, "📢｜コミュニティ・アップデート", "ANNOUNCEMENTS")

    # 運営班用のテキスト＆VCチャンネル
    planning_txt = await ensure_channel(guild, "📁｜企画進行", "運営")
    planning_vc = await ensure_channel(guild, "🔊｜企画進行VC", "運営", is_voice=True)
    pr_txt = await ensure_channel(guild, "📁｜広報", "運営")
    pr_vc = await ensure_channel(guild, "🔊｜広報VC", "運営", is_voice=True)
    ext_txt = await ensure_channel(guild, "📁｜外部連携", "運営")
    ext_vc = await ensure_channel(guild, "🔊｜外部連携VC", "運営", is_voice=True)

    results.append("✅ 必要な全チャンネルの存在確認・作成を完了しました")

    if welcome_ch:
        try:
            await welcome_ch.purge(limit=50)
            results.append("🧹 🏁｜ようこそ の過去メッセージを清掃しました")
        except Exception as e:
            results.append(f"⚠️ 🏁｜ようこそ の清掃に失敗しました: {e}")
        embed1 = discord.Embed(
            title="🎉 ABCABC コミュニティへようこそ！",
            description=(
                "このサーバーに参加してくれた皆さん、本当にありがとうございます！\n"
                "ここは、AIやテクノロジーを活用して新しいプロダクト作りに挑む仲間が集まるコミュニティです。\n\n"
                "直近では **ABCABC AI Hackathon 2026** のメイン会場として稼働しますが、"
                "その後も文系・理系、職種を問わず、本気でものづくりをする人たちが継続して交流できる場を目指しています。\n"
                "エンジニアだけの戦場ではありません。企画力、デザイン力、プレゼン力——すべてが武器になります。"
            ),
            color=0x00E676,
        )

        embed2 = discord.Embed(
            title="📝 まずやること（3ステップ）",
            description=(
                "サーバーに参加したら、以下の3つをお願いします！\n\n"
                f"**Step 1** 📜  **ルールを読む**\n"
                f"→ {m(rule_ch, '📜ルール・ガイドライン')} で行動規範を確認してください。\n"
                "　全員が安心して参加できる環境を一緒に作りましょう。\n\n"
                f"**Step 2** ✅  **ロールを取得する**\n"
                f"→ {m(role_ch, '✅ロール付与')} で、自分の基本情報や得意分野を選択！\n"
                "　スキルや使えるツールを登録しておくと、交流やチームビルディングで声をかけられやすくなります。\n\n"
                f"**Step 3** 👋  **自己紹介をする**\n"
                f"→ {m(intro_ch, '👋自己紹介')} で、あなたのことを教えてください。\n"
                "　*※チャンネルの下部に専用の自己紹介テンプレートが用意されていますので、コピーして簡単にご利用いただけます！✨*"
            ),
            color=0x00E676,
        )
        embed2.set_footer(text=f"困ったことがあれば {question_ch.name if question_ch else '運営への質問'} チャンネルでいつでも聞いてください 🙌")

        await welcome_ch.send(embeds=[embed1, embed2], silent=True)
    
    if rule_ch:
        try:
            await rule_ch.purge(limit=50)
        except Exception:
            pass
        rule_embed1 = discord.Embed(
            title="📜 サーバー利用ルール ＆ 行動規範（Code of Conduct）",
            description="本サーバーに参加された時点で、以下のルールに同意いただいたものとみなします。\n全員が安心して開発に集中できる環境を、一緒に守っていきましょう。",
            color=0xFF5252,
        )
        rule_embed1.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        rule_embed1.add_field(
            name="🤝 1. 敬意あるコミュニケーション",
            value="• すべての参加者・メンター・スポンサー・運営に対し、**敬意を持って**接してください。\n• 人種・性別・年齢・宗教・性的指向・障がい・国籍に基づく差別的な発言は一切禁止です。\n• 相手が不快に感じる行為は、たとえ「冗談」であっても**ハラスメント**に該当します。\n• 建設的な批判は歓迎しますが、人格否定や攻撃的な言葉遣いは控えてください。",
            inline=False,
        )
        rule_embed1.add_field(
            name="💬 2. チャンネルの適切な利用",
            value=f"• 各チャンネルは目的ごとに分かれています。**チャンネルの趣旨に沿った投稿**をお願いします。\n• 迷ったら {m(lounge_ch, '☕雑談ラウンジ')} へ！ハッカソンに関係ない話題もOKです。",
            inline=False,
        )
        rule_embed1.add_field(
            name="🚫 3. スパム・宣伝の禁止",
            value="• 無許可の宣伝・勧誘・営業活動は禁止です。\n• 同じ内容の連投、不必要な @everyone / @here の使用はおやめください。\n• 外部サーバーへの招待リンクの無断投稿も禁止です。",
            inline=False,
        )

        rule_embed2 = discord.Embed(color=0xFF5252)
        rule_embed2.add_field(
            name="🔒 4. プライバシーとセキュリティ",
            value="• 他の参加者の**個人情報**（本名・住所・電話番号・写真等）を本人の同意なく公開することは厳禁です。\n• スクリーンショットの無断転載、DM内容の外部公開もお控えください。\n• 不審なリンクやファイルの共有を発見した場合は、すぐに運営へ報告をお願いします。",
            inline=False,
        )
        rule_embed2.add_field(
            name="©️ 5. 著作権の尊重",
            value="• 第三者の著作物（コード・画像・音楽等）を使用する場合は、**ライセンスを必ず確認**してください。\n• 海賊版ソフトウェアや不正に入手したAPIキーの使用は厳禁です。\n• オープンソースライセンス（MIT, Apache等）の活用を推奨します。",
            inline=False,
        )
        rule_embed2.add_field(
            name="👨‍🏫 6. メンター・スタッフへの相談マナー",
            value="• メンターやスタッフへの質問は、原則として**公開チャンネル**をご利用ください。\n• DMでの直接連絡は、相手から許可がない限りお控えください。\n• 質問の際は「何を試したか」「どこで詰まっているか」を具体的に伝えると、スムーズです。",
            inline=False,
        )

        rule_embed3 = discord.Embed(color=0xFF5252)
        rule_embed3.add_field(
            name="⚠️ 7. 違反時の対応",
            value="ルール違反が確認された場合、運営チームは以下の措置を取る場合があります。\n\n`\n🟡 軽度 → 注意・警告（DM or チャンネル内）\n🟠 中度 → 一時的なミュート・チャンネルアクセス制限\n🔴 重度 → サーバーからのキック / 永久BAN\n`\n※悪質なハラスメントや脅迫行為は、**即座にBAN**とし、必要に応じて関係機関に通報します。",
            inline=False,
        )
        rule_embed3.add_field(
            name="📋 8. Discordの利用規約",
            value="• 本サーバーのすべてのユーザーは、[Discord利用規約](https://discord.com/terms) および [コミュニティガイドライン](https://discord.com/guidelines) を遵守する義務があります。\n• 13歳未満の方はDiscordの利用規約に基づきご利用いただけません。",
            inline=False,
        )
        rule_embed3.add_field(
            name="🆘 困ったとき・報告したいとき",
            value=f"• ルール違反を目撃した場合、または自身が被害を受けた場合は、\n　{m(sos_ch, '🆘SOS窓口')} チャンネルまたは運営メンバーへのDMでご連絡ください。\n• 報告者のプライバシーは厳守します。安心してご相談ください。\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n📌 *本ルールは運営の判断により予告なく更新される場合があります。*\n📌 *最終更新: 2026年5月30日*",
            inline=False,
        )

        await rule_ch.send(embeds=[rule_embed1, rule_embed2, rule_embed3], view=RuleVerifyView(), silent=True)

    if guide_ch:
        try:
            await guide_ch.purge(limit=50)
            results.append("🧹 🗺️｜歩き方ガイド の過去メッセージを清掃しました")
        except Exception as e:
            pass
        guide_embed1 = discord.Embed(
            title="🗺️ サーバーの歩き方ガイド",
            description="「チャンネルが多くてどこを見ればいいかわからない！」\nそんな方のために、このサーバーの全体マップをお届けします。\n目的に合ったチャンネルを活用して、コミュニティを最大限楽しみましょう！\n\n━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0x448AFF,
        )
        guide_embed1.add_field(
            name="🚀 WELCOME & ONBOARDING — まずはここから",
            value=f"🏁 {m(welcome_ch, 'ようこそ')} — 最初に読むサーバーの紹介\n📜 {m(rule_ch, 'ルール・ガイドライン')} — 必ず最初に目を通してください\n✅ {m(role_ch, 'ロール付与')} — 自分の基本情報とスキルを登録しよう\n🗺️ {m(guide_ch, '歩き方ガイド')} — このページです",
            inline=False,
        )
        guide_embed1.add_field(
            name="📢 ANNOUNCEMENTS — 見逃し厳禁！運営からのお知らせ",
            value=f"🔔 {m(announce_ch, '全体アナウンス')} — 最重要の連絡事項（※書き込み不可・閲覧専用）\n📅 {m(calendar_ch, 'イベントカレンダー')} — フェーズごとの日程、〆切リマインド\n🏆 {m(award_ch, '審査・アワード情報')} — 審査基準・賞金・賞品の詳細\n🎁 {m(sponsor_info_ch, '協賛企業からのお知らせ')} — API無料枠・企業賞などの情報",
            inline=False,
        )
        guide_embed1.add_field(
            name="💬 COMMUNITY & NETWORKING — 仲間をつくろう",
            value=f"👋 {m(intro_ch, '自己紹介')} — 挨拶をして他のメンバーに自分を知ってもらおう！\n☕ {m(lounge_ch, '雑談ラウンジ')} — テーマ自由のフリートーク（息抜きに最適）\n📰 {m(news_ai_ch, 'aiテックニュース')} — 最新のAI動向や使えそうなツールの共有\n📰 {m(news_youth_ch, '若手ニュース')} — 若手向けの有益な情報\n📚 {m(resource_ch, 'リソース共有')} — 便利な記事・テンプレートの共有\n📸 {m(photo_ch, '写真・スクショ共有')} — 開発中の画面やイベントの思い出",
            inline=False,
        )

        guide_embed2 = discord.Embed(color=0x448AFF)
        guide_embed2.add_field(
            name="🤝 TEAM BUILDING — チームを結成しよう",
            value=f"🤝 {m(recruit_ch, 'メンバー募集')} — 「エンジニア求む！」の募集投稿\n🙋‍♀️ {m(join_ch, 'チーム加入希望')} — 「こんなスキルあります！」のアピール投稿\n💡 {m(idea_ch, 'アイデア共有・壁打ち')} — アイデアを投げてフィードバックをもらう\n\n💡 **ヒント**: 募集チャンネル等で発言すると、Botがフォーマットを自動で案内してくれます！",
            inline=False,
        )
        guide_embed2.add_field(
            name="❓ SUPPORT & HELPDESK — 困ったらここ",
            value=f"❓ {m(question_ch, '運営への質問')} — 日程・ルールに関する一般的な質問\n🛠️ {m(tech_ai_ch, '技術サポート_ai')} — ChatGPT/Claude等のAPI連携やプロンプトの相談\n🛠️ {m(tech_nocode_ch, '技術サポート_ノーコード')} — Make, Bubble, Glide等の使い方の質問\n🆘 {m(sos_ch, 'SOS窓口')} — 緊急トラブル（チームとの連絡不通・機材故障等）",
            inline=False,
        )
        guide_embed2.add_field(
            name="🏢 SPONSORS & MENTORS — 心強い味方たち",
            value=f"👨‍🏫 {m(mentor_intro_ch, 'メンター紹介')} — 参加メンターの得意領域・プロフィール\n🙋‍♂️ {m(mentor_reserve_ch, 'メンタリング予約')} — メンターへの壁打ち・技術相談の予約\n🏢 {m(sponsor_booth_ch, 'スポンサーブース')} — 各協賛企業との交流・質問",
            inline=False,
        )

        guide_embed3 = discord.Embed(
            title="🎯 おすすめの行動フロー",
            description=(
                "`\n"
                "📜 ルール確認  →  ✅ ロール取得  →  👋 自己紹介\n"
                "      ↓\n"
                "💡 アイデア壁打ち  →  🤝 チーム結成  →  🛠️ 開発開始！\n"
                "      ↓\n"
                "👨‍🏫 メンタリング活用  →  🏆 成果発表  →  🎉 打ち上げ！\n"
                "`\n\n"
                f"分からないことがあれば、いつでも {m(question_ch, '❓運営への質問')} で聞いてください。\n"
                "「こんな初歩的なこと聞いていいのかな…」と思う必要はありません。\n"
                "**どんな質問も大歓迎です！** 🙌"
            ),
            color=0x448AFF,
        )
        guide_embed3.set_footer(text="ABCABC AI Hackathon 2026 運営チーム")

        await guide_ch.send(embeds=[guide_embed1, guide_embed2, guide_embed3], silent=True)

    if role_ch:
        try:
            await role_ch.purge(limit=50)
        except Exception:
            pass
        role_embed1 = discord.Embed(
            title="✅ STEP 1：基本プロフィールと興味ある職種を登録しよう",
            description="サーバー内での交流やチームビルディング（仲間探し）を円滑にするための大切な登録です！\n下のプルダウンメニューから、あなたに当てはまるものや興味のある分野を登録してください。\n\n📌 **【超重要】興味のある職種は『全部チェック』が断然おすすめ！**\nチームメンバーを募集したり探したりする際、ここで選んだ職種ロールが最大の目印になります。\n「本職はエンジニアだけど、ビジネスや企画にも関わってみたい」「デザインを勉強中・少し興味がある」といった場合も、**少しでも関心があれば【すべて】チェックを入れておくのがおすすめです！**\n\n💡 **どれを選べばいいか迷ったら？**\n「自分に何ができるか分からない…」「まだ未経験だし…」という場合でも、**少しでも面白そう、関係しそうだと思う職種には【全部チェック】を入れておくことを強くお勧めします！**\nチェックを多く入れておくことで、他のメンバーから声をかけてもらえるチャンスが格段に増え、新しい挑戦への第一歩になります！✨\n\n※プルダウンは複数選択が可能です（タップ/クリックするたびに追加・解除が切り替わります）。",
            color=0xFFAB00,
        )
        await role_ch.send(embed=role_embed1, view=BasicProfileView(), silent=True)

        role_embed2 = discord.Embed(
            title="🛠️ STEP 2：スキル・ツールを登録しよう",
            description="さらに、使用経験のあるプログラミング言語やAIツールを選択してアピールしましょう！\n\n💡 **Tip**: 「少しだけ触ったことがある」程度のツールでも、とりあえずチェックを入れておくのがオススメです！思わぬ共通点で会話が弾むかも？🙌",
            color=0xFFAB00,
        )
        await role_ch.send(embed=role_embed2, view=SkillsToolsView(), silent=True)

    summary = "\n".join(results)
    await interaction.followup.send(f"**オンボーディング セットアップ完了！**\n\n{summary}\n\n各チャンネルを確認してください。", silent=True)

@client.tree.command(name="setup_permissions", description="【運営用】ロールとチャンネルの権限を一括設定します")
@app_commands.default_permissions(administrator=True)
async def setup_permissions(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    # === ロールの取得・作成 ===
    def get_or_create_role(name):
        return discord.utils.get(guild.roles, name=name)
        
    ume_role = get_or_create_role("運営統括")
    mgmt_role = get_or_create_role("運営メンバー")
    kikaku_role = get_or_create_role("企画進行班")
    koho_role = get_or_create_role("広報班")
    renkei_role = get_or_create_role("外部連携班")
    staff_role = get_or_create_role("スタッフ")
    
    sponsor_role = get_or_create_role("スポンサー")
    kyosai_role = get_or_create_role("共催")
    judge_role = get_or_create_role("審査員")
    mentor_role = get_or_create_role("メンター")
    
    participant_role = get_or_create_role("参加者")
    
    # 万が一ロールが無ければ作成（今回は作成済み前提とするが最低限のフォロー）
    for r_name in ["運営統括", "運営メンバー", "企画進行班", "広報班", "外部連携班", "企画進行班リーダー", "広報班リーダー", "外部連携班リーダー", "企画進行班リーダー", "広報班リーダー", "外部連携班リーダー", "広報班", "外部連携班", "スタッフ", "スポンサー", "共催", "審査員", "メンター", "参加者"]:
        if not get_or_create_role(r_name):
            try:
                await guild.create_role(name=r_name)
            except Exception:
                pass

    ume_role = get_or_create_role("運営統括")
    mgmt_role = get_or_create_role("運営メンバー")
    kikaku_role = get_or_create_role("企画進行班")
    koho_role = get_or_create_role("広報班")
    renkei_role = get_or_create_role("外部連携班")
    staff_role = get_or_create_role("スタッフ")
    sponsor_role = get_or_create_role("スポンサー")
    kyosai_role = get_or_create_role("共催")
    judge_role = get_or_create_role("審査員")
    mentor_role = get_or_create_role("メンター")
    participant_role = get_or_create_role("参加者")

    # === ロール権限の基本設定 ===
    if ume_role:
        try:
            perms = discord.Permissions.all()
            await ume_role.edit(permissions=perms)
        except Exception:
            pass

    # 削除権限などを消すためのベース権限
    base_perms = discord.Permissions.general()
    base_perms.manage_channels = False
    base_perms.manage_roles = False
    base_perms.manage_webhooks = False
    base_perms.manage_messages = False
    base_perms.manage_guild = False
    base_perms.administrator = False

    for r in [mgmt_role, kikaku_role, koho_role, renkei_role, staff_role]:
        if r:
            try:
                await r.edit(permissions=base_perms)
            except Exception:
                pass
                
    # === チャンネルごとの権限設定 ===
    # 運営系チャンネル
    planning_txt = discord.utils.get(guild.text_channels, name="📁｜企画進行")
    planning_vc = discord.utils.get(guild.voice_channels, name="🔊｜企画進行vc")
    pr_txt = discord.utils.get(guild.text_channels, name="📁｜広報")
    pr_vc = discord.utils.get(guild.voice_channels, name="🔊｜広報vc")
    ext_txt = discord.utils.get(guild.text_channels, name="📁｜外部連携")
    ext_vc = discord.utils.get(guild.voice_channels, name="🔊｜外部連携vc")
    
    admin_channels = [planning_txt, planning_vc, pr_txt, pr_vc, ext_txt, ext_vc]
    
    # 運営系チャンネルへの共通設定（一般参加者、スポンサー等は完全不可視）
    for ch in admin_channels:
        if ch:
            try:
                await ch.set_permissions(guild.default_role, view_channel=False)
                for r in [sponsor_role, kyosai_role, judge_role, mentor_role, participant_role]:
                    if r:
                        await ch.set_permissions(r, view_channel=False)
                
                # 運営メンバー全体は見れる
                if mgmt_role:
                    await ch.set_permissions(mgmt_role, view_channel=True, send_messages=True)
                if ume_role:
                    await ch.set_permissions(ume_role, view_channel=True, send_messages=True, manage_messages=True)
            except Exception:
                pass
                
    # 各班専用の設定（他の班は見る専）
    # 企画進行班
    for ch in [planning_txt, planning_vc]:
        if ch:
            if kikaku_role:
                await ch.set_permissions(kikaku_role, send_messages=True, manage_messages=True)
            if koho_role:
                await ch.set_permissions(koho_role, send_messages=False)
            if renkei_role:
                await ch.set_permissions(renkei_role, send_messages=False)
                
    # 広報班
    for ch in [pr_txt, pr_vc]:
        if ch:
            if koho_role:
                await ch.set_permissions(koho_role, send_messages=True, manage_messages=True)
            if kikaku_role:
                await ch.set_permissions(kikaku_role, send_messages=False)
            if renkei_role:
                await ch.set_permissions(renkei_role, send_messages=False)
                
    # 外部連携班
    for ch in [ext_txt, ext_vc]:
        if ch:
            if renkei_role:
                await ch.set_permissions(renkei_role, send_messages=True, manage_messages=True)
            if kikaku_role:
                await ch.set_permissions(kikaku_role, send_messages=False)
            if koho_role:
                await ch.set_permissions(koho_role, send_messages=False)

    # === カテゴリーごとの認証・非表示設定 ===
    welcome_category = discord.utils.find(lambda c: "WELCOME" in c.name, guild.categories)
    if welcome_category:
        # @everyone は閲覧可能、書き込み不可
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=False)
        }
        if ume_role:
            overwrites[ume_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if mgmt_role:
            overwrites[mgmt_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            
        for ch in welcome_category.channels:
            try:
                await ch.edit(overwrites=overwrites)
            except Exception as e:
                print(f"Failed to set welcome channel permissions: {e}")

    # WELCOME 以外のカテゴリー（参加者・運営のみ閲覧・書き込み可能）
    for category in guild.categories:
        if "WELCOME" in category.name or "運営" in category.name:
            continue
            
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False)
        }
        
        if participant_role:
            overwrites[participant_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, read_message_history=True)
        if mentor_role:
            overwrites[mentor_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, read_message_history=True)
        if sponsor_role:
            overwrites[sponsor_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, read_message_history=True)
        if judge_role:
            overwrites[judge_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True, read_message_history=True)
        if mgmt_role:
            overwrites[mgmt_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if ume_role:
            overwrites[ume_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
            
        for ch in category.channels:
            try:
                await ch.edit(overwrites=overwrites)
            except Exception as e:
                print(f"Failed to set category channel permissions: {e}")

    await interaction.followup.send("✅ 権限のセットアップが完了しました！（未同意者向けの非表示設定も適用されました）", silent=True)

@client.tree.command(name="create_missing_roles", description="不足しているロールをすべて作成します")
@app_commands.default_permissions(administrator=True)
async def create_missing_roles(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    roles_to_create = [
        "🎨 デザイン", "💻 エンジニア", "📊 ビジネス・企画",
        "🚹 男", "🚺 女",
        "🎓 27卒", "🎓 28卒", "🎓 29卒", "🎓 30卒", "🎓 31卒以降", "💼 社会人",
        "💻 フロントエンド", "💻 バックエンド", "💻 インフラ・クラウド", "💻 モバイルアプリ", "💻 AI・機械学習", "💻 データサイエンス", "💻 セキュリティ", "💻 ゲームエンジニア", "💻 QA・テスター", "💻 UI/UXデザイナー", "💻 PdM", "💻 PM", "💻 SRE", "💻 DevRel", "💻 社内SE・情シス", "🏢 営業", "🏢 企画・マーケティング", "🏢 人事・総務・法務", "🏢 経理・財務", "🏢 事務・アシスタント", "🏢 コンサルティング", "🏢 クリエイター・デザイン", "🏢 メディア・マスコミ", "🏢 研究・開発", "🏢 製造・生産管理", "🏢 建築・土木", "🏢 医療・福祉・介護", "🏢 教育・保育", "🏢 金融・保険", "🏢 不動産", "🏢 販売・サービス", "🏢 飲食・フード", "🏢 運輸・物流", "🏢 農林水産", "🏢 公務員・団体職員", "🏢 専門職（士業等）", "🏢 その他",
        "💻 Python", "💻 JavaScript", "💻 TypeScript", "💻 Go", "💻 Rust", "💻 C/C++", "💻 C#", 
        "💻 Java", "💻 Ruby", "💻 PHP", "💻 Swift", "💻 Kotlin", "💻 HTML/CSS", "💻 SQL", "💻 Dart",
        "🤖 Antigravity", "🤖 Gemini", "🤖 Google AI Studio", "🤖 Vertex AI", "🤖 ChatGPT", "🤖 Claude", 
        "🤖 Perplexity", "🤖 GitHub Copilot", "🤖 Cursor", "🤖 v0", "🤖 Devin", "🤖 Cline", "🤖 Dify", 
        "🤖 Coze", "🤖 Notion AI",
        "🤖 Midjourney", "🤖 Stable Diffusion", "🤖 DALL-E 3", "🤖 Adobe Firefly", "🤖 Runway", "🤖 Sora", 
        "🤖 Luma Dream Machine", "🤖 Suno", "🤖 Udio", "🤖 Vrew", "🤖 HeyGen", "🤖 Canva AI", "🤖 Figma AI", 
        "🤖 Make", "🤖 Zapier"
    ]
    
    created = []
    for rname in roles_to_create:
        if not discord.utils.get(guild.roles, name=rname):
            try:
                await guild.create_role(name=rname)
                created.append(rname)
            except Exception as e:
                print(f"Failed to create role {rname}: {e}")
            
    if created:
        await interaction.followup.send(f"以下のロールを作成しました！\n{', '.join(created)}", silent=True)
    else:
        await interaction.followup.send("すべてのロールは既に存在しています。", silent=True)

@client.tree.command(name="template", description="各種テンプレートを呼び出します")
@app_commands.describe(type="呼び出したいテンプレートの種類を選択してください")
@app_commands.choices(type=[
    app_commands.Choice(name="👋 自己紹介", value="intro"),
    app_commands.Choice(name="🤝 メンバー募集", value="recruit"),
    app_commands.Choice(name="💡 アイデア共有", value="idea"),
])
async def template_command(interaction: discord.Interaction, type: app_commands.Choice[str]):
    template_text = TEMPLATES.get(type.value, "テンプレートが見つかりませんでした。")
    await interaction.response.send_message(template_text, ephemeral=True, silent=True)

sticky_messages = {}
STICKY_PREFIX = "📌 **【テンプレート】** このチャンネルでは以下をコピーしてご活用ください！"

def _match_template(channel_name: str):
    if "自己紹介" in channel_name:
        return TEMPLATES["intro"]
    if "メンバー募集" in channel_name:
        return TEMPLATES["recruit"]
    if "アイデア" in channel_name:
        return TEMPLATES["idea"]
    return None

async def _cleanup_old_sticky(channel: discord.TextChannel):
    try:
        async for msg in channel.history(limit=50):
            if msg.author == client.user and STICKY_PREFIX in msg.content:
                await msg.delete()
    except Exception:
        pass

async def initialize_sticky_messages():
    for guild in client.guilds:
        for channel in guild.text_channels:
            template_text = _match_template(channel.name)
            if template_text:
                try:
                    await _cleanup_old_sticky(channel)
                    new_msg = await channel.send(f"{STICKY_PREFIX}\n\n{template_text}", silent=True)
                    sticky_messages[channel.id] = new_msg.id
                except Exception as e:
                    print(f"Error initializing sticky for {channel.name}: {e}")


@client.event
async def on_voice_state_update(member, before, after):
    # Dynamic VC logic
    if after.channel:
        cat = after.channel.category
        if cat:
            empty_vcs = [vc for vc in cat.voice_channels if len(vc.members) == 0]
            if len(empty_vcs) == 0:
                base_name = after.channel.name
                import re
                base_name = re.sub(r' \d+$', '', base_name)
                new_name = f"{base_name} {len(cat.voice_channels) + 1}"
                try:
                    await cat.create_voice_channel(name=new_name)
                except:
                    pass
                
    if before.channel:
        cat = before.channel.category
        if cat and len(before.channel.members) == 0:
            empty_vcs = [vc for vc in cat.voice_channels if len(vc.members) == 0]
            if len(empty_vcs) > 1:
                import re
                if re.search(r' \d+$', before.channel.name):
                    try:
                        await before.channel.delete()
                    except:
                        pass

@client.event
async def on_reaction_add(reaction, user):
    if user.bot: return
    if reaction.message.author == user: return
    target_user = reaction.message.author
    if target_user.bot: return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT xp, level FROM users WHERE user_id = ?', (target_user.id,))
    row = c.fetchone()
    if row:
        xp = row[0] + 10
        level = row[1]
    else:
        xp = 10
        level = 1
        
    new_level = (xp // 50) + 1
    leveled_up = new_level > level
    
    c.execute('INSERT OR REPLACE INTO users (user_id, xp, level) VALUES (?, ?, ?)', (target_user.id, xp, new_level))
    conn.commit()
    conn.close()
    
    if leveled_up:
        try:
            guild = reaction.message.guild
            # 🏆｜レベル・通知 チャンネルを検索
            level_ch = discord.utils.get(guild.text_channels, name="🏆｜レベル・通知")
            if not level_ch:
                # 無ければ自動で作成 (COMMUNITYカテゴリーを探す)
                category = discord.utils.find(lambda c: "COMMUNITY" in c.name or "WELCOME" in c.name, guild.categories)
                if category:
                    level_ch = await guild.create_text_channel(name="🏆｜レベル・通知", category=category)
                else:
                    level_ch = await guild.create_text_channel(name="🏆｜レベル・通知")
            
            await level_ch.send(f"🎉 {target_user.mention} がレベルアップしました！ (Lv.{new_level}) 🚀", silent=True, allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            print(f"Level notification error: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    await initialize_sticky_messages()
    print('Bot is ready and slash commands are synced!')

@client.event
async def on_message(message: discord.Message):
    # コミュニティ・アップデートの翻訳
    ch_name = getattr(message.channel, 'name', '').lower()
    if "コミュニティ・アップデート" in ch_name or "community-updates" in ch_name or "コミュニティアップデート" in ch_name:
        # 英語のメッセージが来たら翻訳する (botでもwebhookでもユーザーでも翻訳)
        content_text = message.content or ""
        # Embedがある場合はEmbedの説明文も対象にする
        for emb in message.embeds:
            if emb.description:
                content_text += "\n" + emb.description
                
        if content_text.strip():
            try:
                translated = GoogleTranslator(source='auto', target='ja').translate(content_text)
                if translated:
                    await message.reply(f"🇯🇵 **自動翻訳:**\n{translated}", silent=True)
            except Exception as e:
                print(f"Translation failed: {e}")

    if message.author.bot:
        return
    # AI技術サポート/チャット (DMまたはメンションされた場合)
    is_dm = isinstance(message.channel, discord.DMChannel)
    if is_dm or client.user.mentioned_in(message):
        async with message.channel.typing():
            prompt = message.content.replace(f'<@{client.user.id}>', '').replace(f'<@!{client.user.id}>', '').strip()
            answer = await ask_gemini(prompt)
            await message.reply(answer, silent=True)

    # スレッドやダイレクトメッセージなど、通常のテキストチャンネル以外はスキップ
    if not isinstance(message.channel, discord.TextChannel):
        return

    template_text = _match_template(getattr(message.channel, 'name', ''))
    if not template_text:
        return
    old_id = sticky_messages.get(message.channel.id)
    if old_id:
        try:
            old_msg = await message.channel.fetch_message(old_id)
            await old_msg.delete()
        except Exception:
            pass
    else:
        await _cleanup_old_sticky(message.channel)
    try:
        new_msg = await message.channel.send(f"{STICKY_PREFIX}\n\n{template_text}", silent=True)
        sticky_messages[message.channel.id] = new_msg.id
    except Exception as e:
        print(f"Error sending sticky message: {e}")


@client.tree.command(name="task", description="【リーダー・運営専用】タスク用のチャンネルを生成します")
@app_commands.describe(assignees="アサインするメンバーを @メンション で指定（複数指定可）", title="タスク名")
async def create_task(interaction: discord.Interaction, assignees: str, title: str):
    allowed_roles = ["運営統括", "企画進行班リーダー", "広報班リーダー", "外部連携班リーダー"]
    has_role = any(r.name in allowed_roles for r in interaction.user.roles)
    if not has_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True, silent=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    import re
    # 文字列からユーザーIDをすべて抽出
    user_ids = [int(uid) for uid in re.findall(r'<@!?(\d+)>', assignees)]
    
    members = []
    for uid in set(user_ids):
        member = guild.get_member(uid)
        if not member:
            try:
                member = await guild.fetch_member(uid)
            except Exception:
                pass
        if member:
            members.append(member)
            
    if not members:
        await interaction.followup.send("エラー: アサインするメンバーを @メンション で1人以上指定してください。", ephemeral=True, silent=True)
        return
        
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    for member in members:
        overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
    cat = interaction.channel.category
    new_ch = await guild.create_text_channel(name=f"📝-{title}", category=cat, overwrites=overwrites)
    
    mentions_str = " ".join(m.mention for m in members)
    await new_ch.send(f"@silent {mentions_str} 新しいタスク「{title}」が割り当てられました！\n進捗が変わったら `/status` コマンドで状態を更新してください。", silent=True)
    await interaction.followup.send(f"タスクチャンネル {new_ch.mention} を作成しました。", silent=True)

@client.tree.command(name="status", description="タスクチャンネルの進捗ステータスを更新します")
@app_commands.choices(state=[
    app_commands.Choice(name="順調", value="🟢"),
    app_commands.Choice(name="やや遅れ", value="🟡"),
    app_commands.Choice(name="SOS", value="🔴"),
    app_commands.Choice(name="完了", value="✅")
])
async def update_status(interaction: discord.Interaction, state: app_commands.Choice[str]):
    ch = interaction.channel
    old_name = ch.name
    import re
    clean_name = re.sub(r'^[🟢🟡🔴✅📝]-', '', old_name)
    new_name = f"{state.value}-{clean_name}"
    await ch.edit(name=new_name)
    await interaction.response.send_message(f"ステータスを {state.name} に更新しました！", silent=True)

@client.tree.command(name="timer", description="指定分数後にメンションでお知らせします")
async def timer_cmd(interaction: discord.Interaction, minutes: int, message: str = "時間です！"):
    await interaction.response.send_message(f"{minutes}分後にアラームをセットしました。", silent=True)
    await asyncio.sleep(minutes * 60)
    await interaction.channel.send(f"{interaction.user.mention} ⏰ {message}", silent=True)

@client.tree.command(name="level", description="現在の自分のレベルと経験値（XP）を確認します")
async def check_level(interaction: discord.Interaction):
    user = interaction.user
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT xp, level FROM users WHERE user_id = ?', (user.id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        xp = row[0]
        level = row[1]
    else:
        xp = 0
        level = 1
        
    next_level = level + 1
    next_level_total_xp_required = level * 50
    xp_needed_for_next = next_level_total_xp_required - xp
    
    current_level_base = (level - 1) * 50
    current_level_progress = xp - current_level_base
    progress_percent = min(max(int((current_level_progress / 50) * 100), 0), 100)
    
    bar_length = 10
    filled_blocks = min(max(int(progress_percent / 10), 0), bar_length)
    empty_blocks = bar_length - filled_blocks
    progress_bar = "🟩" * filled_blocks + "⬜" * empty_blocks
    
    embed = discord.Embed(
        title=f"📊 {user.display_name} さんのレベルステータス",
        color=0xFFAB00
    )
    embed.set_thumbnail(url=user.display_avatar.url if user.display_avatar else None)
    embed.add_field(name="🏆 現在のレベル", value=f"**Lv. {level}**", inline=True)
    embed.add_field(name="✨ 累積経験値 (XP)", value=f"**{xp} XP**", inline=True)
    embed.add_field(name="📈 次のレベルまで", value=f"残り **{xp_needed_for_next} XP** (合計 {next_level_total_xp_required} XP で Lv.{next_level}へ)", inline=False)
    embed.add_field(name="🗺️ 進捗状況", value=f"{progress_bar} ({progress_percent}%)", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True, silent=True)

@client.tree.command(name="set_deadline", description="【運営用】提出期限（カウントダウン目標日時）を設定します")
@app_commands.default_permissions(administrator=True)
async def set_deadline(interaction: discord.Interaction, target_time: str):
    # format: YYYY-MM-DD HH:MM
    try:
        dt = datetime.datetime.strptime(target_time, "%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('deadline', ?)", (dt.isoformat(),))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"提出期限を {target_time} に設定しました。", silent=True)
    except Exception:
        await interaction.response.send_message("フォーマットが違います。例: 2026-06-30 18:00", ephemeral=True, silent=True)

@client.tree.command(name="cancel_deadline", description="【運営用】提出期限の設定をクリアし、カウントダウンチャンネルをすべて削除します")
@app_commands.default_permissions(administrator=True)
async def cancel_deadline(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM settings WHERE key='deadline'")
        conn.commit()
        conn.close()
        
        # 既存のカウントダウン用VCをすべて削除する
        guild = interaction.guild
        deleted_count = 0
        for ch in guild.voice_channels:
            if "⏳｜" in ch.name:
                try:
                    await ch.delete()
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete channel {ch.name}: {e}")
                    
        await interaction.followup.send(f"提出期限の設定を解除し、カウントダウンチャンネルを削除しました（削除件数: {deleted_count}件）。", silent=True)
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}", silent=True)

@client.tree.command(name="schedule_message", description="【運営用】指定日時にメッセージを予約送信します")
@app_commands.default_permissions(administrator=True)
async def schedule_message(interaction: discord.Interaction, target_time: str, channel: discord.TextChannel, message: str):
    # format: YYYY-MM-DD HH:MM
    try:
        dt = datetime.datetime.strptime(target_time, "%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO schedules (channel_id, send_at, message) VALUES (?, ?, ?)", (channel.id, dt.strftime("%Y-%m-%d %H:%M"), message))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"{channel.mention} 宛に {target_time} に送信予約しました。", silent=True)
    except Exception:
        await interaction.response.send_message("フォーマットが違います。例: 2026-06-30 18:00", ephemeral=True, silent=True)

@client.tree.command(name="add_knowledge", description="【運営用】AIのナレッジベース（RAG）に情報を追加します")
@app_commands.default_permissions(administrator=True)
async def add_knowledge(interaction: discord.Interaction, text: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO knowledge (content) VALUES (?)", (text,))
    conn.commit()
    conn.close()
    await interaction.response.send_message("ナレッジを追加しました！AIがこれを参考に回答するようになります。", silent=True)

@client.tree.command(name="spawn_sos_button", description="【運営用】SOS窓口にメンター呼び出しボタンを設置します")
@app_commands.default_permissions(administrator=True)
async def spawn_sos_button(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🆘 メンター呼び出し窓口", 
        description="技術的に詰まった、または運営に緊急で相談したい場合は、下のボタンを押してください。\n待機中のメンター・スタッフに通知が飛びます！", 
        color=0xFF5252
    )
    await interaction.channel.send(embed=embed, view=MentorSummonView())
    await interaction.response.send_message("ボタンを設置しました。", ephemeral=True)

@client.tree.command(name="events", description="【運営用】現在登録されているDiscordイベントの一覧を取得・表示します")
@app_commands.default_permissions(administrator=True)
async def list_events(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    try:
        events = await guild.fetch_scheduled_events()
        if not events:
            await interaction.followup.send("現在スケジュールされているイベントはありません。", ephemeral=True, silent=True)
            return
            
        embeds = []
        for event in events:
            embed = discord.Embed(
                title=event.name,
                description=event.description or "（説明なし）",
                color=0x5865F2,
                url=event.url
            )
            timestamp = int(event.start_time.timestamp())
            embed.add_field(name="📅 開始時刻", value=f"<t:{timestamp}:F> (<t:{timestamp}:R>)", inline=False)
            embed.add_field(name="📍 場所", value=event.location or "Discord内", inline=True)
            embed.add_field(name="👥 参加予定者数", value=f"{event.user_count or 0} 人", inline=True)
            embed.set_footer(text=f"ステータス: {event.status.name} | ID: {event.id}")
            embeds.append(embed)
            
        await interaction.followup.send(f"📅 **取得したイベント一覧 ({len(events)}件)**:", embeds=embeds[:10], ephemeral=True, silent=True)
    except Exception as e:
        await interaction.followup.send(f"イベントの取得中にエラーが発生しました: {e}", ephemeral=True, silent=True)

@client.tree.command(name="setup_event_reminder", description="【運営用】イベント自動リマインダーの通知先・ロール・文面を設定します")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    channel="リマインドを送信するテキストチャンネル",
    role="メンションするロール（指定しない場合は @everyone または 参加者）",
    template="文面。プレースホルダー: {name}, {time}, {location}, {url}, {role}",
    minutes_before="何分前に通知を送るか (例: 60 で1時間前、30 で30分前、120 で2時間前)"
)
async def setup_event_reminder(
    interaction: discord.Interaction, 
    channel: discord.TextChannel = None, 
    role: discord.Role = None, 
    template: str = None,
    minutes_before: int = None
):
    await interaction.response.defer(ephemeral=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    updated = []
    if channel:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_reminder_channel_id', ?)", (str(channel.id),))
        updated.append(f"• **通知チャンネル**: {channel.mention}")
    if role:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_reminder_role_id', ?)", (str(role.id),))
        updated.append(f"• **メンションロール**: {role.mention}")
    if template:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_reminder_template', ?)", (template,))
        updated.append(f"• **テンプレート文面**:\n```\n{template}\n```")
    if minutes_before is not None:
        if minutes_before <= 0:
            await interaction.followup.send("エラー: minutes_before は正の整数を指定してください。", ephemeral=True, silent=True)
            conn.close()
            return
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_reminder_minutes_before', ?)", (str(minutes_before),))
        updated.append(f"• **通知タイミング**: イベント開始の **{minutes_before} 分前**")
        
    conn.commit()
    conn.close()
    
    if not updated:
        await interaction.followup.send("パラメータが指定されていません。設定は変更されていません。", ephemeral=True, silent=True)
    else:
        await interaction.followup.send("✅ **イベントリマインダー設定を更新しました：**\n\n" + "\n".join(updated), ephemeral=True, silent=True)

@client.tree.command(name="cancel_event_reminder", description="【運営用】イベント自動リマインダーを一時停止・再開、または設定リセットします")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(action=[
    app_commands.Choice(name="⏸️ 自動リマインダーを一時停止・無効化", value="disable"),
    app_commands.Choice(name="▶️ 自動リマインダーを再開・有効化", value="enable"),
    app_commands.Choice(name="🔄 設定（チャンネル・ロール・文面）を初期リセット", value="reset"),
])
async def cancel_event_reminder(interaction: discord.Interaction, action: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if action.value == "disable":
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_reminder_enabled', 'false')")
        conn.commit()
        conn.close()
        await interaction.followup.send("⏸️ **イベント自動リマインダーを一時停止（無効化）しました。**\nイベントが開催されても自動リマインドは送信されません。", ephemeral=True, silent=True)
    elif action.value == "enable":
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_reminder_enabled', 'true')")
        conn.commit()
        conn.close()
        await interaction.followup.send("▶️ **イベント自動リマインダーを再開（有効化）しました。**", ephemeral=True, silent=True)
    elif action.value == "reset":
        c.execute("DELETE FROM settings WHERE key IN ('event_reminder_channel_id', 'event_reminder_role_id', 'event_reminder_template', 'event_reminder_enabled', 'event_reminder_minutes_before')")
        conn.commit()
        conn.close()
        await interaction.followup.send("🔄 **イベントリマインダーの設定（通知先・ロール・テンプレート・タイマー）を初期状態にリセットしました。**", ephemeral=True, silent=True)

@client.tree.command(name="schedules", description="【運営用】現在登録されている予約送信メッセージの一覧取得・編集・削除を行います")
@app_commands.default_permissions(administrator=True)
async def list_schedules(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_id, send_at, message FROM schedules ORDER BY send_at ASC")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        await interaction.followup.send("現在登録されている予約メッセージはありません。", ephemeral=True, silent=True)
        return
        
    view = ScheduleManageView(rows)
    await interaction.followup.send(f"📅 **現在登録されている予約メッセージ ({len(rows)}件):**\n下記ドロップダウンから選択して編集・削除が行えます。", view=view, ephemeral=True, silent=True)


def run_health_check_server():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Health check server running on port {port}...")
    server.serve_forever()

if __name__ == '__main__':
    if not TOKEN:
        print("エラー: .env に DISCORD_TOKEN が設定されていません。")
    else:
        # バックグラウンドスレッドで生存確認用サーバーを起動（Koyeb/Render等の無料サーバー用）
        threading.Thread(target=run_health_check_server, daemon=True).start()
        client.run(TOKEN)







