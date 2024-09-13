import requests
import hashlib
import os
import time
import json
from tqdm import tqdm

def download_extension(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        start_time = time.time()
        downloaded = 0
        for data in response.iter_content(block_size):
            size = file.write(data)
            downloaded += size
            progress_bar.update(size)
            
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                speed = downloaded / elapsed_time / 1024 / 1024  # MB/s
                progress_bar.set_postfix(speed=f"{speed:.2f} MB/s", refresh=True)
    
    return filename

def calculate_file_hash(filename):
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_saved_hashes():
    if os.path.exists('extension_hashes.json'):
        with open('extension_hashes.json', 'r') as f:
            return json.load(f)
    return {}

def save_hash(filename, hash_value):
    hashes = load_saved_hashes()
    hashes[filename] = hash_value
    with open('extension_hashes.json', 'w') as f:
        json.dump(hashes, f, indent=2)

def main():
    extension_url = "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ms-python/vsextensions/python/latest/vspackage"
    filename = "python_extension.vsix"
    
    print("Downloading VSCode extension...")
    try:
        downloaded_file = download_extension(extension_url, filename)
    except requests.RequestException as e:
        print(f"Error downloading the file: {e}")
        return

    print("\nCalculating file hash...")
    calculated_hash = calculate_file_hash(downloaded_file)
    print(f"Calculated hash: {calculated_hash}")

    saved_hashes = load_saved_hashes()
    if filename in saved_hashes:
        print("\nComparing with previously saved hash...")
        if calculated_hash == saved_hashes[filename]:
            print("The file hash matches the previously saved hash.")
        else:
            print("Warning: The file hash is different from the previously saved hash.")
            print(f"Previous hash: {saved_hashes[filename]}")
    else:
        print("\nNo previously saved hash found for this file.")

    save_hash(filename, calculated_hash)
    print(f"\nThe current hash has been saved for future comparisons.")

if __name__ == "__main__":
    main()