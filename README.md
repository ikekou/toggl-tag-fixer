# Toggl Tag Fixer

[日本語](README.ja.md) | English

An automated tool that detects untagged time entries in Toggl Track and adds tags based on project name mappings.

## 📋 Requirements

- Python 3.9+
- Toggl Track account
- Toggl API token
- Workspace ID

## 🚀 Setup

### Step 1: Clone or Download Repository

```bash
git clone https://github.com/ikekou/toggl-tag-fixer.git
cd toggl-tag-fixer
```

### Step 2: Create Python Virtual Environment (Recommended)

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Get Toggl API Token

1. Log in to [Toggl Track](https://track.toggl.com)
2. Open the left sidebar
3. Click "Profile" button in the sidebar
4. Scroll to the bottom of the profile page
5. Click "Click to reveal" or "Show" in the "API Token" section
6. Copy the 32-character alphanumeric token

### Step 5: Get Workspace ID

**Method 1: Using Browser Developer Tools**
1. Open developer tools (F12) in Toggl Track web app
2. Go to Network tab
3. Reload the page (F5)
4. Find "me" API call in the request list and click it
5. Check `default_workspace_id` value in Response or Preview tab

**Method 2: Direct API Call**
1. Open terminal or command prompt
2. Run the following command (replace YOUR_API_TOKEN with actual token):
```bash
curl -u YOUR_API_TOKEN:api_token https://api.track.toggl.com/api/v9/me
```
3. Find `default_workspace_id` value in the returned JSON data

### Step 6: Configure Environment Variables

Copy `.env.sample` to `.env` and enter your information:

```bash
cp .env.sample .env
```

Edit the `.env` file:

```bash
TOGGL_API_TOKEN=your_api_token_here
WORKSPACE_ID=your_workspace_id_here
```

**Values to enter:**
- `TOGGL_API_TOKEN=` followed by the API token (32-character alphanumeric) from Step 4
- `WORKSPACE_ID=` followed by the workspace ID (7-digit number) from Step 5
- `TIMEZONE=` followed by your preferred timezone (optional, default: Asia/Tokyo)

Example:
```bash
TOGGL_API_TOKEN=1234567890abcdef1234567890abcdef
WORKSPACE_ID=1234567
TIMEZONE=Asia/Tokyo
```

### Step 7: Configure Project→Tag Mappings

Edit `config.json` file to set your project names and tags:

```json
{
  "Project Name 1": ["tag1", "tag2"],
  "Project Name 2": ["tag3"],
  "Project Name 3": ["tag4", "tag5"]
}
```

Example:
```json
{
  "Internal Meeting": ["meeting", "internal"],
  "Client A Project": ["client", "development"],
  "Learning & Training": ["learning"]
}
```

**Note**: Project names must exactly match those registered in Toggl.

## ✨ Features

### 🎯 Core Features
- ✅ Auto-detect untagged time entries from previous day
- ✅ Automatic tagging based on project names
- ✅ Detailed logging output (JSON format)

### 📅 Date Processing
- ✅ Specific date targeting (--date)
- ✅ Today's entries processing (--today)
- ✅ Multiple past days batch processing (--days)
- ✅ Timezone support (.env configuration)

### 🛡️ Safety
- ✅ Dry-run mode for preview
- ✅ API token & workspace validation
- ✅ config.json syntax checking
- ✅ Detailed error messages

### 🚀 Performance
- ✅ Project information caching
- ✅ Network error retry (exponential backoff)
- ✅ Efficient API calls

### 🎨 User Experience
- ✅ Interactive mode (dialog-based tag selection)
- ✅ Colorful output with icons
- ✅ Comprehensive help and documentation
- ✅ Progress display and cache statistics

## 🎯 Usage

### Quick Start (Mac Users)

**For first-time setup:**
1. Double-click `run-setup.command` to automatically set up the environment
2. Edit `.env` and `config.json` files as guided
3. Double-click `run-toggl-tag-fixer.command` to run the tool

### Basic Usage (Command Line)

After completing all setup, run:

```bash
python main.py
```

### Detailed Options

The tool provides many convenient options:

#### Date Options
```bash
# Default: process yesterday's entries
python main.py

# Process specific date
python main.py --date 2025-07-01

# Process today's entries
python main.py --today

# Process past 3 days
python main.py --days 3
```

#### Safety Options
```bash
# Preview target entries without actually updating (recommended)
python main.py --dry-run

# Dry-run for specific date
python main.py --date 2025-07-01 --dry-run
```

#### Interactive Mode
```bash
# Select/edit tags interactively
python main.py --interactive

# Interactive mode with dry-run
python main.py --interactive --dry-run
```

In interactive mode, you'll see these options for each entry:
- **1. Use suggested tags**: Auto-apply tags defined in config.json
- **2. Enter custom tags**: Manually input tags (comma-separated for multiple)
- **3. Choose from commonly used tags**: Select by number from existing tags
- **4. Skip**: Don't add tags to this entry

#### Other Options
```bash
# Show help
python main.py --help

# Show version
python main.py --version
```

### Timezone Configuration (Optional)

Default is Japan time (Asia/Tokyo), but can be changed in .env file:

```bash
# Add to .env file
TIMEZONE=America/New_York  # New York time
TIMEZONE=Europe/London     # London time
TIMEZONE=UTC              # UTC time
```

## 📊 Understanding Output

### Normal Mode
When executed, you'll see output like:

```
✅ Config validation passed: 11 projects defined
🔐 Validating API access...
✅ API token valid for user: Your Name (email@example.com)
✅ Workspace access confirmed: Workspace Name (ID: 1234567)

==================================================
🔍 Processing date: 2025-07-04 (Asia/Tokyo)
==================================================
📊 Found 15 time entries
✅ Internal Meeting -> ['meeting', 'internal']
✅ Client A Project -> ['client', 'development']
❌ Client B Project 403 Forbidden

📈 Summary for 2025-07-04:
   Total entries: 15
   Processed: 3
   Success: 2
   Failed: 1
📝 Log saved to: logs/toggl_tag_log_2025-07-04_20250705_123456.json
💾 Project cache: 5 projects cached
```

### Dry-run Mode
```bash
python main.py --dry-run
```
```
🔍 [DRY RUN] Internal Meeting -> ['meeting', 'internal']
🔍 [DRY RUN] Client A Project -> ['client', 'development']

📈 Summary for 2025-07-04:
   Total entries: 15
   Processed: 2
   Would be updated: 2
   Failed: 0
```

### Icon Meanings
- ✅ : Successfully added tags
- 🔍 : Dry-run mode (no actual updates)
- ❌ : Failed to add tags (permission error, etc.)
- 💾 : Project cache statistics
- 📝 : Log file location

## 🔧 Troubleshooting

### Error: "TOGGL_API_TOKEN and WORKSPACE_ID must be set"

Check if `.env` file is properly configured.

### Error: "401 Unauthorized"

Verify your API token is correct. If expired, get a new one.

### Error: "403 Forbidden"

- Check if workspace ID is correct
- Verify you have access permissions to the workspace

### Tags not being added

- Check if project name exactly matches the configuration in `config.json`
- Verify target entries don't already have tags (entries with existing tags are skipped)

### Error: "Invalid timezone"

Check TIMEZONE setting in `.env` file:
- Correct format: `Asia/Tokyo`, `America/New_York`, `Europe/London`, `UTC`
- See [Timezone list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### config.json errors

- Check JSON format (commas, brackets, quotes)
- Verify project names are strings and tags are arrays
- Ensure no trailing comma after the last item

### Interactive mode not responding

- Enter a number (1-4) and press Enter
- Use Ctrl+C to cancel

## 🤖 Automated Execution (Optional)

### Mac/Linux cron setup

To run automatically at 9 AM daily:

```bash
crontab -e
```

Add:
```
0 9 * * * cd /path/to/toggl-tag-fixer && /path/to/venv/bin/python main.py >> log.txt 2>&1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Select "Create Basic Task"
3. Set trigger to "Daily"
4. Configure action:
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\toggl-tag-fixer`

## 📝 Notes

- This tool processes previous day's entries by default (depends on timezone setting)
- Entries with existing tags are skipped
- Entries without assigned projects are also skipped