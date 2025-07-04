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

yesterday = datetime.utcnow().date() - timedelta(days=1)
start_date = f"{yesterday}T00:00:00+00:00"
end_date = f"{yesterday}T23:59:59+00:00"

print(f"🔍 Fetching time entries for {yesterday}...")

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
    else:
        failed += 1
        print(f"❌ {project_name} {update_response.status_code} {update_response.reason}")

print(f"\n📈 Summary:")
print(f"   Total entries: {len(entries)}")
print(f"   Processed: {processed}")
print(f"   Success: {success}")
print(f"   Failed: {failed}")