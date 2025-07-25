# Discord Hackathon Infrastructure

Terraform を使用して Discord サーバーとチャンネルをコードで管理する Infrastructure as Code (IaC) プロジェクトです。

## 概要

このプロジェクトは、ハッカソンやイベント用の Discord サーバーの構成を Terraform で自動化・管理することを目的としています。サーバー設定、チャンネル構成、カテゴリー設定などを宣言的に管理できます。

## 主な機能

- **Discord サーバー管理**: サーバーの基本設定を Terraform で管理
- **チャンネル自動構築**: デフォルトチャンネルとイベント専用チャンネルの自動作成
- **モジュール化**: 再利用可能なモジュール構造で効率的な管理を実現
- **環境分離**: production 環境の設定を分離管理

## プロジェクト構造

```plaintext
.
├── docker-compose.yml         # Terraform 実行環境の Docker 構成
└── services/
    └── discord/
        ├── environments/      # 環境別設定
        │   └── pro/          # Production 環境
        │       ├── channels/ # チャンネル管理設定
        │       └── server/   # サーバー管理設定
        └── modules/          # 再利用可能なモジュール
            ├── default_channels/  # デフォルトチャンネルセット
            ├── event_channels/    # イベント用チャンネルセット
            └── server/           # サーバー基本設定
```

## モジュール詳細

### default_channels
基本的なチャンネル構成を提供します：

- **テキストチャンネル**
  - 💬｜一般
  - ☁｜アイデアクラウド
  - 🗣｜雑談
- **ボイスチャンネル**
  - 💬｜一般
  - 💻｜作業
  - 🗣｜雑談
  - 🔕｜通知なし

- **特殊チャンネル**
  - 👂｜聴き専
  - ☎｜通話通知

### event_channels
イベント（ハッカソン等）専用のチャンネル構成：

- 🔧｜技術選定
- 💻｜開発
- 📊｜発表
- 📃｜資料
- 🔔｜webhook（GitLab 連携用）

### server
Discord サーバーの基本設定を管理：

- サーバー名
- デフォルト通知設定
- その他のサーバー設定

## 技術スタック

- **Terraform**: v1.0+
- **Provider**: [Lucky3028/discord](https://registry.terraform.io/providers/Lucky3028/discord/latest) v2.1.0
- **Backend**: HTTP backend (GitLab)
- **Docker**: Terraform 実行環境

## セットアップ

### 必要な環境変数

`.env` ファイルに以下の環境変数を設定してください：

```bash
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token

# Discord Server ID
DISCORD_SERVER_ID=your_discord_server_id

# GitLab Settings (for remote state)
GITLAB_USERNAME=your_gitlab_username
GITLAB_ACCESS_TOKEN=your_gitlab_access_token
GITLAB_REMOTE_STATE_ADDRESS=your_gitlab_remote_state_url
```

### 実行方法

1. Discord
   1. サーバーを新規作成します。
   2. 作成したサーバーのIDを取得してください。
       - [ユーザー/サーバー/メッセージIDはどこで見つけられる？｜Discord Support](https://support.discord.com/hc/ja/articles/206346498-%E3%83%A6%E3%83%BC%E3%82%B6%E3%83%BC-%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC-%E3%83%A1%E3%83%83%E3%82%BB%E3%83%BC%E3%82%B8ID%E3%81%AF%E3%81%A9%E3%81%93%E3%81%A7%E8%A6%8B%E3%81%A4%E3%81%91%E3%82%89%E3%82%8C%E3%82%8B)を参考にサーバーIDを取得して下さい。
       - 取得したサーバーのIDは、`.env`ファイルに設定してください。

2. Discord Developer Portal
   1. アプリケーションを作成します。アプリケーション名はサーバー内のユーザーに表示されます。
   2. アプリケーションの設定を開き、Bot設定からBot Tokenを取得して下さい。
       - 取得したBot Tokenは、`.env`ファイルに設定してください。
   3. Privileged Gateway Intentsを有効化してください。
   4. OAuth2 URL Generatorより、サーバーに追加するためのURLを取得してください。
       - SCOPES: bot
       - BOT PERMISSIONS: Administrator
   5. 取得したURLへアクセスして、アプリケーションをサーバーに追加して下さい。

3. (BackendをGitLab Terraform Stateにする場合) GitLab
   1. GitLab Personal Access Tokenを取得してください。
       - 取得したPersonal Access Tokenは、`.env`ファイルに設定してください。
   2. GitLab Terraform StateのURLを取得してください。
       - 取得したURLは、`.env`ファイルに設定してください。
       - URLは、`https://[gitlab_domain]/api/v4/projects/[project_id]/terraform/state`の形式です。

4. Terraform

   1. Docker上でTerraformコンテナを起動し、Terraformを実行します。

       （使用しているTerraform Providerがx86_64のみ対応しているため、Apple SiliconではDockerを使用して実行する必要があります。）

        ```bash
        docker compose run --rm terraform
        ```

   2. Terraform Initを行います。

        GitLab Terraform Stateを使用している場合は、GitLabの画面表示に従って下さい。

   3. 設定を適用：

        ```bash
        # サーバー設定を先に適用
        cd services/discord/environments/pro/server
        terraform plan
        terraform apply

        # 既に存在するチャンネルを使用する場合には`terraform import`を使用して下さい。

        # その後チャンネル設定を適用
        cd ../channels
        terraform plan
        terraform apply
        ```

## 使用上の注意

- Discord Bot には適切な権限（サーバー管理、チャンネル管理等）が必要です
- サーバー設定を先に適用してから、チャンネル設定を適用してください
- remote state を使用しているため、チーム開発時は state の競合に注意してください

## カスタマイズ

### 新しいイベントチャンネルの追加

`channels/variables.tf` でイベント変数を定義し、`channels/main.tf` で新しいモジュールインスタンスを作成：

```hcl
module "your_event_channels" {
  source = "../../../modules/event_channels/channels"
  
  common = var.common
  server = data.terraform_remote_state.server.outputs.server
  event = {
    name = "Your Event Name"
  }
}
```

### チャンネル構成の変更

各モジュールの `main.tf` を編集してチャンネル名、位置、カテゴリーなどをカスタマイズできます。

## ライセンス

プロジェクトのライセンスについては、リポジトリのライセンスファイルを参照してください。
