import requests

def download_vsix(extension_id):
    """Downloads a VSIX extension from the Visual Studio Code Marketplace.

    Args:
        extension_id (str): The ID of the extension to download in the format 'publisher.extension'.
    """
    
    # Marketplace API URL to get the extension metadata
    marketplace_url = f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{extension_id.split('.')[0]}/vsextensions/{extension_id.split('.')[1]}/latest/vspackage"

    # Download the VSIX file
    response = requests.get(marketplace_url, stream=True)
    
    if response.status_code == 200:
        filename = f"{extension_id}.vsix"
        with open(filename, 'wb') as vsix_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    vsix_file.write(chunk)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download the extension. Status code: {response.status_code}")

# Example usage:
extension_id = "yy0931.vscode-sqlite3-editor"  # Replace with the desired extension ID
download_vsix(extension_id)
