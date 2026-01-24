import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Load the keys from your GitHub Secrets
CLIENT_ID = os.environ.get('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('YOUTUBE_REFRESH_TOKEN')

def get_youtube_client():
    info = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(info)
    return build("youtube", "v3", credentials=credentials)

def upload_video(file_path, title, description):
    youtube = get_youtube_client()
    
    # This creates a title like: "Daily Video - Jan 24, 2026"
    today = datetime.date.today().strftime("%b %d, %2026")
    final_title = f"{base_title} - {today}"
    
    body = {
        'snippet': {
            'title': final_title,
            'description': description,
            'categoryId': '22' # 22 is "People & Blogs"
        },
        'status': {
            'privacyStatus': 'public' # changed from private to public!
        }
    }
    
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    
    print(f"Success! Video ID: {response['id']}")

if __name__ == "__main__":
    # This assumes your video is named 'daily_video.mp4' in your repo
    upload_video("daily_video.mp4", "My Futuristic Tech Terms Video", "Uploaded automatically via GitHub Actions!")
