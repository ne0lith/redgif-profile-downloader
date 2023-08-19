# Redgif Downloader

The Redgif Downloader is a Python script that allows you to download videos from a specific Redgifs user's profile. This script utilizes asynchronous programming to efficiently retrieve and download videos from Redgifs, making use of the Redgifs API.

## Features

- Downloads videos from a specified Redgifs user's profile.
- Utilizes asynchronous programming to maximize efficiency and speed.
- Supports concurrent downloads to speed up the process.
- Skips videos that have already been downloaded to avoid duplicates.

## Prerequisites

- Python 3.7 or higher is required.
- Install required dependencies using the following command:
`pip install httpx`

## Usage

1. Clone the repository or download the script directly.
2. Open a terminal or command prompt and navigate to the directory containing the script.
3. Run the script using the following command:
`python redgif_downloader.py [--username USERNAME] [--concurrency CONCURRENCY] [--skip-history] [--batch BATCH]`

- Replace `USERNAME` with the Redgifs username you want to scrape. If you don't provide the `--username` argument, the script will prompt you to enter the username.
- You can use the optional `--concurrency` argument to specify the maximum number of concurrent downloads. If not provided, the default value of 5 will be used.
- Use the `--skip-history` flag to download files even if they are in the history.
- Use the `--batch` argument to provide a path to a file containing a list of usernames or a comma-separated list of usernames.

4. The script will start fetching and downloading videos from the specified user's profile. The videos will be saved in a folder named `Redgif Files - USERNAME`, where `USERNAME` is the provided Redgifs username.
5. Once the script finishes, it will display the total number of downloads, downloaded videos, and skipped videos.

## Contributing

If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## Acknowledgments

This script is inspired by the [CyberDropDownloader](https://github.com/Jules-WinnfieldX/CyberDropDownloader/) project. The API logic was directly copied from their [RedGifs Spider](https://github.com/Jules-WinnfieldX/CyberDropDownloader/blob/master/cyberdrop_dl/crawlers/RedGifs_Spider.py).

## Disclaimer

This script is meant for educational and personal use only. Please respect Redgifs' terms of use and the rights of content creators when using this script.

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
