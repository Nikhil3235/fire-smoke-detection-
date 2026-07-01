import os
import urllib.request
from huggingface_hub import HfApi

def download_file(url, dest):
    print(f"Downloading {url} to {dest}...")
    urllib.request.urlretrieve(url, dest)
    print(f"Downloaded {dest} ({os.path.getsize(dest)} bytes)")

def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN env var not set")
        return

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
            try:
                download_file(url, path)
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                continue
        print(f"Uploading {path} to Hugging Face Space...")
        try:
            api.upload_file(
                path_or_fileobj=path,
                path_in_repo=path,
                repo_id="Nikhil3235/fire-smoke-detection",
                repo_type="space",
                token=token
            )
            print(f"Successfully uploaded {path}!")
        except Exception as e:
            print(f"Error uploading {path}: {e}")

if __name__ == "__main__":
    main()
