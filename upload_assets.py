import os
import sys
import urllib.request
from huggingface_hub import HfApi

def download_file(url, dest):
    print(f"📥 Downloading {url} to {dest}...")
    # Add a custom User-Agent to be safe
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, dest)
    print(f"✅ Downloaded {dest} ({os.path.getsize(dest)} bytes)")

def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ Error: HF_TOKEN env var not set")
        sys.exit(1)

    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    # Assets to download and upload
    assets = [
        ("https://files.catbox.moe/p418cz.pt", "models/best.pt"),
        ("https://files.catbox.moe/vz9ix2.mp4", "static/sample-fire.mp4"),
        ("https://files.catbox.moe/kzn8sg.mp4", "static/sample-smoke.mp4")
    ]

    api = HfApi()

    for url, path in assets:
        if not os.path.exists(path):
            download_file(url, path)
        
        print(f"🚀 Uploading {path} to Hugging Face Space...")
        api.upload_file(
            path_or_fileobj=path,
            path_in_repo=path,
            repo_id="Nikhil3235/fire-smoke-detection",
            repo_type="space",
            token=token
        )
        print(f"✨ Successfully uploaded {path}!")

if __name__ == "__main__":
    main()
