import requests
import gzip
import io
import os
import re
import xml.etree.ElementTree as ET
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


# --- Configuration ---
BUCKET_URL = "https://vcthackathon-data.s3.us-west-2.amazonaws.com/"
LISTING_PARAMS = {'list-type': '2'}
NAMESPACE = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
DOWNLOAD_DIR = "f:\VCT-data"

# --- Fetch all object keys from the public S3 bucket ---
def get_all_keys():
    keys = []
    continuation_token = None

    print("Fetching keys from S3 bucket...")

    while True:
        params = LISTING_PARAMS.copy()
        if continuation_token:
            params['continuation-token'] = continuation_token

        response = requests.get(BUCKET_URL, params=params)
        response.raise_for_status()
        xml_root = ET.fromstring(response.text)

        for content in xml_root.findall('.//s3:Contents', NAMESPACE):
            key = content.find('s3:Key', NAMESPACE).text
            keys.append(key)

        next_token = xml_root.find('.//s3:NextContinuationToken', NAMESPACE)
        if next_token is not None:
            continuation_token = next_token.text
        else:
            break

    print(f"✅ Found {len(keys)} files.")
    return keys

# --- Download, decompress, and save a single file ---
def download_and_save(key):
    match = re.match(r"(game-changers|vct-international|vct-challengers)/games/(\d{4})/val:([a-f0-9\-]+)\.json\.gz", key)
    if not match:
        return  # skip irrelevant keys

    category, year, game_id = match.groups()
    out_dir = os.path.join(DOWNLOAD_DIR, category, year)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{game_id}.json")

    # ✅ Skip if the file already exists
    if os.path.exists(out_path):
        return

    file_url = BUCKET_URL + key
    try:
        response = requests.get(file_url)
        response.raise_for_status()

        with gzip.open(io.BytesIO(response.content), 'rb') as f_in:
            json_data = f_in.read()

        with open(out_path, "wb") as f_out:
            f_out.write(json_data)
    except Exception as e:
        tqdm.write(f"❌ Error processing {key}: {e}")


# --- Main Workflow ---
if __name__ == "__main__":
    all_keys = get_all_keys()

    # Filter only relevant .json.gz files
    game_keys = [
        key for key in all_keys
        if re.match(r"(vct-international|game-changers|vct-challengers)/games/\d{4}/val:[a-f0-9\-]+\.json\.gz", key)
    ]

    print(f"⬇️ Downloading and saving {len(game_keys)} game files with parallel processing...\n")

    max_workers = min(32, os.cpu_count() * 4)  # Tune this based on your system

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_and_save, key): key for key in game_keys}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing", unit="file"):
            pass  # download_and_save already handles errors


    print("\n✅ All files downloaded and saved.")
