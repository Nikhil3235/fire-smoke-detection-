import os
import sys
import urllib.request
from huggingface_hub import HfApi

# Custom print that writes to console and a log file
log_file = open("upload_log.txt", "w", encoding="utf-8")
def log_print(*args, **kwargs):
    print(*args, **kwargs)
    print(*args, file=log_file, **kwargs)
    log_file.flush()

def download_file(url, dest):
    log_print(f"📥 Downloading {url} to {dest}...")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, dest)
    log_print(f"✅ Downloaded {dest} ({os.path.getsize(dest)} bytes)")

def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        log_print("❌ Error: HF_TOKEN env var not set")
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
            try:
                download_file(url, path)
            except Exception as e:
                log_print(f"❌ Error downloading {url}: {e}")
                sys.exit(1)
        
        log_print(f"🚀 Uploading {path} to Hugging Face Space...")
        try:
            api.upload_file(
                path_or_fileobj=path,
                path_in_repo=path,
                repo_id="Nikhil3235/fire-smoke-detection",
                repo_type="space",
                token=token
            )
            log_print(f"✨ Successfully uploaded {path}!")
        except Exception as e:
            log_print(f"❌ Error uploading {path}: {e}")
            sys.exit(1)

    # Finally, upload the log file itself so we can read it!
    log_file.close()
    print("Uploading log file to Hugging Face Space...")
    try:
        api.upload_file(
            path_or_fileobj="upload_log.txt",
            path_in_repo="upload_log.txt",
            repo_id="Nikhil3235/fire-smoke-detection",
            repo_type="space",
            token=token
        )
        print("Log file uploaded successfully!")
    except Exception as e:
        print(f"Error uploading log file: {e}")

if __name__ == "__main__":
    main()
