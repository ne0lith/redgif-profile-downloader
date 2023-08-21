import os
import httpx
import asyncio
import sqlite3
import argparse
from urllib.parse import urlparse, unquote
from pathlib import Path

# Some logic/code was taken from this project: https://github.com/Jules-WinnfieldX/CyberDropDownloader/
# Specifically this spider: https://github.com/Jules-WinnfieldX/CyberDropDownloader/blob/master/cyberdrop_dl/crawlers/RedGifs_Spider.py

os.chdir(Path(__file__).resolve().parent)

CONFIG = {
    "max_concurrent_downloads": 3,
    "root_path": "",
    "database_path": "redgif_history.sqlite",
}

history_to_insert = []


class DatabaseManager:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def __enter__(self):
        self.conn = sqlite3.connect(self.database_path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.commit()
        self.conn.close()


def initialize_database():
    with DatabaseManager(CONFIG["database_path"]) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                username TEXT,
                video_name TEXT,
                PRIMARY KEY (username, video_name)
            )
        """
        )


def check_download_in_db(username, video_name):
    with DatabaseManager(CONFIG["database_path"]) as cursor:
        cursor.execute(
            "SELECT * FROM downloads WHERE username = ? AND video_name = ?",
            (username, video_name),
        )
        result = cursor.fetchone()
    return result is not None


async def download_video(session, url, folder_path, semaphore, username):
    async with semaphore:
        async with session.stream("GET", url) as response:
            if response.status_code == 200:
                video_data = await response.aread()
                video_name = unquote(urlparse(url).path.split("/")[-1].split("?")[0])

                if CONFIG.get("root_path"):
                    root_path = Path(CONFIG["root_path"])
                    video_path = root_path / folder_path / video_name
                else:
                    video_path = Path(folder_path) / video_name

                if not video_path.parent.exists():
                    video_path.parent.mkdir(parents=True)

                is_skipped = False

                if not video_path.exists():
                    if (
                        not check_download_in_db(username, video_name)
                        or args.skip_history
                    ):
                        with video_path.open("wb") as video_file:
                            video_file.write(video_data)
                        print(f"Downloaded {video_name}")

                        history_to_insert.append((username, video_name))
                    else:
                        print(f"Skipping {video_name} (already downloaded)")
                        is_skipped = True
                        # this condition probably never happens
                else:
                    if not check_download_in_db(username, video_name):
                        print(f"Skipping {video_name} (already downloaded)")
                        is_skipped = True
                        # this condition probably never happens
                    else:
                        print(f"Skipping {video_name} (already downloaded)")
                        is_skipped = True

                if is_skipped:
                    history_to_insert.append((username, video_name))
                    return 0, 1
                else:
                    return 1, 0
            else:
                print(f"Failed to download {url}")
                return 0, 1


async def main(username):
    redgifs_api = "https://api.redgifs.com/"
    print(f"Scraping https://www.redgifs.com/users/{username}\n")

    download_folder = Path(f"Redgif Files - {username}")

    async with httpx.AsyncClient() as session:
        token_response = await session.get(redgifs_api + "v2/auth/temporary")
        token = token_response.json()["token"]
        start_page = 1

        headers = {"Authorization": f"Bearer {token}"}

        search_url = redgifs_api + f"v2/users/{username}/search?page={start_page}"
        json_response = await session.get(search_url, headers=headers)
        json_obj = json_response.json()

        total_pages = json_obj["pages"]

        hd_sd_values = []

        skipped_count = 0

        for page in range(start_page, total_pages + 1):
            search_url = redgifs_api + f"v2/users/{username}/search?page={page}"
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
                if hd_value or sd_value:
                    video_name = unquote(
                        urlparse(hd_value or sd_value).path.split("/")[-1].split("?")[0]
                    )
                    if (
                        not check_download_in_db(username, video_name)
                        or args.skip_history
                    ):
                        hd_sd_values.append(hd_value or sd_value)
                    else:
                        print(f"Skipping {video_name} (already in database)")
                        skipped_count += 1

        semaphore = asyncio.Semaphore(CONFIG["max_concurrent_downloads"])
        downloaded_count = 0

        tasks = []
        for value in hd_sd_values:
            tasks.append(
                download_video(session, value, download_folder, semaphore, username)
            )

        results = await asyncio.gather(*tasks)

    for downloaded, skipped in results:
        downloaded_count += downloaded
        skipped_count += skipped

    total_downloads = downloaded_count + skipped_count

    with DatabaseManager(CONFIG["database_path"]) as cursor:
        cursor.executemany(
            "INSERT OR IGNORE INTO downloads (username, video_name) VALUES (?, ?)",
            history_to_insert,
        )

    print(f"\nTotal downloads: {total_downloads}")
    print(f"Downloaded: {downloaded_count}")
    print(f"Skipped: {skipped_count}\n")


if __name__ == "__main__":
    os.system("clear" if os.name == "posix" else "cls")
    initialize_database()

    parser = argparse.ArgumentParser()
    parser.add_argument("--username", "-u", help="Username or profile link to scrape")
    parser.add_argument(
        "--concurrency",
        type=int,
        help="Maximum number of concurrent downloads",
    )
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Download files even if they are in the history",
    )
    parser.add_argument(
        "--batch",
        help="Path to a file containing a list of usernames, or a comma-separated list of usernames",
    )
    parser.add_argument(
        "--root-path",
        help="Root path for downloaded files",
    )
    parser.add_argument(
        "--database-path",
        help="Path for the database",
    )
    args = parser.parse_args()

    if args.concurrency is not None:
        CONFIG["max_concurrent_downloads"] = args.concurrency

    if args.root_path is not None:
        CONFIG["root_path"] = args.root_path

    if args.database_path is not None:
        CONFIG["database_path"] = args.database_path

    if args.batch:
        usernames = []

        if Path(args.batch).is_file():
            with open(args.batch, "r") as batch_file:
                for line in batch_file:
                    if not line.startswith("#"):
                        usernames.append(line.strip())
        else:
            usernames = args.batch.split(",")

        for username in usernames:
            asyncio.run(main(username))

    else:
        username = args.username or input(
            "Enter the username or profile link to scrape: "
        )

        asyncio.run(main(username))
