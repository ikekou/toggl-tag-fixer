#!/usr/bin/env python3
import os
import json
import requests
from base64 import b64encode
from datetime import datetime, timedelta
from dotenv import load_dotenv

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

from zoneinfo import ZoneInfo
jst = ZoneInfo("Asia/Tokyo")
now_jst = datetime.now(jst)
yesterday_jst = now_jst.date() - timedelta(days=1)

# JSTの00:00:00と23:59:59をUTCに変換
start_jst = datetime.combine(yesterday_jst, datetime.min.time()).replace(tzinfo=jst)
end_jst = datetime.combine(yesterday_jst, datetime.max.time()).replace(tzinfo=jst)

# ISO形式でUTC時刻として出力
start_date = start_jst.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
end_date = end_jst.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

print(f"🔍 Fetching time entries for {yesterday_jst} (JST)...")

url = "https://api.track.toggl.com/api/v9/me/time_entries"
params = {
    "start_date": start_date,
    "end_date": end_date
}

response = requests.get(url, headers=auth_header, params=params)

if response.status_code != 200:
    print(f"❌ Failed to fetch time entries: {response.status_code} {response.reason}")
    print(f"Response: {response.text}")
    exit(1)

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
    
    update_response = requests.put(update_url, headers=auth_header, json=update_data)
    
    processed += 1
    
    if update_response.status_code == 200:
        success += 1
        print(f"✅ {project_name} -> {tags_to_add}")
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
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
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "entry_id": entry['id'],
            "project_name": project_name,
            "description": entry.get('description', ''),
            "error_code": update_response.status_code,
            "error_reason": update_response.reason
        }
    
    log_entries.append(log_entry)

print(f"\n📈 Summary:")
print(f"   Total entries: {len(entries)}")
print(f"   Processed: {processed}")
print(f"   Success: {success}")
print(f"   Failed: {failed}")

# ログディレクトリの作成
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 実行時刻をファイル名に含める（JST）
execution_time_jst = now_jst.strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"toggl_tag_log_{yesterday_jst}_{execution_time_jst}.json")
with open(log_filename, 'w', encoding='utf-8') as f:
    json.dump({
        "execution_date": now_jst.isoformat(),
        "target_date": str(yesterday_jst),
        "summary": {
            "total_entries": len(entries),
            "processed": processed,
            "success": success,
            "failed": failed
        },
        "changes": log_entries
    }, f, indent=2, ensure_ascii=False)
print(f"\n📝 Log saved to: {log_filename}")