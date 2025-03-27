# TikTok Data Analytics Tool

個人利用のための TikTok 動画分析ツール。公開動画の統計データを取得し、ローカルでの分析と CSV エクスポートを提供します。

## 機能

- 公開動画の統計データ取得
- トレンド動画の分析
- ハッシュタグ検索
- データの暗号化保存
- CSV エクスポート

## 必要環境

- Python 3.8 以上
- MySQL 8.0 以上
- TikTok 開発者アカウント

## インストール手順

1. リポジトリのクローン

```bash
git clone https://github.com/kent0221/250320_DataAnalysis.git
```

2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

3. 環境変数の設定

- .env.example を.env にコピー
- 必要な認証情報を入力

## 使用方法

```bash
python -m app.main --interactive
```

## セキュリティ

- データは全てローカルに保存
- AES-256 による暗号化
- 30 日後の自動データ削除

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照

## プライバシーとセキュリティ

- [プライバシーポリシー](docs/PRIVACY.md)
- [利用規約](docs/TERMS.md)
- [セキュリティポリシー](docs/SECURITY.md)
