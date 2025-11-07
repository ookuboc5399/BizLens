# デプロイ環境設定ガイド

## バックエンド（Render）

### ビルドコマンド
```
poetry install --no-root && poetry run playwright install chromium
```

### 環境変数
Renderダッシュボードで以下の環境変数を設定：
- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_SCHEMA`
- `SNOWFLAKE_WAREHOUSE`
- `OPENAI_API_KEY`
- その他必要な環境変数

### バックエンドURL
```
https://bizlens-r85b.onrender.com
```

## フロントエンド（Vercel）

### 環境変数の設定

Vercelダッシュボードで以下の環境変数を設定：

1. **Vercelダッシュボードにアクセス**
   - https://vercel.com/dashboard
   - プロジェクト「BizLens」を選択

2. **Settings → Environment Variables** に移動

3. **以下の環境変数を追加**：

   ```
   VITE_API_URL=https://bizlens-r85b.onrender.com/api
   ```

4. **環境を選択**：
   - Production
   - Preview
   - Development（オプション）

5. **保存後、再デプロイ**：
   - 自動デプロイが有効な場合は、次回のコミットで自動的に再デプロイされます
   - 手動で再デプロイする場合は、Deploymentsタブから「Redeploy」をクリック

### 確認方法

デプロイ後、以下を確認：

1. **ブラウザの開発者ツール（F12）**
   - Consoleタブでエラーを確認
   - NetworkタブでAPIリクエストのURLを確認
   - `/api/health` へのリクエストが `https://bizlens-r85b.onrender.com/api/health` に送信されているか確認

2. **ナビゲーションバーの接続状態インジケーター**
   - 緑色（接続中）: 正常
   - 赤色（切断）: 環境変数が設定されていない、またはバックエンドが起動していない

3. **API URLの表示**
   - ナビゲーションバーに表示されるAPI URLを確認
   - `(相対パス)` と表示される場合: 環境変数が設定されていない
   - `(https://bizlens-r85b.onrender.com/api)` と表示される場合: 環境変数が正しく設定されている

## トラブルシューティング

### 問題: HTMLが返される（JSON parse error）

**原因**: 環境変数 `VITE_API_URL` が設定されていない

**解決策**:
1. Vercelダッシュボードで環境変数を設定
2. 再デプロイ

### 問題: CORSエラー

**原因**: バックエンドのCORS設定

**解決策**: バックエンドのCORS設定は既に `allow_origins=["*"]` になっているため、通常は問題ありません

### 問題: タイムアウトエラー

**原因**: バックエンドが起動していない、または応答が遅い

**解決策**:
1. Renderダッシュボードでバックエンドのログを確認
2. バックエンドが正常に起動しているか確認

## ローカル開発環境

### フロントエンド
```bash
cd frontend
npm run dev
```

### バックエンド
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ローカル環境では、`vite.config.ts`のプロキシ設定により、`/api`が自動的に`http://localhost:8000`にプロキシされます。

