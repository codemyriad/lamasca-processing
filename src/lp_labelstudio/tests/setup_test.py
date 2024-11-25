#!/usr/bin/env python
from pathlib import Path
import requests


TEST_FILES_ROOT = Path("/tmp/lamasca-tests")
BASEURL = "https://newspapers.codemyriad.io/lamasca-pages/"

PAGES = [
    "1994/lamasca-1994-02-16/page_01.jpeg",
    "1994/lamasca-1994-02-16/page_02.jpeg",
    "1994/lamasca-1994-02-16/page_03.jpeg",
]

MANIFESTS = ["1994/lamasca-1994-02-16/manifest.json"]


def prepare():
    # Download the pages needed for the test
    # from https://newspapers.codemyriad.io/lamasca-pages/
    # to /tmp/lamasca-tests
    for filepath in PAGES + MANIFESTS:
        fullpath = TEST_FILES_ROOT / filepath
        if not fullpath.exists():
            print(f"Downloading {fullpath}")
            url = BASEURL + filepath
            response = requests.get(url)
            # Create parent directory if it doesn't exist
            fullpath.parent.mkdir(parents=True, exist_ok=True)
            # Save the file
            if response.status_code == 200:
                fullpath.write_bytes(response.content)
            else:
                print(f"Failed to download {url}: {response.status_code}")


if __name__ == "__main__":
    prepare()
