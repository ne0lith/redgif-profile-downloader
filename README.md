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
`python redgif_downloader.py [--username USERNAME] [--concurrency CONCURRENCY]`

Replace `USERNAME` with the Redgifs username you want to scrape. If you don't provide the `--username` argument, the script will prompt you to enter the username. You can also use the optional `--concurrency` argument to specify the maximum number of concurrent downloads. If not provided, the default value of 5 will be used.
5. The script will start fetching and downloading videos from the specified user's profile. The videos will be saved in a folder named `Redgif Files - USERNAME`, where `USERNAME` is the provided Redgifs username.
6. Once the script finishes, it will display the total number of downloads, downloaded videos, and skipped videos.

## Contributing

If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## Acknowledgments

This script is inspired by the [CyberDropDownloader](https://github.com/Jules-WinnfieldX/CyberDropDownloader/) project.

## Disclaimer

This script is meant for educational and personal use only. Please respect Redgifs' terms of use and the rights of content creators when using this script.

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
