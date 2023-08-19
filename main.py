import os
import httpx
import asyncio
import sqlite3
import argparse
from urllib.parse import urlparse, unquote
from pathlib import Path

# Some logic/code was taken from this project: https://github.com/Jules-WinnfieldX/CyberDropDownloader/
# Specifically this spider: https://github.com/Jules-WinnfieldX/CyberDropDownloader/blob/master/cyberdrop_dl/crawlers/RedGifs_Spider.py

os.chdir(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {
    "max_concurrent_downloads": 5,
    "root_path": "",  # if this is empty, it will store downloads in a subfolder of the path this script is in
}


def configure():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", "-u", help="Username or profile link to scrape")
    parser.add_argument(
        "--concurrency",
        type=int,
        help="Maximum number of concurrent downloads",
    )
    args = parser.parse_args()

    user_input = args.username or input(
        "Enter the username or profile link to scrape: "
    )

    parsed_url = urlparse(user_input)
    if parsed_url.netloc == "www.redgifs.com" and parsed_url.path.startswith("/users/"):
        user_id = parsed_url.path.split("/")[-1]
    else:
        user_id = user_input

    if args.concurrency is not None:
        CONFIG["max_concurrent_downloads"] = args.concurrency

    return user_id


def initialize_database():
    conn = sqlite3.connect("history.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS downloads (
            username TEXT,
            video_name TEXT,
            PRIMARY KEY (username, video_name)
        )
    """
    )
    conn.commit()
    conn.close()


async def download_video(
    session, url, folder_path, semaphore, downloaded_count, skipped_count, username
):
    async with semaphore:
        async with session.stream("GET", url) as response:
            if response.status_code == 200:
                video_data = await response.aread()
                parsed_url = urlparse(url)
                video_name = unquote(parsed_url.path.split("/")[-1].split("?")[0])

                if CONFIG.get("root_path"):
                    root_path = Path(CONFIG["root_path"])
                    video_path = root_path / folder_path / video_name
                else:
                    video_path = Path(folder_path) / video_name

                if not video_path.parent.exists():
                    video_path.parent.mkdir(parents=True)

                if not video_path.exists() and not check_download_in_db(
                    username, video_name
                ):
                    with video_path.open("wb") as video_file:
                        video_file.write(video_data)
                    print(f"Downloaded {video_name}")
                    downloaded_count += 1
                    insert_download_into_db(username, video_name)
                else:
                    print(f"Skipping {video_name}")
                    skipped_count += 1
                    insert_download_into_db(username, video_name)
            else:
                print(f"Failed to download {url}")

    return downloaded_count, skipped_count


def check_download_in_db(username, video_name):
    conn = sqlite3.connect("history.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM downloads WHERE username = ? AND video_name = ?",
        (username, video_name),
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def insert_download_into_db(username, video_name):
    conn = sqlite3.connect("history.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO downloads (username, video_name) VALUES (?, ?)",
        (username, video_name),
    )
    conn.commit()
    conn.close()


async def main():
    os.system("clear" if os.name == "posix" else "cls")
    initialize_database()

    redgifs_api = "https://api.redgifs.com/"
    user_id = configure()
    print(f"Scraping https://www.redgifs.com/users/{user_id}\n")

    download_folder = Path(f"Redgif Files - {user_id}")

    async with httpx.AsyncClient() as session:
        token_response = await session.get(redgifs_api + "v2/auth/temporary")
        token = token_response.json()["token"]
        start_page = 1

        headers = {"Authorization": f"Bearer {token}"}

        search_url = redgifs_api + f"v2/users/{user_id}/search?page={start_page}"
        json_response = await session.get(search_url, headers=headers)
        json_obj = json_response.json()

        total_pages = json_obj["pages"]

        hd_sd_values = []

        for page in range(start_page, total_pages + 1):
            search_url = redgifs_api + f"v2/users/{user_id}/search?page={page}"
            json_response = await session.get(search_url, headers=headers)

            if json_response.status_code == 404:
                print(f"Page {page} doesn't exist. Stopping crawling.")
                break

            json_obj = json_response.json()

            gifs = json_obj["gifs"]
            for gif in gifs:
                links = gif.get("urls", {})
                hd_value = links.get("hd")
                sd_value = links.get("sd")
                if hd_value:
                    hd_sd_values.append(hd_value)
                elif sd_value:
                    hd_sd_values.append(sd_value)

        semaphore = asyncio.Semaphore(CONFIG["max_concurrent_downloads"])
        downloaded_count = 0
        skipped_count = 0
        tasks = [
            download_video(
                session,
                value,
                download_folder,
                semaphore,
                downloaded_count,
                skipped_count,
                user_id,
            )
            for value in hd_sd_values
        ]
        results = await asyncio.gather(*tasks)

        for result in results:
            downloaded_count += result[0]
            skipped_count += result[1]

        total_downloads = downloaded_count + skipped_count

    print(f"\nTotal downloads: {total_downloads}")
    print(f"Downloaded: {downloaded_count}")
    print(f"Skipped: {skipped_count}\n")


asyncio.run(main())
