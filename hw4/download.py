import requests
import tarfile
import os

def download_and_extract(url, folder="packages"):
  """
  Downloads a library from the provided URL, extracts it, and stores it in the specified folder.

  Args:
    url: The URL of the library to download.
    folder: The folder where the extracted library will be stored (default: "packages").
  """

  # Get the filename from the URL
  filename = url.split("/")[-1]

  # Create the packages folder if it doesn't exist
  os.makedirs(folder, exist_ok=True)

  # Download the library file
  try:
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for unsuccessful downloads
  except requests.exceptions.RequestException as e:
    print(f"Error downloading library: {e}")
    return

  # Save the downloaded file
  filepath = os.path.join(folder, filename)
  with open(filepath, "wb") as f:
    for chunk in response.iter_content(1024):
      f.write(chunk)

  # Extract the downloaded file (assuming it's a tar.gz archive)
  try:
    with tarfile.open(filepath, 'r:gz') as tar_ref:
      tar_ref.extractall(folder)
    print(f"Library downloaded and extracted to: {folder}/{filename.replace('.tar.gz', '')}")
  except tarfile.ReadError as e:
    print(f"Error extracting library: {e}")
    os.remove(filepath)  # Remove the downloaded file if extraction fails

if __name__ == "__main__":
  url = input("Enter the library download URL (tar.gz format): ")
  download_and_extract(url)
