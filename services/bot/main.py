# -*- coding: utf-8 -*-
import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

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
        await interaction.followup.send(msg, ephemeral=True)

class BasicProfileView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.add_item(RoleDropdown(
            placeholder="▼ 大まかな役割（複数選択可）", custom_id="select_job", max_values=3, row=0,
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

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(BasicProfileView())
        self.add_view(SkillsToolsView())
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

async def ensure_channel(guild: discord.Guild, name: str, category_keyword: str):
    ch = discord.utils.get(guild.text_channels, name=name)
    if ch:
        return ch
    category = discord.utils.find(lambda c: category_keyword in c.name, guild.categories)
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

    lounge_ch = discord.utils.find(lambda c: "雑談" in c.name, guild.text_channels)
    if not lounge_ch:
        lounge_ch = await ensure_channel(guild, "☕｜雑談ラウンジ", "COMMUNITY")
        results.append("🆕 ☕｜雑談ラウンジ を作成しました")

    sos_ch = discord.utils.find(lambda c: "SOS" in c.name or "sos" in c.name, guild.text_channels)
    if not sos_ch:
        sos_ch = await ensure_channel(guild, "🆘｜SOS窓口", "SUPPORT")
        results.append("🆕 🆘｜SOS窓口 を作成しました")

    rule_ch = discord.utils.find(lambda c: "ルール" in c.name or "ガイドライン" in c.name, guild.text_channels)
    role_ch = discord.utils.find(lambda c: "ロール" in c.name or "付与" in c.name, guild.text_channels)
    intro_ch = discord.utils.find(lambda c: "自己紹介" in c.name, guild.text_channels)
    guide_ch = discord.utils.find(lambda c: "歩き方" in c.name or "ガイド" in c.name, guild.text_channels)
    welcome_ch = discord.utils.find(lambda c: "ようこそ" in c.name, guild.text_channels)
    question_ch = discord.utils.find(lambda c: "運営への質問" in c.name, guild.text_channels)

    def m(ch, fallback: str) -> str:
        return ch.mention if ch else fallback

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
        embed2.set_footer(text=f"困ったことがあれば ❓運営への質問 チャンネルでいつでも聞いてください 🙌")

        await welcome_ch.send(embeds=[embed1, embed2], silent=True)
        results.append("✅ 🏁｜ようこそ")
    else:
        results.append("⚠️ 🏁｜ようこそ — チャンネルが見つかりません")

    if rule_ch:
        try:
            await rule_ch.purge(limit=50)
            results.append(f"🧹 {rule_ch.name} の過去メッセージを清掃しました")
        except Exception as e:
            results.append(f"⚠️ {rule_ch.name} の清掃に失敗しました: {e}")
        rule_embed1 = discord.Embed(
            title="📜 サーバー利用ルール ＆ 行動規範（Code of Conduct）",
            description=(
                "本サーバーに参加された時点で、以下のルールに同意いただいたものとみなします。\n"
                "全員が安心して開発に集中できる環境を、一緒に守っていきましょう。"
            ),
            color=0xFF5252,
        )
        rule_embed1.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        rule_embed1.add_field(
            name="🤝 1. 敬意あるコミュニケーション",
            value=(
                "\n"
                "• すべての参加者・メンター・スポンサー・運営に対し、**敬意を持って**接してください。\n"
                "• 人種・性別・年齢・宗教・性的指向・障がい・国籍に基づく差別的な発言は一切禁止です。\n"
                "• 相手が不快に感じる行為は、たとえ「冗談」であっても**ハラスメント**に該当します。\n"
                "• 建設的な批判は歓迎しますが、人格否定や攻撃的な言葉遣いは控えてください。"
            ),
            inline=False,
        )
        rule_embed1.add_field(name="\u200b", value="\u200b", inline=False)
        rule_embed1.add_field(
            name="💬 2. チャンネルの適切な利用",
            value=(
                "\n"
                "• 各チャンネルは目的ごとに分かれています。**チャンネルの趣旨に沿った投稿**をお願いします。\n"
                f"• 迷ったら {m(lounge_ch, '☕雑談ラウンジ')} へ！ハッカソンに関係ない話題もOKです。"
            ),
            inline=False,
        )
        rule_embed1.add_field(name="\u200b", value="\u200b", inline=False)
        rule_embed1.add_field(
            name="🚫 3. スパム・宣伝の禁止",
            value=(
                "\n"
                "• 無許可の宣伝・勧誘・営業活動は禁止です。\n"
                "• 同じ内容の連投、不必要な @everyone / @here の使用はおやめください。\n"
                "• 外部サーバーへの招待リンクの無断投稿も禁止です。"
            ),
            inline=False,
        )

        rule_embed2 = discord.Embed(color=0xFF5252)
        rule_embed2.add_field(
            name="🔒 4. プライバシーとセキュリティ",
            value=(
                "\n"
                "• 他の参加者の**個人情報**（本名・住所・電話番号・写真等）を本人の同意なく公開することは厳禁です。\n"
                "• スクリーンショットの無断転載、DM内容の外部公開もお控えください。\n"
                "• 不審なリンクやファイルの共有を発見した場合は、すぐに運営へ報告をお願いします。"
            ),
            inline=False,
        )
        rule_embed2.add_field(name="\u200b", value="\u200b", inline=False)
        rule_embed2.add_field(
            name="©️ 5. 著作権の尊重",
            value=(
                "\n"
                "• 第三者の著作物（コード・画像・音楽等）を使用する場合は、**ライセンスを必ず確認**してください。\n"
                "• 海賊版ソフトウェアや不正に入手したAPIキーの使用は厳禁です。\n"
                "• オープンソースライセンス（MIT, Apache等）の活用を推奨します。"
            ),
            inline=False,
        )
        rule_embed2.add_field(name="\u200b", value="\u200b", inline=False)
        rule_embed2.add_field(
            name="👨‍🏫 6. メンター・スタッフへの相談マナー",
            value=(
                "\n"
                "• メンターやスタッフへの質問は、原則として**公開チャンネル**をご利用ください。\n"
                "• DMでの直接連絡は、相手から許可がない限りお控えください。\n"
                "• 質問の際は「何を試したか」「どこで詰まっているか」を具体的に伝えると、スムーズです。"
            ),
            inline=False,
        )

        rule_embed3 = discord.Embed(color=0xFF5252)
        rule_embed3.add_field(
            name="⚠️ 7. 違反時の対応",
            value=(
                "\n"
                "ルール違反が確認された場合、運営チームは以下の措置を取る場合があります。\n\n"
                "`\n"
                "🟡 軽度 → 注意・警告（DM or チャンネル内）\n"
                "🟠 中度 → 一時的なミュート・チャンネルアクセス制限\n"
                "🔴 重度 → サーバーからのキック / 永久BAN\n"
                "`\n"
                "※悪質なハラスメントや脅迫行為は、**即座にBAN**とし、必要に応じて関係機関に通報します。"
            ),
            inline=False,
        )
        rule_embed3.add_field(name="\u200b", value="\u200b", inline=False)
        rule_embed3.add_field(
            name="📋 8. Discordの利用規約",
            value=(
                "\n"
                "• 本サーバーのすべてのユーザーは、[Discord利用規約](https://discord.com/terms) および "
                "[コミュニティガイドライン](https://discord.com/guidelines) を遵守する義務があります。\n"
                "• 13歳未満の方はDiscordの利用規約に基づきご利用いただけません。"
            ),
            inline=False,
        )
        rule_embed3.add_field(name="\u200b", value="\u200b", inline=False)
        rule_embed3.add_field(
            name="🆘 困ったとき・報告したいとき",
            value=(
                "\n"
                "• ルール違反を目撃した場合、または自身が被害を受けた場合は、\n"
                f"　{m(sos_ch, '🆘SOS窓口')} チャンネルまたは運営メンバーへのDMでご連絡ください。\n"
                "• 報告者のプライバシーは厳守します。安心してご相談ください。\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 *本ルールは運営の判断により予告なく更新される場合があります。*\n"
                "📌 *最終更新: 2026年5月29日*"
            ),
            inline=False,
        )

        await rule_ch.send(embeds=[rule_embed1, rule_embed2, rule_embed3], silent=True)
        results.append(f"✅ {rule_ch.name}")
    else:
        results.append("⚠️ ルール・ガイドライン — チャンネルが見つかりません")

    if guide_ch:
        try:
            await guide_ch.purge(limit=50)
            results.append("🧹 🗺️｜歩き方ガイド の過去メッセージを清掃しました")
        except Exception as e:
            results.append(f"⚠️ 🗺️｜歩き方ガイド の清掃に失敗しました: {e}")
        guide_embed1 = discord.Embed(
            title="🗺️ サーバーの歩き方ガイド",
            description=(
                "「チャンネルが多くてどこを見ればいいかわからない！」\n"
                "そんな方のために、このサーバーの全体マップをお届けします。\n"
                "目的に合ったチャンネルを活用して、コミュニティを最大限楽しみましょう！\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x448AFF,
        )
        guide_embed1.add_field(
            name="🚀 WELCOME & ONBOARDING — まずはここから",
            value=(
                "\n"
                f"🏁 {m(welcome_ch, 'ようこそ')} — 最初に読むサーバーの紹介\n"
                f"📜 {m(rule_ch, 'ルール・ガイドライン')} — 必ず最初に目を通してください\n"
                f"✅ {m(role_ch, 'ロール付与')} — 自分の基本情報とスキルを登録しよう\n"
                f"🗺️ {m(guide_ch, '歩き方ガイド')} — このページです"
            ),
            inline=False,
        )
        guide_embed1.add_field(name="\u200b", value="\u200b", inline=False)
        guide_embed1.add_field(
            name="📢 ANNOUNCEMENTS — 見逃し厳禁！運営からのお知らせ",
            value=(
                "\n"
                "🔔 **全体アナウンス** — 最重要の連絡事項（※書き込み不可・閲覧専用）\n"
                "📅 **イベントカレンダー** — フェーズごとの日程、〆切リマインド\n"
                "🏆 **審査・アワード情報** — 審査基準・賞金・賞品の詳細\n"
                "🎁 **協賛企業からのお知らせ** — API無料枠・企業賞などの情報"
            ),
            inline=False,
        )
        guide_embed1.add_field(name="\u200b", value="\u200b", inline=False)
        guide_embed1.add_field(
            name="💬 COMMUNITY & NETWORKING — 仲間をつくろう",
            value=(
                "\n"
                f"👋 {m(intro_ch, '自己紹介')} — 挨拶をして他のメンバーに自分を知ってもらおう！\n"
                f"☕ {m(lounge_ch, '雑談ラウンジ')} — テーマ自由のフリートーク（息抜きに最適）\n"
                "📰 **AI・テックニュース** — 最新のAI動向や使えそうなツールの共有\n"
                "📚 **役立ちリソース共有** — 便利な記事・テンプレートの共有\n"
                "📸 **写真・スクショ共有** — 開発中の画面やイベントの思い出"
            ),
            inline=False,
        )

        guide_embed2 = discord.Embed(color=0x448AFF)
        guide_embed2.add_field(
            name="🤝 TEAM BUILDING — チームを結成しよう",
            value=(
                "\n"
                "🤝 **メンバー募集** — 「エンジニア求む！」の募集投稿\n"
                "🙋‍♀️ **チーム加入希望** — 「こんなスキルあります！」のアピール投稿\n"
                "💡 **アイデア共有・壁打ち** — アイデアを投げてフィードバックをもらう\n\n"
                "💡 **ヒント**: 募集チャンネル等で発言すると、Botがフォーマットを自動で案内してくれます！"
            ),
            inline=False,
        )
        guide_embed2.add_field(name="\u200b", value="\u200b", inline=False)
        guide_embed2.add_field(
            name="❓ SUPPORT & HELPDESK — 困ったらここ",
            value=(
                "\n"
                f"❓ {m(question_ch, '運営への質問')} — 日程・ルールに関する一般的な質問\n"
                "🛠️ **技術サポート_AI** — ChatGPT/Claude等のAPI連携やプロンプトの相談\n"
                "🛠️ **技術サポート_ノーコード** — Make, Bubble, Glide等の使い方の質問\n"
                f"🆘 {m(sos_ch, 'SOS窓口')} — 緊急トラブル（チームとの連絡不通・機材故障等）"
            ),
            inline=False,
        )
        guide_embed2.add_field(name="\u200b", value="\u200b", inline=False)
        guide_embed2.add_field(
            name="🏢 SPONSORS & MENTORS — 心強い味方たち",
            value=(
                "\n"
                "👨‍🏫 **メンター紹介** — 参加メンターの得意領域・プロフィール\n"
                "🙋‍♂️ **メンタリング予約** — メンターへの壁打ち・技術相談の予約\n"
                "🏢 **スポンサーブース** — 各協賛企業との交流・質問"
            ),
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
        results.append("✅ 🗺️｜歩き方ガイド")
    else:
        results.append("⚠️ 🗺️｜歩き方ガイド — チャンネルが見つかりません")

    if role_ch:
        try:
            await role_ch.purge(limit=50)
            results.append("🧹 ✅｜ロール付与 の過去メッセージを清掃しました")
        except Exception as e:
            results.append(f"⚠️ ✅｜ロール付与 の清掃に失敗しました: {e}")
        # Message 1
        role_embed1 = discord.Embed(
            title="✅ STEP 1：基本プロフィールと興味ある職種を登録しよう",
            description=(
                "サーバー内での交流やチームビルディング（仲間探し）を円滑にするための大切な登録です！\n"
                "下のプルダウンメニューから、あなたに当てはまるものや興味のある分野を登録してください。\n\n"
                "📌 **【超重要】興味のある職種は『全部チェック』が断然おすすめ！**\n"
                "チームメンバーを募集したり探したりする際、ここで選んだ職種ロールが最大の目印になります。\n"
                "「本職はエンジニアだけど、ビジネスや企画にも関わってみたい」「デザインを勉強中・少し興味がある」といった場合も、**少しでも関心があれば【すべて】チェックを入れておくのがおすすめです！**\n\n"
                "💡 **どれを選べばいいか迷ったら？**\n"
                "「自分に何ができるか分からない…」「まだ未経験だし…」という場合でも、**少しでも面白そう、関係しそうだと思う職種には【全部チェック】を入れておくことを強くお勧めします！**\n"
                "チェックを多く入れておくことで、他のメンバーから声をかけてもらえるチャンスが格段に増え、新しい挑戦への第一歩になります！✨\n\n"
                "※プルダウンは複数選択が可能です（タップ/クリックするたびに追加・解除が切り替わります）。"
            ),
            color=0xFFAB00,
        )
        await role_ch.send(embed=role_embed1, view=BasicProfileView(), silent=True)

        # Message 2
        role_embed2 = discord.Embed(
            title="🛠️ STEP 2：スキル・ツールを登録しよう",
            description="さらに、使用経験のあるプログラミング言語やAIツールを選択してアピールしましょう！\n\n                💡 **Tip**: 「少しだけ触ったことがある」程度のツールでも、とりあえずチェックを入れておくのがオススメです！思わぬ共通点で会話が弾むかも？🙌",
            color=0xFFAB00,
        )
        await role_ch.send(embed=role_embed2, view=SkillsToolsView(), silent=True)

        results.append("✅ ✅｜ロール付与 (分割メッセージ)")
    else:
        results.append("⚠️ ✅｜ロール付与 — チャンネルが見つかりません")

    summary = "\n".join(results)
    await interaction.followup.send(
        f"**オンボーディング セットアップ完了！**\n\n{summary}\n\n各チャンネルを確認してください。",
    )

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
        await interaction.followup.send(f"以下のロールを作成しました！\n{', '.join(created)}")
    else:
        await interaction.followup.send("すべてのロールは既に存在しています。")

@client.tree.command(name="template", description="各種テンプレートを呼び出します")
@app_commands.describe(type="呼び出したいテンプレートの種類を選択してください")
@app_commands.choices(type=[
    app_commands.Choice(name="👋 自己紹介", value="intro"),
    app_commands.Choice(name="🤝 メンバー募集", value="recruit"),
    app_commands.Choice(name="💡 アイデア共有", value="idea"),
])
async def template_command(interaction: discord.Interaction, type: app_commands.Choice[str]):
    template_text = TEMPLATES.get(type.value, "テンプレートが見つかりませんでした。")
    await interaction.response.send_message(template_text, ephemeral=True)

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
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    await initialize_sticky_messages()
    print('Bot is ready and slash commands are synced!')

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
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







