import os
import httpx
import asyncio
import argparse
from urllib.parse import urlparse, unquote
from pathlib import Path

# Some logic/code was taken from this project: https://github.com/Jules-WinnfieldX/CyberDropDownloader/

CONFIG = {
    "max_concurrent_downloads": 5,
}


def configure():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", "-u", help="Username to scrape")
    parser.add_argument(
        "--concurrency",
        type=int,
        help="Maximum number of concurrent downloads",
    )
    args = parser.parse_args()

    user_id = args.username or input("Enter the username to scrape: ")
    if args.concurrency is not None:
        CONFIG["max_concurrent_downloads"] = args.concurrency

    return user_id


async def download_video(
    session, url, folder_path, semaphore, downloaded_count, skipped_count
):
    async with semaphore:
        async with session.stream("GET", url) as response:
            if response.status_code == 200:
                video_data = await response.aread()
                parsed_url = urlparse(url)
                video_name = unquote(parsed_url.path.split("/")[-1].split("?")[0])
                video_path = Path(folder_path) / video_name

                if not video_path.parent.exists():
                    video_path.parent.mkdir(parents=True)

                if not video_path.exists():
                    with video_path.open("wb") as video_file:
                        video_file.write(video_data)
                    print(f"Downloaded {video_name}")
                    downloaded_count += 1
                else:
                    print(f"Skipping {video_name}")
                    skipped_count += 1
            else:
                print(f"Failed to download {url}")

    return downloaded_count, skipped_count


async def main():
    os.system("clear" if os.name == "posix" else "cls")

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
