from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen


BASE_URL = "https://divvy-tripdata.s3.amazonaws.com"
MONTHS = [
    "202503",
    "202504",
    "202505",
    "202506",
    "202507",
    "202508",
    "202509",
    "202510",
    "202511",
    "202512",
    "202601",
    "202602",
]
DEST_DIR = Path("data/raw")
CHUNK_SIZE = 1024 * 1024


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(url) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            output.write(chunk)


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    for month in MONTHS:
        filename = f"{month}-divvy-tripdata.zip"
        destination = DEST_DIR / filename

        if destination.exists() and destination.stat().st_size > 0:
            print(f"skip {filename}")
            continue

        url = f"{BASE_URL}/{filename}"
        print(f"download {url}")
        download_file(url, destination)


if __name__ == "__main__":
    main()
