import requests
import os
import hashlib
from urllib.parse import urlparse, unquote

def download_vsix(extension_id):
    """
    Downloads a VSIX extension from the Visual Studio Code Marketplace.
    Ensures the file is in .vsix format, checks download progress to 100%,
    verifies file integrity, and only outputs the .vsix file on success.

    Args:
        extension_id (str): The ID of the extension to download in the format 'publisher.extension'.

    Returns:
        str: The path to the downloaded .vsix file, or None if the download failed.
    """
    
    metadata_url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    
    payload = {
        "filters": [
            {
                "criteria": [
                    {"filterType": 7, "value": extension_id}
                ]
            }
        ],
        "flags": 0x1 | 0x2 | 0x4 | 0x800
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json;api-version=7.1-preview.1"
    }

    try:
        response = requests.post(metadata_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("results") or not data["results"][0].get("extensions"):
            return None
        
        extension = data["results"][0]["extensions"][0]
        vsix_url = extension["versions"][0]["files"][0]["source"]
        
        if not vsix_url.lower().endswith('.vsix'):
            return None
        
        filename = get_filename_from_url(vsix_url, extension_id)
        
        with requests.get(vsix_url, stream=True, timeout=30) as vsix_response:
            vsix_response.raise_for_status()
            total_size = int(vsix_response.headers.get('content-length', 0))
            
            temp_filename = f"{filename}.temp"
            sha256_hash = hashlib.sha256()
            try:
                with open(temp_filename, 'wb') as vsix_file:
                    downloaded = 0
                    for chunk in vsix_response.iter_content(chunk_size=8192):
                        if chunk:
                            vsix_file.write(chunk)
                            sha256_hash.update(chunk)
                            downloaded += len(chunk)
                            print_progress(downloaded, total_size)
                
                if downloaded != total_size:
                    raise Exception("Download incomplete")
                
                print("\nVerifying file integrity...")
                if verify_integrity(temp_filename, sha256_hash.hexdigest()):
                    os.rename(temp_filename, filename)
                    return filename
                else:
                    raise Exception("File integrity check failed")
            except Exception as e:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                return None
    
    except requests.RequestException:
        return None
    except Exception:
        return None

def get_filename_from_url(url, fallback_name):
    """Extracts filename from URL or generates a safe filename."""
    parsed_url = urlparse(url)
    filename = unquote(os.path.basename(parsed_url.path))
    if not filename.lower().endswith('.vsix'):
        filename = f"{fallback_name}.vsix"
    return sanitize_filename(filename)

def sanitize_filename(filename):
    """Sanitizes the filename to ensure it's safe for the file system."""
    return "".join(c for c in filename if c.isalnum() or c in "._- ").rstrip()

def print_progress(downloaded, total):
    """Prints the download progress."""
    percent = int(downloaded * 100 / total)
    bar = '█' * int(percent / 2) + '-' * (50 - int(percent / 2))
    print(f"\r|{bar}| {percent:.1f}%", end="\r")

def verify_integrity(file_path, expected_hash):
    """Verifies the integrity of the downloaded file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash

if __name__ == "__main__":
    extension_id = input("Enter the extension ID (e.g., ms-vscode-remote.remote-wsl): ")
    result = download_vsix(extension_id)
    if result:
        print(f"{result}")
    else:
        print("Failed to download the VSIX file.")