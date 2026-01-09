import os
import datetime
import requests
import subprocess
import shutil
from bs4 import BeautifulSoup
import yt_dlp

# --- Configuration ---
BASE_URL = "https://www.newgrounds.com/audio"
# Creates a folder like ~/ng/0108 for Jan 8th
TODAY_STR = datetime.datetime.now().strftime("%m%d")
SAVE_DIR = os.path.expanduser(f"~/music/newbeach/{TODAY_STR}")

def get_recent_urls(limit=10):
    """Scrapes the main audio page for the most recent submission links."""
    print(f"[1/4] Fetching recent tracks from {BASE_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        r = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        links = []
        for a in soup.find_all('a', href=True):
            if '/audio/listen/' in a['href']:
                full_link = a['href']
                if full_link not in links:
                    links.append(full_link)
                    if len(links) >= limit:
                        break
        return links
    except Exception as e:
        print(f"Error scraping Newgrounds: {e}")
        return []

def download_tracks(urls, target_dir):
    """Downloads tracks using yt-dlp to the target directory."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print(f"[2/4] Downloading {len(urls)} songs to {target_dir}...")

    # We use playlist_index to ensure filenames match our URL list order
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{target_dir}/%(playlist_index)s - %(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

def create_metadata_files(target_dir, urls):
    """
    1. Creates playlist.m3u for the player.
    2. Creates tracks.txt mapping filenames to URLs.
    """
    print("[3/4] Generating playlist and track records...")

    # Sort files by the numeric index prefix (e.g., '1 - Song.mp3')
    # This ensures they match the order of the 'urls' list.
    files = [f for f in os.listdir(target_dir) if f.endswith('.mp3')]

    # Helper to extract the leading number for sorting
    def get_index(filename):
        try:
            return int(filename.split(' - ')[0])
        except ValueError:
            return 999

    files.sort(key=get_index)

    playlist_path = os.path.join(target_dir, "playlist.m3u")
    tracks_txt_path = os.path.join(target_dir, "tracks.txt")

    # Write the playlist for mpv
    with open(playlist_path, "w") as f_play:
        for file in files:
            f_play.write(file + "\n")

    # Write the text file for the user
    with open(tracks_txt_path, "w") as f_txt:
        for i, file in enumerate(files):
            # Map file to URL based on index
            url = urls[i] if i < len(urls) else "Unknown URL"
            f_txt.write(f"File: {file}\n")
            f_txt.write(f"Link: {url}\n")
            f_txt.write("-" * 40 + "\n")

    return playlist_path, tracks_txt_path

def main():
    # 1. Get URLs
    urls = get_recent_urls(10)

    if not urls:
        print("No songs found.")
        return

    # 2. Download
    download_tracks(urls, SAVE_DIR)

    # 3. Generate Files
    playlist, tracks_txt = create_metadata_files(SAVE_DIR, urls)

    print("\n" + "="*60)
    print(f"READY. Saved to: {SAVE_DIR}")
    print(f"URL List saved to: {tracks_txt}")
    print("="*60)

    # 4. Play
    if shutil.which("mpv"):
        print("Launching MPV... (Press 'Enter' to skip, 'q' to quit)")
        subprocess.run(["mpv", "--playlist=" + playlist], cwd=SAVE_DIR)
    else:
        print("Error: 'mpv' is not installed.")

if __name__ == "__main__":
    main()