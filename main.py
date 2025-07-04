#!/usr/bin/env python3
import os
import json
import requests
import argparse
import time
from base64 import b64encode
from datetime import datetime, timedelta
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(
        description='Toggl Track のタイムエントリーに自動でタグを追加します。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用例:
  %(prog)s                    # 昨日のエントリーを処理
  %(prog)s --date 2025-07-01  # 特定の日付を処理
  %(prog)s --today            # 今日のエントリーを処理
  %(prog)s --dry-run          # 実際に更新せずに確認
  %(prog)s --interactive      # 対話的にタグを選択
        '''
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    # 日付関連オプション
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        '--date',
        type=str,
        help='処理する日付を指定 (YYYY-MM-DD形式)',
        metavar='YYYY-MM-DD'
    )
    date_group.add_argument(
        '--today',
        action='store_true',
        help='今日のエントリーを処理'
    )
    date_group.add_argument(
        '--days',
        type=int,
        help='過去N日分を処理',
        metavar='N'
    )
    
    # その他のオプション
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際に更新せずに対象エントリーを表示'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='対話的にタグを選択・編集する'
    )
    
    return parser.parse_args()

def make_request_with_retry(method, url, headers, max_retries=3, **kwargs):
    """リトライ機能付きのHTTPリクエスト"""
    for attempt in range(max_retries):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, **kwargs)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # 成功またはクライアントエラー（4xx）の場合はリトライしない
            if response.status_code < 500:
                return response
            
            # サーバーエラー（5xx）の場合はリトライ
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数バックオフ
                print(f"⏳ Server error {response.status_code}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⏳ Network error: {e}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ Network error after {max_retries} attempts: {e}")
                raise
    
    return response

def validate_config_file(config_path):
    """config.jsonの検証"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {config_path} not found")
        print(f"   💡 Hint: Create {config_path} with project name to tag mappings")
        return False, {}
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {config_path}")
        print(f"   💡 Hint: Check JSON syntax at line {e.lineno}, column {e.colno}")
        return False, {}
    
    if not isinstance(config, dict):
        print(f"❌ Error: {config_path} must contain a JSON object")
        return False, {}
    
    if not config:
        print(f"⚠️  Warning: {config_path} is empty - no project mappings defined")
        return True, {}
    
    # プロジェクト名とタグの検証
    for project_name, tags in config.items():
        if not isinstance(project_name, str) or not project_name.strip():
            print(f"❌ Error: Project name must be a non-empty string: {repr(project_name)}")
            return False, {}
        
        if not isinstance(tags, list):
            print(f"❌ Error: Tags for '{project_name}' must be a list, got {type(tags).__name__}")
            return False, {}
        
        if not tags:
            print(f"⚠️  Warning: Project '{project_name}' has empty tag list")
            continue
        
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                print(f"❌ Error: Tag must be a non-empty string in project '{project_name}': {repr(tag)}")
                return False, {}
    
    print(f"✅ Config validation passed: {len(config)} projects defined")
    return True, config

def validate_api_access(workspace_id, auth_header):
    """APIトークンとワークスペースアクセスの検証"""
    print("🔐 Validating API access...")
    
    # APIトークンの有効性確認
    try:
        me_response = make_request_with_retry('GET', 'https://api.track.toggl.com/api/v9/me', auth_header)
        if me_response.status_code == 401:
            print("❌ Error: Invalid API token")
            print("   💡 Hint: Check TOGGL_API_TOKEN in .env file")
            return False
        elif me_response.status_code != 200:
            print(f"❌ Error: Failed to validate API token: {me_response.status_code} {me_response.reason}")
            return False
        
        user_data = me_response.json()
        print(f"✅ API token valid for user: {user_data.get('fullname', 'Unknown')} ({user_data.get('email', 'Unknown')})")
        
        # デフォルトワークスペースIDの確認
        default_workspace = user_data.get('default_workspace_id')
        if default_workspace and str(default_workspace) != str(workspace_id):
            print(f"⚠️  Warning: Using workspace {workspace_id}, but your default is {default_workspace}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: Network error validating API access: {e}")
        return False
    
    # ワークスペースアクセス権限の確認
    try:
        workspace_url = f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}"
        workspace_response = make_request_with_retry('GET', workspace_url, auth_header)
        
        if workspace_response.status_code == 403:
            print(f"❌ Error: No access to workspace {workspace_id}")
            print("   💡 Hint: Check if you're a member of this workspace")
            return False
        elif workspace_response.status_code == 404:
            print(f"❌ Error: Workspace {workspace_id} not found")
            print("   💡 Hint: Verify WORKSPACE_ID in .env file")
            return False
        elif workspace_response.status_code != 200:
            print(f"❌ Error: Failed to access workspace: {workspace_response.status_code} {workspace_response.reason}")
            return False
        
        workspace_data = workspace_response.json()
        print(f"✅ Workspace access confirmed: {workspace_data.get('name', 'Unknown')} (ID: {workspace_id})")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: Network error validating workspace access: {e}")
        return False
    
    return True

def interactive_tag_selection(entry, project_name, suggested_tags, all_used_tags):
    """インタラクティブなタグ選択"""
    print(f"\n📝 Entry: {entry.get('description', 'No description')}")
    print(f"🏷️  Project: {project_name}")
    print(f"⏱️  Duration: {entry.get('duration', 0) / 3600:.1f} hours")
    print(f"📅 Start: {entry.get('start', 'Unknown')}")
    
    if suggested_tags:
        print(f"\n💡 Suggested tags: {', '.join(suggested_tags)}")
    
    print(f"\n選択肢:")
    print(f"  1. 提案されたタグを使用: {suggested_tags}")
    print(f"  2. カスタムタグを入力")
    print(f"  3. よく使われるタグから選択")
    print(f"  4. スキップ（タグを追加しない）")
    
    while True:
        try:
            choice = input("\n選択してください (1-4): ").strip()
            
            if choice == '1':
                return suggested_tags
            
            elif choice == '2':
                print("\nカスタムタグを入力してください（カンマ区切りで複数可）:")
                custom_input = input("タグ: ").strip()
                if custom_input:
                    custom_tags = [tag.strip() for tag in custom_input.split(',') if tag.strip()]
                    return custom_tags
                else:
                    print("❌ タグが入力されませんでした")
                    continue
            
            elif choice == '3':
                if all_used_tags:
                    print(f"\nよく使われるタグ:")
                    sorted_tags = sorted(list(all_used_tags))
                    for i, tag in enumerate(sorted_tags[:10], 1):  # 最大10個表示
                        print(f"  {i}. {tag}")
                    
                    tag_choice = input("\n番号を選択してください（複数選択は「1,3,5」のように）: ").strip()
                    try:
                        indices = [int(x.strip()) - 1 for x in tag_choice.split(',')]
                        selected_tags = [sorted_tags[i] for i in indices if 0 <= i < len(sorted_tags)]
                        if selected_tags:
                            return selected_tags
                        else:
                            print("❌ 有効な番号が選択されませんでした")
                            continue
                    except (ValueError, IndexError):
                        print("❌ 無効な入力です")
                        continue
                else:
                    print("⚠️  利用可能なタグがありません")
                    continue
            
            elif choice == '4':
                return None  # スキップ
            
            else:
                print("❌ 1-4の数字を入力してください")
                continue
                
        except KeyboardInterrupt:
            print("\n\n❌ 操作がキャンセルされました")
            return None
        except EOFError:
            print("\n\n❌ 入力が終了しました")
            return None

def collect_all_used_tags(project_tag_map):
    """設定ファイルから全ての使用されているタグを収集"""
    all_tags = set()
    for tags in project_tag_map.values():
        all_tags.update(tags)
    return all_tags

def main():
    """メイン処理"""
    args = parse_arguments()
    
    load_dotenv()
    
    API_TOKEN = os.getenv('TOGGL_API_TOKEN')
    WORKSPACE_ID = os.getenv('WORKSPACE_ID')
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tokyo')  # デフォルトは日本時間
    
    if not API_TOKEN or not WORKSPACE_ID:
        print("❌ Error: TOGGL_API_TOKEN and WORKSPACE_ID must be set in .env file")
        exit(1)
    
    # タイムゾーンの検証
    try:
        user_tz = ZoneInfo(TIMEZONE)
    except Exception as e:
        print(f"❌ Error: Invalid timezone '{TIMEZONE}'. Please check TIMEZONE in .env file.")
        print(f"   Common timezones: Asia/Tokyo, America/New_York, Europe/London, UTC")
        exit(1)
    
    # config.jsonの検証
    config_valid, PROJECT_TAG_MAP = validate_config_file('config.json')
    if not config_valid:
        exit(1)

    auth_header = {
        "Authorization": f"Basic {b64encode(f'{API_TOKEN}:api_token'.encode()).decode()}"
    }

    # APIアクセスの検証
    if not validate_api_access(WORKSPACE_ID, auth_header):
        exit(1)

    now_local = datetime.now(user_tz)
    
    # プロジェクト情報のキャッシュ
    project_cache = {}
    
    # インタラクティブモード用の全タグリスト
    all_used_tags = collect_all_used_tags(PROJECT_TAG_MAP) if args.interactive else set()
    
    # 処理する日付を決定
    if args.date:
        # 指定された日付を使用
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Error: 日付は YYYY-MM-DD 形式で指定してください (例: 2025-07-01)")
            exit(1)
        dates_to_process = [target_date]
    elif args.today:
        # 今日を処理
        dates_to_process = [now_local.date()]
    elif args.days:
        # 過去N日分を処理
        if args.days < 1:
            print(f"❌ Error: --days は1以上の数値を指定してください")
            exit(1)
        dates_to_process = [now_local.date() - timedelta(days=i) for i in range(args.days)]
    else:
        # デフォルト: 昨日を処理
        dates_to_process = [now_local.date() - timedelta(days=1)]
    
    # 各日付を処理
    for target_date in dates_to_process:
        print(f"\n{'='*50}")
        print(f"🔍 Processing date: {target_date} ({TIMEZONE})")
        print(f"{'='*50}")
        
        # ユーザータイムゾーンの00:00:00と23:59:59をUTCに変換
        start_local = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=user_tz)
        end_local = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=user_tz)

        # ISO形式でUTC時刻として出力
        start_date = start_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
        end_date = end_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

        url = "https://api.track.toggl.com/api/v9/me/time_entries"
        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        response = make_request_with_retry('GET', url, auth_header, params=params)

        if response.status_code != 200:
            print(f"❌ Failed to fetch time entries: {response.status_code} {response.reason}")
            print(f"Response: {response.text}")
            continue

        entries = response.json()
        print(f"📊 Found {len(entries)} time entries")

        processed = 0
        success = 0
        failed = 0

        log_entries = []

        for entry in entries:
            if entry.get('tags') and len(entry['tags']) > 0:
                continue
            
            project_id = entry.get('project_id')
            if not project_id:
                continue
            
            # プロジェクト情報をキャッシュから取得、なければAPIで取得
            if project_id in project_cache:
                project_name = project_cache[project_id]
            else:
                project_url = f"https://api.track.toggl.com/api/v9/workspaces/{WORKSPACE_ID}/projects/{project_id}"
                try:
                    project_response = make_request_with_retry('GET', project_url, auth_header)
                    
                    if project_response.status_code != 200:
                        print(f"❌ Failed to fetch project {project_id}: {project_response.status_code} {project_response.reason}")
                        if project_response.status_code == 403:
                            print(f"   ℹ️  Hint: Check if you have access to this project in workspace {WORKSPACE_ID}")
                        elif project_response.status_code == 404:
                            print(f"   ℹ️  Hint: Project {project_id} may have been deleted or moved")
                        continue
                    
                    project_data = project_response.json()
                    project_name = project_data.get('name', '')
                    # キャッシュに保存
                    project_cache[project_id] = project_name
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ Network error fetching project {project_id}: {e}")
                    continue
            
            # タグの決定
            suggested_tags = PROJECT_TAG_MAP.get(project_name, [])
            
            if args.interactive:
                # インタラクティブモード: ユーザーがタグを選択
                selected_tags = interactive_tag_selection(entry, project_name, suggested_tags, all_used_tags)
                if selected_tags is None:
                    print("⏭️  Skipped")
                    continue
                tags_to_add = selected_tags
            else:
                # 通常モード: 設定ファイルのマッピングに従う
                if project_name not in PROJECT_TAG_MAP:
                    continue
                tags_to_add = suggested_tags
            
            update_url = f"https://api.track.toggl.com/api/v9/workspaces/{WORKSPACE_ID}/time_entries/{entry['id']}"
            update_data = {"tags": tags_to_add}
            
            processed += 1
            
            if args.dry_run:
                # Dry-runモードでは実際に更新しない
                print(f"🔍 [DRY RUN] {project_name} -> {tags_to_add}")
                log_entry = {
                    "timestamp": now_local.isoformat(),
                    "status": "dry_run",
                    "entry_id": entry['id'],
                    "project_name": project_name,
                    "description": entry.get('description', ''),
                    "start": entry.get('start', ''),
                    "duration": entry.get('duration', 0),
                    "tags_to_add": tags_to_add
                }
                success += 1
            else:
                # 実際に更新する
                try:
                    update_response = make_request_with_retry('PUT', update_url, auth_header, json=update_data)
                except requests.exceptions.RequestException as e:
                    failed += 1
                    print(f"❌ {project_name} Network error: {e}")
                    log_entry = {
                        "timestamp": now_local.isoformat(),
                        "status": "network_error",
                        "entry_id": entry['id'],
                        "project_name": project_name,
                        "description": entry.get('description', ''),
                        "error_message": str(e)
                    }
                    log_entries.append(log_entry)
                    continue
            
                if update_response.status_code == 200:
                    success += 1
                    print(f"✅ {project_name} -> {tags_to_add}")
                    log_entry = {
                        "timestamp": now_local.isoformat(),
                        "status": "success",
                        "entry_id": entry['id'],
                        "project_name": project_name,
                        "description": entry.get('description', ''),
                        "start": entry.get('start', ''),
                        "duration": entry.get('duration', 0),
                        "tags_added": tags_to_add
                    }
                else:
                    failed += 1
                    print(f"❌ {project_name} {update_response.status_code} {update_response.reason}")
                    log_entry = {
                        "timestamp": now_local.isoformat(),
                        "status": "failed",
                        "entry_id": entry['id'],
                        "project_name": project_name,
                        "description": entry.get('description', ''),
                        "error_code": update_response.status_code,
                        "error_reason": update_response.reason
                    }
            
            log_entries.append(log_entry)

        print(f"\n📈 Summary for {target_date}:")
        print(f"   Total entries: {len(entries)}")
        print(f"   Processed: {processed}")
        if args.dry_run:
            print(f"   Would be updated: {success}")
            print(f"   Failed: {failed}")
        else:
            print(f"   Success: {success}")
            print(f"   Failed: {failed}")

        # ログディレクトリの作成
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # 実行時刻をファイル名に含める（JST）
        execution_time = now_local.strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"toggl_tag_log_{target_date}_{execution_time}.json")
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "execution_date": now_local.isoformat(),
                "target_date": str(target_date),
                "summary": {
                    "total_entries": len(entries),
                    "processed": processed,
                    "success": success,
                    "failed": failed
                },
                "changes": log_entries
            }, f, indent=2, ensure_ascii=False)
        print(f"📝 Log saved to: {log_filename}")
        
        # キャッシュ統計の表示
        if project_cache:
            print(f"💾 Project cache: {len(project_cache)} projects cached")

if __name__ == "__main__":
    main()