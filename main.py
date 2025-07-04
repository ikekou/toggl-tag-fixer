#!/usr/bin/env python3
import os
import json
import requests
import argparse
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
    
    return parser.parse_args()

def main():
    """メイン処理"""
    args = parse_arguments()
    
    load_dotenv()
    
    API_TOKEN = os.getenv('TOGGL_API_TOKEN')
    WORKSPACE_ID = os.getenv('WORKSPACE_ID')
    
    if not API_TOKEN or not WORKSPACE_ID:
        print("❌ Error: TOGGL_API_TOKEN and WORKSPACE_ID must be set in .env file")
        exit(1)
    
    with open('config.json', 'r', encoding='utf-8') as f:
        PROJECT_TAG_MAP = json.load(f)

    auth_header = {
        "Authorization": f"Basic {b64encode(f'{API_TOKEN}:api_token'.encode()).decode()}"
    }

    jst = ZoneInfo("Asia/Tokyo")
    now_jst = datetime.now(jst)
    
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
        dates_to_process = [now_jst.date()]
    elif args.days:
        # 過去N日分を処理
        if args.days < 1:
            print(f"❌ Error: --days は1以上の数値を指定してください")
            exit(1)
        dates_to_process = [now_jst.date() - timedelta(days=i) for i in range(args.days)]
    else:
        # デフォルト: 昨日を処理
        dates_to_process = [now_jst.date() - timedelta(days=1)]
    
    # 各日付を処理
    for target_date in dates_to_process:
        print(f"\n{'='*50}")
        print(f"🔍 Processing date: {target_date} (JST)")
        print(f"{'='*50}")
        
        # JSTの00:00:00と23:59:59をUTCに変換
        start_jst = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=jst)
        end_jst = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=jst)

        # ISO形式でUTC時刻として出力
        start_date = start_jst.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
        end_date = end_jst.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

        url = "https://api.track.toggl.com/api/v9/me/time_entries"
        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        response = requests.get(url, headers=auth_header, params=params)

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
            
            project_url = f"https://api.track.toggl.com/api/v9/workspaces/{WORKSPACE_ID}/projects/{project_id}"
            project_response = requests.get(project_url, headers=auth_header)
            
            if project_response.status_code != 200:
                print(f"❌ Failed to fetch project {project_id}: {project_response.status_code}")
                continue
            
            project_data = project_response.json()
            project_name = project_data.get('name', '')
            
            if project_name not in PROJECT_TAG_MAP:
                continue
            
            tags_to_add = PROJECT_TAG_MAP[project_name]
            
            update_url = f"https://api.track.toggl.com/api/v9/workspaces/{WORKSPACE_ID}/time_entries/{entry['id']}"
            update_data = {"tags": tags_to_add}
            
            processed += 1
            
            if args.dry_run:
                # Dry-runモードでは実際に更新しない
                print(f"🔍 [DRY RUN] {project_name} -> {tags_to_add}")
                log_entry = {
                    "timestamp": now_jst.isoformat(),
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
                update_response = requests.put(update_url, headers=auth_header, json=update_data)
            
                if update_response.status_code == 200:
                    success += 1
                    print(f"✅ {project_name} -> {tags_to_add}")
                    log_entry = {
                        "timestamp": now_jst.isoformat(),
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
                        "timestamp": now_jst.isoformat(),
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
        execution_time_jst = now_jst.strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"toggl_tag_log_{target_date}_{execution_time_jst}.json")
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "execution_date": now_jst.isoformat(),
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

if __name__ == "__main__":
    main()