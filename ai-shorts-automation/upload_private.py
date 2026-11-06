"""Opt-in OAuth upload, always private. Never commit OAuth credentials."""
import argparse
from pathlib import Path


def upload(video, client_secret, title, description="Generated for private review"):
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    video = Path(video)
    if not video.is_file():
        raise FileNotFoundError(video)
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secret), ["https://www.googleapis.com/auth/youtube.upload"]
    )
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)
    request = youtube.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": title, "description": description, "categoryId": "22"},
              "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}},
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True),
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    print("Uploaded private video:", response["id"])
    return response["id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="Generated for private review")
    args = parser.parse_args()
    upload(args.video, args.client_secret, args.title, args.description)
