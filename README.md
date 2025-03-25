# TikTok 動画分析ツール

## 概要

個人利用のための TikTok 動画データ分析ツールです。
コマンドラインから操作でき、動画データの取得、保存、CSV 出力が可能です。

## 前提条件

- Python 3.11 以上
- MySQL 8.0 以上
- TikTok 開発者アカウント

## セットアップ

1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/DataAnalysis.git
cd DataAnalysis
```

2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な情報を入力
```

3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

4. データベースの準備

```bash
docker-compose up -d
mysql -u root -p < setup/init.sql
```

## 使用方法

```bash
python -m app.main --interactive
```

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)をご覧ください。

## 目的

- コンテンツクリエイターの動画分析支援
- トレンド動画の特徴分析
- ハッシュタグベースの動画分析

## プライバシーとデータ保護

- 取得したデータは個人の分析目的でのみ使用
- データは暗号化されたローカルデータベースに保存
- 個人情報は収集・保存しません
- 詳細は[プライバシーポリシー](https://github.com/kent0221/250320_DataAnalysis/PRIVACY)をご確認ください

## 利用規約

本ツールのご利用前に[利用規約](https://github.com/kent0221/250320_DataAnalysis/TERMS)をご確認ください。

## 機能

### 1. データ取得方法（3 パターン）

#### 1.1 トレンドデータ取得

- **取得データ**: クリエイター ID、動画 URL、再生回数、いいね数、コメント数、シェア数、投稿日時
- **取得条件**: 過去 1 週間で再生回数の伸びが大きいもの
- **取得データ数**: 10 件（ページネーション対応）
- **ソート機能**: 再生回数、いいね数、コメント数、投稿日時など

#### 1.2 特定クリエイター動画のデータ取得

- **取得データ**: クリエイター ID、動画 URL、再生回数、いいね数、コメント数、シェア数、投稿日時、取得日時
- **取得条件**: 動画 URL または動画 ID
- **取得数**: 指定された動画

#### 1.3 ハッシュタグ指定動画のデータ取得

- **取得データ**: クリエイター ID、動画 URL、再生回数、いいね数、コメント数、シェア数、投稿日時、取得日時
- **取得条件**: ハッシュタグ
- **取得数**: 10 件（ページネーション対応）

### 2. データベース

- MySQL を使用してデータを永続化

### 3. API

- 公式 TikTok API を使用予定
- 開発中はモックデータを使用して挙動確認

### 4. 環境変数

- データベース接続情報、API 認証情報などは`.env`ファイルで管理

### 5. コンテナ化

- Docker を使用して環境を構築

## プロジェクト構成

## API 制限

- TikTok API の制限：1 分あたり 1000 リクエスト
- Login Kit 必須
- 個人利用目的のみ

## 必要な環境変数

- TIKTOK_API_KEY: TikTok API キー
- TIKTOK_API_SECRET: TikTok API シークレット
- TIKTOK_ACCESS_TOKEN: アクセストークン
- REDIRECT_URI: 認証コールバック URI

## データベース設定

このプロジェクトは MySQL を使用しています。

### セットアップ手順

1. MySQL サーバーの起動:

```bash
docker-compose up -d
```

2. データベース初期化:

```bash
mysql -u root -p < setup/init.sql
```

## セキュリティ注意事項

- `.env`ファイルは決して GitHub にコミットしないでください
- API キーやデータベースパスワードは必ず安全に管理してください
- 本番環境では`USE_MOCK_API=false`に設定してください

## プライバシーとセキュリティ

- [プライバシーポリシー](https://github.com/kent0221/250320_DataAnalysis/PRIVACY)
- [利用規約](https://github.com/kent0221/250320_DataAnalysis/TERMS)
- [セキュリティポリシー](https://github.com/kent0221/250320_DataAnalysis/SECURITY)

## TikTok API 利用について

- 個人利用目的のみ
- API レート制限：600 リクエスト/分
- データの暗号化保存
