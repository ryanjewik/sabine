import requests, json, gzip, shutil, os
from io import BytesIO
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurable
S3_BUCKET_URL = "https://vcthackathon-data.s3.us-west-2.amazonaws.com"
MAX_THREADS = 10  # You can tweak this depending on your network/CPU


def download_gzip_and_write_to_json(file_name):  # this just downloads the S3 file and writes it to a local json file
    local_filename = f"{file_name}.json"
    if os.path.exists(local_filename):
        return True

    url = f"{S3_BUCKET_URL}/{file_name}.json.gz"
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            gzip_bytes = BytesIO(response.content)
            with gzip.GzipFile(fileobj=gzip_bytes, mode="rb") as gzipped_file:
                with open(local_filename, 'wb') as output_file:
                    shutil.copyfileobj(gzipped_file, output_file)
            return True
        return False
    except Exception as e:
        print(f"Download failed: {file_name} ({e})")
        return False
    
def download_esports_files(league):
    directory = f"{league}/esports-data"

    if not os.path.exists(directory):
        os.makedirs(directory)

    esports_data_files = ["leagues", "tournaments",
                          "players", "teams", "mapping_data"]
    for file_name in esports_data_files:
        download_gzip_and_write_to_json(f"{directory}/{file_name}")
    

def download_games(league, year):
    mapping_file = f"{league}/esports-data/mapping_data.json"
    game_dir = f"{league}/games/{year}"
    os.makedirs(game_dir, exist_ok=True)

    with open(mapping_file, "r") as f:
        mappings_data = json.load(f)

    # Build download task list
    download_list = []
    for game in mappings_data:
        game_id = game.get("platformGameId")
        if game_id:
            download_list.append(f"{league}/games/{year}/{game_id}")

    print(f"Downloading {len(download_list)} game files for {league} {year}...")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(download_gzip_and_write_to_json, file): file for file in download_list}
        for _ in tqdm(as_completed(futures), total=len(futures), desc=f"Game Downloads {league} {year}"):
            pass
    print(f"All game files downloaded successfully for {league} {year}.")
    

if __name__ == "__main__":
    leagues = ["vct-international", "vct-challengers", "game-changers"]
    years = [2022, 2023, 2024]
    for league in leagues:
        download_esports_files(league)
        for year in years:
            download_games(league, year)