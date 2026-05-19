from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import json
import base64
import os
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import pickle
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# NVIDIA Llama setup
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
if not NVIDIA_API_KEY:
    raise ValueError("NVIDIA_API_KEY environment variable not set. Add it to your .env file.")

client = OpenAI(
    api_key=NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)
VISION_MODEL = "meta/llama-3.2-90b-vision-instruct"

# Data storage
DATA_FILE = 'processed_photos.json'
TEMPLATE_FILE = 'template.json'
CONFIG_FILE = 'drive_config.json'
TOKEN_FILE = 'token.pickle'
CLIENT_SECRET_FILE = 'client_secret.json'

# Google Drive & Sheets
SCOPES = ['https://www.googleapis.com/auth/drive', 
          'https://www.googleapis.com/auth/spreadsheets']

gs_client = None
drive_service = None
folder_id = None
spreadsheet = None

def load_config():
    """Load Google Drive config"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_config(config):
    """Save Google Drive config"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_processed_photos():
    """Load list of already processed photos"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_processed_photos(data):
    """Save list of processed photos"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_template():
    """Load template structure"""
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_template(template):
    """Save template structure"""
    with open(TEMPLATE_FILE, 'w') as f:
        json.dump(template, f, indent=2)

def get_google_credentials():
    """Get valid Google credentials from OAuth"""
    creds = None
    
    # Load saved token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def init_google_services_oauth():
    """Initialize Google Drive and Sheets with OAuth"""
    global gs_client, drive_service
    
    try:
        creds = get_google_credentials()
        
        if not creds:
            return False, "Not logged in"
        
        gs_client = gspread.authorize(creds)
        drive_service = build('drive', 'v3', credentials=creds)
        return True, "Connected to Google Drive and Sheets"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_photos_in_folder(folder_id):
    """Get all image files in a Google Drive folder"""
    try:
        query = f"'{folder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png' or mimeType='image/gif') and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)',
            pageSize=100
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        print(f"Error getting photos: {str(e)}")
        return []

def download_photo(file_id):
    """Download a photo from Google Drive"""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file.seek(0)
        return file.read()
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None

def get_or_create_sheet(folder_id, title, columns):
    """Get existing sheet or create new one in folder"""
    global spreadsheet
    
    try:
        # Try to find existing sheet in folder
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            # Open existing sheet
            spreadsheet = gs_client.open_by_key(files[0]['id'])
            return True, spreadsheet.url
        else:
            # Create new sheet
            spreadsheet = gs_client.create(title, folder_id=folder_id)
            worksheet = spreadsheet.sheet1
            worksheet.update_title("Daily Log")
            worksheet.append_row(columns)
            
            # Format header
            try:
                spreadsheet.format("A1", {
                    "backgroundColor": {
                        "red": 0.4,
                        "green": 0.49,
                        "blue": 0.93
                    },
                    "textFormat": {
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        "bold": True
                    }
                })
            except:
                pass
            
            return True, spreadsheet.url
    except Exception as e:
        return False, f"Error: {str(e)}"

def add_row_to_sheet(row_data, columns):
    """Add a row to the Google Sheet"""
    try:
        if not spreadsheet:
            return False, "No sheet open"
        
        worksheet = spreadsheet.sheet1
        row = [row_data.get(col, '') for col in columns]
        worksheet.append_row(row)
        
        return True, "Row added"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Load folder ID from config on startup
config = load_config()
if config:
    folder_id = config.get('folder_id')

@app.route('/')
def index():
    return render_template('index-nvidia.html')

@app.route('/api/upload-credentials', methods=['POST'])
def upload_credentials():
    """Upload Google OAuth client_secret.json"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        file.save(CLIENT_SECRET_FILE)
        return jsonify({'success': True, 'message': 'OAuth credentials uploaded successfully'})
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/google-login', methods=['POST'])
def google_login():
    """Initiate Google OAuth login"""
    try:
        if not os.path.exists(CLIENT_SECRET_FILE):
            return jsonify({'error': 'client_secret.json not found. Upload it first.'}), 400
        
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, SCOPES)
        
        creds = flow.run_local_server(port=8080)
        
        # Save token
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        success, message = init_google_services_oauth()
        
        return jsonify({
            'success': success,
            'message': message if success else 'Login failed'
        })
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/set-folder', methods=['POST'])
def set_folder():
    """Set the Google Drive folder ID"""
    data = request.get_json()
    folder_id_input = data.get('folder_id')
    
    if not folder_id_input:
        return jsonify({'error': 'No folder ID provided'}), 400
    
    try:
        global folder_id
        folder_id = folder_id_input
        
        file_metadata = drive_service.files().get(fileId=folder_id).execute()
        
        config = {
            'folder_id': folder_id,
            'folder_name': file_metadata['name'],
            'created_at': datetime.now().isoformat()
        }
        save_config(config)
        
        return jsonify({
            'success': True,
            'folder_name': file_metadata['name'],
            'message': f'Folder "{file_metadata["name"]}" connected successfully'
        })
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 400

@app.route('/api/analyze-template', methods=['POST'])
def analyze_template():
    """Analyze a sample photo to extract column structure"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        image_data = file.read()
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')
        
        # Determine media type
        media_type = 'image/jpeg'
        if file.filename.lower().endswith('.png'):
            media_type = 'image/png'
        elif file.filename.lower().endswith('.gif'):
            media_type = 'image/gif'
        
        # Call Llama vision API
        message = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this school daily log form. Extract ALL the labeled sections/columns exactly as they appear.

Return ONLY a JSON array of strings with column names (no markdown or backticks):
[
  "exact column name 1",
  "exact column name 2",
  ...
]

Be precise and get every single column/section from the form in order."""
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        response_text = message.choices[0].message.content
        
        # Extract JSON
        import re
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if not json_match:
            return jsonify({'error': 'Could not extract template', 'raw': response_text}), 400
        
        columns = json.loads(json_match.group(0))
        save_template(columns)
        
        return jsonify({
            'success': True,
            'columns': columns
        })
    
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Failed to parse: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/scan-folder', methods=['POST'])
def scan_folder():
    """Scan folder for new photos and extract data"""
    if not folder_id:
        return jsonify({'error': 'No folder configured'}), 400
    
    template = load_template()
    if not template:
        return jsonify({'error': 'No template set'}), 400
    
    try:
        # Get all photos in folder
        photos = get_photos_in_folder(folder_id)
        print(f"Found {len(photos)} photos in folder")  # Debug logging
        
        processed = load_processed_photos()
        print(f"Already processed: {len(processed)} photos")  # Debug logging
        
        new_entries = []
        
        for photo in photos:
            photo_id = photo['id']
            print(f"Processing: {photo['name']} (ID: {photo_id})")  # Debug logging
            
            # Skip if already processed
            if photo_id in processed:
                print(f"  Skipping - already processed")
                continue
            
            # Download and analyze photo
            photo_data = download_photo(photo_id)
            if not photo_data:
                print(f"  Failed to download")
                continue
            
            print(f"  Extracting data...")
            base64_photo = base64.standard_b64encode(photo_data).decode('utf-8')
            
            # Extract data using Llama
            message = client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_photo}"
                                }
                            },
                            {
                                "type": "text",
                                "text": f"""Extract all the handwritten/filled data from this school daily log form.

The columns in this form are: {', '.join(template)}

Return ONLY a JSON object (no markdown or backticks) with these exact keys:
{{
  "{template[0]}": "extracted value",
  "{template[1] if len(template) > 1 else 'other'}": "extracted value",
  ...
}}

Extract all data exactly as written. If a field is empty, use an empty string."""
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            response_text = message.choices[0].message.content
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                print(f"  Failed to extract JSON from response")
                continue
            
            data = json.loads(json_match.group(0))
            
            # Ensure sheet exists
            if not spreadsheet:
                get_or_create_sheet(folder_id, f"School Daily Log - {datetime.now().strftime('%Y-%m-%d')}", template)
            
            # Add to sheet
            success, msg = add_row_to_sheet(data, template)
            if success:
                processed[photo_id] = {
                    'filename': photo['name'],
                    'processed_at': datetime.now().isoformat()
                }
                new_entries.append({
                    'filename': photo['name'],
                    'data': data
                })
                print(f"  ✓ Successfully added to sheet")
            else:
                print(f"  Failed to add to sheet: {msg}")
        
        # Save processed list
        save_processed_photos(processed)
        
        return jsonify({
            'success': True,
            'new_entries': len(new_entries),
            'entries': new_entries,
            'total_photos_found': len(photos),
            'message': f'Processed {len(new_entries)} new photos out of {len(photos)} total'
        })
    
    except Exception as e:
        print(f"Error in scan_folder: {str(e)}")
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/get-config', methods=['GET'])
def get_config():
    """Get current config"""
    config = load_config()
    template = load_template()
    processed = load_processed_photos()
    creds = get_google_credentials()
    
    return jsonify({
        'configured': config is not None,
        'logged_in': creds is not None,
        'config': config,
        'template': template,
        'processed_count': len(processed)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
