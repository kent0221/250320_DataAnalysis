# 公開前チェックリスト

## 1. Git 関連の確認

- [ ] `git clean -fdx`を実行し、未追跡ファイルを確認
  ```bash
  git clean -fdx --dry-run  # 削除されるファイルを確認
  git clean -fdx            # 実際に削除を実行
  ```
- [ ] `git diff`で変更内容を確認
  ```bash
  git diff main            # mainブランチとの差分を確認
  git diff --cached       # ステージングされた変更を確認
  ```

## 2. セキュリティチェック

- [ ] `.env`ファイルが`.gitignore`に含まれている
- [ ] 機密情報（API キー、トークン）が含まれていない
- [ ] `.env.example`が適切に設定されている
- [ ] データベースの認証情報が安全に管理されている

## 3. テスト実行

- [ ] 単体テストの実行
  ```bash
  python -m pytest tests/
  ```
- [ ] カバレッジレポートの確認
  ```bash
  python -m pytest --cov=app tests/
  ```
- [ ] モック API テストの確認
  ```bash
  python -m pytest tests/test_mock_api.py
  ```

## 4. ドキュメント確認

- [ ] README.md の内容が最新
- [ ] プライバシーポリシーが存在する
- [ ] 利用規約が存在する
- [ ] アプリケーションの目的が明確に記述されている

## 5. 依存関係の確認

- [ ] requirements.txt が最新
- [ ] 不要なパッケージが含まれていない
- [ ] セキュリティ脆弱性のあるバージョンを使用していない

## 6. API スコープの確認

- [ ] 必要最小限のスコープのみ使用
  - user.info.basic
  - video.list
  - video.list.basic
- [ ] レート制限が 600req/min に設定されている

## 7. テスト確認

- [ ] 全テストが通過
- [ ] レート制限のテストが正しい
- [ ] モックテストが機能している
