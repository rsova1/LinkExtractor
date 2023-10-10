import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import time

# Define permissions
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Authenticate with Google
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('/Users/ryan/Downloads/client_secret_442306611800-vn1om04upmoguo7ocha051b12bnksqej.apps.googleusercontent.com.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

drive_service = build('drive', 'v3', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)

# Retrieve file links from Google Drive
def list_files(service, folder_id=None, path=[]):
    results = []
    page_token = None
    query = "'{}' in parents and trashed = false".format(folder_id) if folder_id else "trashed = false"
    while True:
        response = service.files().list(q=query,
                                        corpora='drive',
                                        driveId='0APD3Q4oQLcmSUk9PVA',
                                        includeItemsFromAllDrives=True,
                                        supportsAllDrives=True,
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name, mimeType, webViewLink)',
                                        pageToken=page_token).execute()
        print(response)
        for file in response.get('files', []):
            current_item = {
                'id': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink'),
                'path': path
            }
            results.append(current_item)
            if file.get('mimeType') == 'application/vnd.google-apps.folder':
                results.extend(list_files(service, file.get('id'), path + [file.get('name')]))
        page_token = response.get('nextPageToken', None)
        #time.sleep(1)  # Introduce a delay of 1 second between requests
        if not page_token:
            break
    return results

# Write links to Google Sheets
def write_to_sheet(service, sheet_id, data):
    values = [["Path", "Name", "Link"]]
    for item in data:
        if 'path' in item:
            row = item['path'] + [item['name'], item['webViewLink']]
            values.append(row)
        else:
            print(f"Missing 'path' for item: {item}")  # Log the problematic item
    body = {'values': values}
    range_name = 'A1:Z{}'.format(len(data) + 1)
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_name,
        valueInputOption="RAW", body=body).execute()
    print(values[:10])  # Print the first 10 rows, for a quick preview.


all_files = list_files(drive_service, '1CnzbSRtIEnQo-jXxnX49WjZ3tXVaYNdY')
write_to_sheet(sheets_service, '1xzW3-VX_qgn8CU6U-bvJpvBmvpWuhEfkJVnzGz79UKM', all_files)
print(f"Found {len(all_files)} files/folders.")
print(all_files[:10])  # This will print the first 10 files/folders, for a quick data preview.