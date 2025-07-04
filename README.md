# Toggl タグ自動補完ツール

このツールは、Toggl Track の前日分のタイムエントリーから、タグが未設定のものを自動的に検出し、プロジェクト名に基づいてタグを追加します。

## 📋 必要なもの

- Python 3.9 以上
- Toggl Track アカウント
- Toggl API トークン
- ワークスペース ID

## 🚀 セットアップ手順

### ステップ 1: リポジトリのクローンまたはダウンロード

```bash
git clone <repository-url>
cd toggl-tag-fixer
```

### ステップ 2: Python 仮想環境の作成（推奨）

```bash
python -m venv venv

# Mac/Linux の場合
source venv/bin/activate

# Windows の場合
venv\Scripts\activate
```

### ステップ 3: 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### ステップ 4: Toggl API トークンの取得

1. [Toggl Track](https://track.toggl.com) にログイン
2. 右上のプロフィールアイコンをクリック
3. 「Profile settings」を選択
4. ページ下部の「API Token」セクションまでスクロール
5. 「Click to reveal」をクリックしてトークンを表示
6. トークンをコピー

### ステップ 5: ワークスペース ID の取得

1. Toggl Track のウェブアプリで、左側のメニューから使用するワークスペースを選択
2. ブラウザの URL を確認：`https://track.toggl.com/XXX/timer`
3. `XXX` の部分がワークスペース ID です（例：1234567）

### ステップ 6: 環境変数の設定

`.env` ファイルを編集して、取得した情報を入力：

```bash
TOGGL_API_TOKEN=あなたのAPIトークン
WORKSPACE_ID=あなたのワークスペースID
```

例：
```bash
TOGGL_API_TOKEN=1234567890abcdef1234567890abcdef
WORKSPACE_ID=1234567
```

### ステップ 7: プロジェクト→タグのマッピング設定

`config.json` ファイルを編集して、あなたのプロジェクト名とタグを設定：

```json
{
  "実際のプロジェクト名1": ["タグ1", "タグ2"],
  "実際のプロジェクト名2": ["タグ3"],
  "実際のプロジェクト名3": ["タグ4", "タグ5"]
}
```

例：
```json
{
  "社内ミーティング": ["meeting", "internal"],
  "A社案件": ["client", "development"],
  "勉強・研修": ["learning"]
}
```

**注意**: プロジェクト名は Toggl に登録されている名前と完全に一致する必要があります。

## 🎯 実行方法

すべての設定が完了したら、以下のコマンドで実行：

```bash
python main.py
```

## 📊 実行結果の見方

実行すると以下のような出力が表示されます：

```
🔍 Fetching time entries for 2024-01-14...
📊 Found 15 time entries
✅ 社内ミーティング -> ['meeting', 'internal']
✅ A社案件 -> ['client', 'development']
❌ B社案件 403 Forbidden

📈 Summary:
   Total entries: 15
   Processed: 3
   Success: 2
   Failed: 1
```

- ✅ : タグの追加に成功
- ❌ : タグの追加に失敗（権限エラーなど）

## 🔧 トラブルシューティング

### エラー: "TOGGL_API_TOKEN and WORKSPACE_ID must be set"

`.env` ファイルが正しく設定されているか確認してください。

### エラー: "401 Unauthorized"

API トークンが正しいか確認してください。トークンが期限切れの場合は新しいものを取得してください。

### エラー: "403 Forbidden"

- ワークスペース ID が正しいか確認
- 該当のワークスペースへのアクセス権限があるか確認

### タグが追加されない

- プロジェクト名が `config.json` の設定と完全に一致しているか確認
- 対象のエントリーに既にタグが設定されていないか確認（既にタグがある場合はスキップされます）

## 🤖 自動実行の設定（オプション）

### Mac/Linux での cron 設定例

毎日朝 9 時に自動実行する場合：

```bash
crontab -e
```

以下を追加：
```
0 9 * * * cd /path/to/toggl-tag-fixer && /path/to/venv/bin/python main.py >> log.txt 2>&1
```

### Windows でのタスクスケジューラ設定

1. タスクスケジューラを開く
2. 「基本タスクの作成」を選択
3. トリガーで「毎日」を選択
4. 操作で以下を設定：
   - プログラム: `C:\path\to\venv\Scripts\python.exe`
   - 引数: `main.py`
   - 開始: `C:\path\to\toggl-tag-fixer`

## 📝 注意事項

- このツールは前日（UTC時間）のエントリーのみを処理します
- 既にタグが設定されているエントリーはスキップされます
- プロジェクトが設定されていないエントリーもスキップされます

## 🆘 サポート

問題が発生した場合は、以下の情報を含めて報告してください：

1. エラーメッセージの全文
2. Python のバージョン（`python --version`）
3. 実行環境（Windows/Mac/Linux）