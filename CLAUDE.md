# Toggl タグ自動補完ツール — Python ローカル実行版 実装指示書

## 1. 目的

Toggl Track の前日分タイムログから **タグ未設定エントリ** を抽出し、あらかじめ定義した「プロジェクト名→タグ」マッピングに基づいて自動でタグを追加する Python スクリプトを構築する。

---

## 2. 技術仕様

| 項目         | 内容                                     |
| ---------- | -------------------------------------- |
| 実行環境       | ローカル（Python 3.9+）                      |
| 言語・主要ライブラリ | `python` / `requests`, `python-dotenv` |
| API        | Toggl Track API v9（REST, Basic 認証）     |
| データファイル    | `.env`（機密情報）、`config.json`（マッピング定義）    |

---

## 3. ディレクトリ構成

```
toggl_tag_fixer/
├── main.py              # 実行スクリプト
├── config.json          # プロジェクト→タグ定義
├── .env                 # API トークンなど
└── requirements.txt     # 依存ライブラリ
```

---

## 4. ファイル詳細

### 4.1 `.env`

```env
TOGGL_API_TOKEN=your_toggl_api_token_here
WORKSPACE_ID=your_workspace_id_here
```

### 4.2 `config.json`

```json
{
  "Project Alpha": ["work", "design"],
  "Project Beta":  ["meeting"],
  "Project Gamma": ["research"]
}
```

### 4.3 `requirements.txt`

```txt
requests
python-dotenv
```

---

## 5. main.py — 実装仕様

### 5.1 全体フロー

1. `.env` を読み込み API 認証情報を取得。
2. `config.json` を読み込み、マッピング辞書 `PROJECT_TAG_MAP` を構築。
3. **前日（UTC）の開始・終了時刻**を計算し、`start_date` と `end_date` を生成。
4. **GET** `https://api.track.toggl.com/api/v9/me/time_entries` で前日エントリを取得。
5. 各エントリを走査し、以下を満たすものを処理対象とする。

   * `tags` が空または未定義
   * `project_name` が `PROJECT_TAG_MAP` に含まれる
6. 5 で抽出したエントリに対し **PUT** `https://api.track.toggl.com/api/v9/time_entries/{id}` を呼び出し、`{"tags": [...]} ` を送信。
7. 成功・失敗の結果を標準出力にログする。

### 5.2 キー実装ポイント

* **Basic 認証ヘッダー**：

  ```python
  from base64 import b64encode
  auth_header = {
      "Authorization": f"Basic {b64encode(f'{API_TOKEN}:api_token'.encode()).decode()}"
  }
  ```
* **前日取得ロジック**：

  ```python
  from datetime import datetime, timedelta
  yesterday = datetime.utcnow().date() - timedelta(days=1)
  start = f"{yesterday}T00:00:00+00:00"
  end   = f"{yesterday}T23:59:59+00:00"
  ```
* **エラーハンドリング**：`response.raise_for_status()` ではなく、`status_code` を確認し失敗時に詳細を出力。
* **ログ形式**：

  * 成功: `✅ Project Alpha -> ['work', 'design']`
  * 失敗: `❌ Project Beta 403 Forbidden`

---

## 6. 実行手順

```bash
# ① 仮想環境（任意）
python -m venv venv
source venv/bin/activate

# ② 依存ライブラリ
pip install -r requirements.txt

# ③ 設定ファイル準備
#    - .env: API トークン, WORKSPACE_ID を入力
#    - config.json: プロジェクト→タグを定義

# ④ 実行
python main.py
```

---

## 7. 成功条件 (Definition of Done)

* **前日分**のタイムエントリが取得できる。
* `tags` 未設定エントリのみを対象とする。
* `project_name` が `config.json` に存在する場合のみタグを付与。
* API 呼び出し後、ステータス 200 が返ること。
* ログにすべての結果が明確に出力されること。

---

## 8. 追加仕様（任意）

* `--dry-run` オプションで実際に PUT せず対象エントリ一覧のみ表示。
* 実行結果を `log.json` に保存。
* Python スクリプトを `cron` へ登録して自動実行。

---

## 9. スコープ外（今回実装しないもの）

* GUI や詳細な CLI オプション
* 複数日または期間指定の一括処理
* クラウド / コンテナデプロイ（Cloudflare Workers など）

---

## 10. 参考

* Toggl Track API Docs: [https://github.com/toggl/toggl\_api\_docs](https://github.com/toggl/toggl_api_docs)

---

> **備考**: 上記指示書に従い、`main.py` を実装し、動作確認が取れたら完了。
