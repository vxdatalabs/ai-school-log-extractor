# School Daily Log - Google Drive Auto-Sync (NVIDIA Llama + UV Edition)

## Workflow Overview

```
1. Setup (One-time)
   ├─ Download Google service account JSON
   ├─ Set NVIDIA_API_KEY in .env
   ├─ Set Google Drive folder ID
   └─ Upload template photo

2. Daily Use
   ├─ Manually upload photos to Google Drive folder
   └─ Click "Scan Folder & Extract" button
       ↓ App finds new photos
       ↓ Extracts data using Llama vision
       ↓ Auto-adds rows to Google Sheet
       ↓ Done!
```

## Prerequisites

- Python 3.8+
- UV package manager (https://docs.astral.sh/uv/)
- NVIDIA API key (free tier available)
- Google service account JSON
- Google Drive folder

## Installation

### 1. Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy BypassPolicy -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone/Setup Project

```bash
# Create project directory
mkdir school-daily-log
cd school-daily-log

# Copy all files into this directory
```

### 3. Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your NVIDIA API key
nano .env
# or use your editor of choice
```

**Content of .env:**
```
NVIDIA_API_KEY=your-nvidia-api-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Install Dependencies with UV

```bash
# Install from pyproject.toml
uv sync

# Or install from requirements.txt if using that
uv pip install -r requirements.txt
```

### 5. Run the App

```bash
uv run python app-nvidia-uv.py
```

App will start at `http://localhost:5000`

## Setup Steps (In App)

### Step 1: Upload Google Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "School Daily Log"
3. Enable APIs:
   - Google Drive API
   - Google Sheets API
4. Create Service Account:
   - Click "Create Service Account"
   - Name: `school-daily-log`
   - Grant Editor role
   - Create JSON key
5. Download JSON file
6. In app: Upload the JSON file

### Step 2: Set Google Drive Folder

1. Go to [Google Drive](https://drive.google.com)
2. Create a folder: "Daily Logs"
3. Right-click folder → "Get link"
4. Copy folder ID from URL: `https://drive.google.com/drive/folders/[FOLDER_ID]`
5. In app: Paste folder ID and click "Set Folder"

### Step 3: Analyze Template

1. Take a photo of your daily log form
2. In app: Upload the template photo
3. Click "Analyze Template"
4. App extracts column names automatically

### Step 4: Daily Workflow

**Every day when you have logs:**

1. Manually upload photos to the Google Drive folder
2. In app: Click "Scan Folder & Extract"
3. App automatically:
   - Finds new photos
   - Extracts all data using Llama vision
   - Adds rows to your Google Sheet
   - Shows results

## Common UV Commands

```bash
# Sync dependencies from pyproject.toml
uv sync

# Install a new package
uv pip install package-name

# Run Python with virtual env
uv run python script.py

# Run the Flask app
uv run python app-nvidia-uv.py

# Run with specific Python version
uv run --python 3.11 python app-nvidia-uv.py

# List installed packages
uv pip list

# Export requirements
uv pip freeze > requirements.txt
```

## Project Structure

```
school-daily-log/
├── app-nvidia-uv.py           # Flask backend with dotenv
├── templates/
│   └── index-nvidia.html      # Frontend
├── pyproject.toml             # UV project config
├── requirements.txt           # Alternative: pip requirements
├── .env                       # Your credentials (keep secret!)
├── .env.example               # Template for .env
├── .gitignore                 # Ignore sensitive files
├── google_credentials.json    # Service account (auto-created)
├── drive_config.json         # Folder config (auto-created)
├── processed_photos.json     # Tracking processed photos
└── template.json             # Column structure
```

## .gitignore

Create a `.gitignore` file to protect sensitive data:

```
# Environment variables
.env
.env.local

# Google credentials
google_credentials.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# UV cache
.uv/
.venv/

# IDE
.vscode/
.idea/
*.swp

# Data files (optional)
*.json
```

## Troubleshooting

### "NVIDIA_API_KEY not found"

Make sure .env file exists with your key:

```bash
# Check if .env exists
ls -la .env

# Check if variable is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('NVIDIA_API_KEY'))"
```

### "Module not found" error

Make sure to use `uv run`:

```bash
# Wrong ❌
python app-nvidia-uv.py

# Correct ✅
uv run python app-nvidia-uv.py
```

### "Folder not found" in app

- Verify folder ID is correct
- Make sure service account has access to folder
- Share folder with service account email

### "Google Sheets API not enabled"

- Go to Google Cloud Console
- APIs & Services → Library
- Search "Google Sheets API"
- Click "Enable"

### Photos not extracting

- Check photo quality (must be clear and readable)
- NVIDIA API has rate limits on free tier
- Wait a few minutes before rescanning
- Check app logs for errors

## NVIDIA API Information

- **Free Tier Available**: Yes
- **API Key**: Get at https://build.nvidia.com/
- **Model**: meta/llama-3.2-90b-vision-instruct
- **Rate Limits**: Check at https://build.nvidia.com/

## Performance Tips

1. **Batch Processing**: Upload multiple photos before scanning
2. **Rate Limiting**: NVIDIA free tier has limits, space out scans
3. **Clear Photos**: Better image quality = better extraction
4. **Use UV**: Faster than pip, better for development

## Support

- UV Documentation: https://docs.astral.sh/uv/
- NVIDIA API Docs: https://docs.nvidia.com/ai-enterprise/
- Google Drive API: https://developers.google.com/drive
- Flask: https://flask.palletsprojects.com

## Next Steps

1. Install UV
2. Create `.env` file with NVIDIA key
3. Get Google credentials JSON
4. Run `uv sync`
5. Run `uv run python app-nvidia-uv.py`
6. Follow the 4 setup steps in the UI

Enjoy! 🚀
