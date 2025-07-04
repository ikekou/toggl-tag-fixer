# Toggl タグ自動補完ツール

English | [日本語](README.ja.md)

このツールは、Toggl Track の前日分のタイムエントリーから、タグが未設定のものを自動的に検出し、プロジェクト名に基づいてタグを追加します。

## 📋 必要なもの

- Python 3.9 以上
- Toggl Track アカウント
- Toggl API トークン
- ワークスペース ID

## 🚀 セットアップ手順

### ステップ 1: リポジトリのクローンまたはダウンロード

```bash
git clone https://github.com/ikekou/toggl-tag-fixer.git
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
2. 左のサイドバーを開く
3. サイドバー内の「Profile」ボタンをクリック
4. プロフィールページが開いたら、一番下までスクロール
5. 「API Token」セクションの「Click to reveal」または「Show」をクリックしてトークンを表示
6. 表示された32文字の英数字のトークンをコピー

### ステップ 5: ワークスペース ID の取得

**方法1: ブラウザの開発者ツールを使用**
1. Toggl Track のウェブアプリで、F12キーを押して開発者ツールを開く
2. Networkタブを選択
3. ページをリロード（F5キー）
4. リクエスト一覧から「me」というAPIコールを探してクリック
5. ResponseまたはPreviewタブで、`default_workspace_id` の値を確認

**方法2: Toggl APIを直接呼び出し**
1. ターミナルまたはコマンドプロンプトを開く
2. 以下のコマンドを実行（YOUR_API_TOKENを実際のトークンに置き換える）：
```bash
curl -u YOUR_API_TOKEN:api_token https://api.track.toggl.com/api/v9/me
```
3. 返されたJSONデータから `default_workspace_id` の値を確認

### ステップ 6: 環境変数の設定

`.env.sample` を `.env` にコピーして、取得した情報を入力：

```bash
cp .env.sample .env
```

次に `.env` ファイルを編集：

```bash
TOGGL_API_TOKEN=あなたのAPIトークン
WORKSPACE_ID=あなたのワークスペースID
```

**どこの値を入力するか：**
- `TOGGL_API_TOKEN=` の後に、ステップ 4 でコピーしたAPIトークン（32文字の英数字）を貼り付けます
- `WORKSPACE_ID=` の後に、ステップ 5 で確認したワークスペースID（7桁程度の数字）を入力します
- `TIMEZONE=` の後に、お好みのタイムゾーン（オプション、デフォルト: Asia/Tokyo）

例：
```bash
TOGGL_API_TOKEN=1234567890abcdef1234567890abcdef
WORKSPACE_ID=1234567
TIMEZONE=Asia/Tokyo
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

## ✨ 機能一覧

### 🎯 基本機能
- ✅ 前日分のタイムエントリーからタグ未設定を自動検出
- ✅ プロジェクト名に基づく自動タグ付け
- ✅ 詳細なログ出力（JSON形式）

### 📅 日付処理
- ✅ 特定日付の指定（--date）
- ✅ 今日のエントリー処理（--today）
- ✅ 過去複数日の一括処理（--days）
- ✅ タイムゾーン対応（.env設定）

### 🛡️ 安全性
- ✅ Dry-runモードで事前確認
- ✅ APIトークン・ワークスペースの検証
- ✅ config.jsonの構文チェック
- ✅ 詳細なエラーメッセージ

### 🚀 パフォーマンス
- ✅ プロジェクト情報のキャッシュ
- ✅ ネットワークエラー時のリトライ（指数バックオフ）
- ✅ 効率的なAPI呼び出し

### 🎨 ユーザビリティ
- ✅ インタラクティブモード（対話的タグ選択）
- ✅ カラフルな出力とアイコン
- ✅ 包括的なヘルプとドキュメント
- ✅ 進捗表示とキャッシュ統計

## 🎯 実行方法

### 基本的な使い方

すべての設定が完了したら、以下のコマンドで実行：

```bash
python main.py
```

### 詳細なオプション

ツールには多くの便利なオプションが用意されています：

#### 日付指定オプション
```bash
# デフォルト: 昨日のエントリーを処理
python main.py

# 特定の日付を処理
python main.py --date 2025-07-01

# 今日のエントリーを処理
python main.py --today

# 過去3日分を一括処理
python main.py --days 3
```

#### 安全確認オプション
```bash
# 実際に更新せずに対象エントリーを確認（推奨）
python main.py --dry-run

# 特定日付をdry-runで確認
python main.py --date 2025-07-01 --dry-run
```

#### インタラクティブモード
```bash
# 対話的にタグを選択・編集
python main.py --interactive

# インタラクティブモードでdry-run
python main.py --interactive --dry-run
```

インタラクティブモードでは、各エントリーに対して以下の選択肢が表示されます：
- **1. 提案されたタグを使用**: config.jsonで定義されたタグを自動適用
- **2. カスタムタグを入力**: 手動でタグを入力（カンマ区切りで複数可）
- **3. よく使われるタグから選択**: 既存のタグから番号で選択
- **4. スキップ**: そのエントリーにはタグを追加しない

#### その他のオプション
```bash
# ヘルプを表示
python main.py --help

# バージョンを表示
python main.py --version
```

### タイムゾーン設定（オプション）

デフォルトは日本時間（Asia/Tokyo）ですが、.envファイルで変更可能：

```bash
# .envファイルに追加
TIMEZONE=America/New_York  # ニューヨーク時間
TIMEZONE=Europe/London     # ロンドン時間
TIMEZONE=UTC              # UTC時間
```

## 📊 実行結果の見方

### 通常モード
実行すると以下のような出力が表示されます：

```
✅ Config validation passed: 11 projects defined
🔐 Validating API access...
✅ API token valid for user: あなたの名前 (email@example.com)
✅ Workspace access confirmed: ワークスペース名 (ID: 1234567)

==================================================
🔍 Processing date: 2025-07-04 (Asia/Tokyo)
==================================================
📊 Found 15 time entries
✅ 社内ミーティング -> ['meeting', 'internal']
✅ A社案件 -> ['client', 'development']
❌ B社案件 403 Forbidden

📈 Summary for 2025-07-04:
   Total entries: 15
   Processed: 3
   Success: 2
   Failed: 1
📝 Log saved to: logs/toggl_tag_log_2025-07-04_20250705_123456.json
💾 Project cache: 5 projects cached
```

### Dry-runモード
```bash
python main.py --dry-run
```
```
🔍 [DRY RUN] 社内ミーティング -> ['meeting', 'internal']
🔍 [DRY RUN] A社案件 -> ['client', 'development']

📈 Summary for 2025-07-04:
   Total entries: 15
   Processed: 2
   Would be updated: 2
   Failed: 0
```

### アイコンの意味
- ✅ : タグの追加に成功
- 🔍 : Dry-runモード（実際の更新なし）
- ❌ : タグの追加に失敗（権限エラーなど）
- 💾 : プロジェクトキャッシュの統計
- 📝 : ログファイルの保存場所

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

### エラー: "Invalid timezone"

`.env` ファイルのTIMEZONE設定を確認してください：
- 正しい形式: `Asia/Tokyo`, `America/New_York`, `Europe/London`, `UTC`
- [タイムゾーン一覧](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)で確認可能

### config.jsonのエラー

- JSON形式が正しいか確認（コンマ、括弧、引用符）
- プロジェクト名が文字列、タグが配列になっているか確認
- 最後の項目の後にコンマがないか確認

### インタラクティブモードで応答しない

- 数字（1-4）を入力してEnterキーを押してください
- Ctrl+Cで中断可能です

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

- このツールはデフォルトで前日のエントリーを処理します（タイムゾーン設定に依存）
- 既にタグが設定されているエントリーはスキップされます
- プロジェクトが設定されていないエントリーもスキップされます