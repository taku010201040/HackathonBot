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

1. Docker Compose で Terraform コンテナを起動：

```bash
docker-compose up -d
```

2. コンテナに入る：

```bash
docker-compose exec terraform sh
```

3. Terraform を初期化：

```bash
# サーバー設定
cd services/discord/environments/pro/server
terraform init

# チャンネル設定
cd ../channels
terraform init
```

4. 設定を適用：

```bash
# サーバー設定を先に適用
cd services/discord/environments/pro/server
terraform plan
terraform apply

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
