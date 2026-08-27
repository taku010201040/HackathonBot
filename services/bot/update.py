import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Welcome text
content = re.sub(
    r'title="🎉 DISRUPT AI Hackathon 2026 へようこそ！",\s*description=\([\s\S]*?\),\s*color=0x00E676,',
    '''title="🎉 DISRUPT AI Hackathon コミュニティへようこそ！",
            description=(
                "このサーバーに参加してくれた皆さん、本当にありがとうございます！\\n"
                "ここは、AIやテクノロジーを活用して新しいプロダクト作りに挑む仲間が集まるコミュニティです。\\n\\n"
                "直近では **DISRUPT AI Hackathon 2026** のメイン会場として稼働しますが、"
                "その後も文系・理系、職種を問わず、本気でものづくりをする人たちが継続して交流できる場を目指しています。\\n"
                "エンジニアだけの戦場ではありません。企画力、デザイン力、プレゼン力——すべてが武器になります。"
            ),
            color=0x00E676,''',
    content
)

# Remove the 5 features from welcome text
content = re.sub(
    r'embed1\.add_field\(\s*name="💡 このハッカソンの5つの特徴",\s*value=\([\s\S]*?\),\s*inline=False,\s*\)',
    '',
    content
)

# Update Step 3 in welcome text
content = re.sub(
    r'/template コマンドでテンプレートを呼び出せます！',
    '*※チャンネル内で「あ」などと送信すると、Botが自動で自己紹介用フォーマットを出してくれます！*',
    content
)

# Update Guide / Team building hint
content = re.sub(
    r'/template コマンドで募集テンプレートを呼び出せます！',
    '募集チャンネル等で発言すると、Botがフォーマットを自動で案内してくれます！',
    content
)

# Update Roles embed
content = re.sub(
    r'role_embed1 = discord\.Embed\(\s*title="✅ スキルロールを選択しよう！",\s*description=\([\s\S]*?color=0xFFAB00,\s*\)\s*role_embed1\.add_field\(\s*name="🎨 デザイン"[\s\S]*?text="💡 複数選択OK！ボタンをもう一度押すとロールを外せます。"\s*\)',
    '''role_embed1 = discord.Embed(
            title="✅ プロフィールを登録しよう！",
            description=(
                "サーバー内での交流やチームビルディングをスムーズにするため、あなたの属性やスキルを登録してください。\\n\\n"
                "下のボタンやプルダウンメニューから、該当するものを選択してください！（複数選択OKです）\\n\\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFFAB00,
        )
        role_embed1.add_field(
            name="🔘 職種・希望ポジション（ボタン）",
            value=(
                "**🎨 デザイン**：UI/UX、グラフィック、プレゼン資料作成など\\n"
                "**💻 エンジニア**：プログラミング、API連携、アプリ開発など\\n"
                "**📊 ビジネス・企画**：アイデア立案、市場調査、マーケティングなど"
            ),
            inline=False,
        )
        role_embed1.set_footer(
            text="💡 各プルダウンから複数選択できます。"
        )''',
    content
)

# Add /create_missing_roles command
cmd_text = '''# ---------------------------------------------------------------------------
# Temp: Create Missing Roles
# ---------------------------------------------------------------------------
@client.tree.command(name="create_missing_roles", description="不足しているロールをすべて作成します")
@app_commands.default_permissions(administrator=True)
async def create_missing_roles(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    roles_to_create = [
        "🚹 男", "🚺 女",
        "🎓 27卒", "🎓 28卒", "🎓 29卒", "🎓 30卒",
        "🤖 ChatGPT", "🤖 Claude", "🤖 Gemini", "🤖 Notion AI", "🤖 GitHub Copilot", "🤖 Cursor", "🤖 Midjourney", "🤖 Stable Diffusion",
        "💻 Python", "💻 JavaScript", "💻 TypeScript", "💻 Go", "💻 Rust", "💻 C++", "💻 Java", "💻 Ruby", "💻 PHP", "💻 HTML/CSS"
    ]
    
    created = []
    for rname in roles_to_create:
        if not discord.utils.get(guild.roles, name=rname):
            try:
                await guild.create_role(name=rname)
                created.append(rname)
            except Exception as e:
                pass
            
    if created:
        await interaction.followup.send(f"以下のロールを作成しました！\\n{', '.join(created)}")
    else:
        await interaction.followup.send("すべてのロールは既に存在しています。")

'''
content = content.replace(
    '# ---------------------------------------------------------------------------\\n# /template',
    cmd_text + '# ---------------------------------------------------------------------------\\n# /template'
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
