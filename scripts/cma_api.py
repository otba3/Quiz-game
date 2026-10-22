"""Shared helper for talking to the CMA Open Access API, with a local cache.

Other scripts use it like this:
    from cma_api import fetch_artwork
    artwork = fetch_artwork("157218")
"""
import json
import time
import urllib.request
from pathlib import Path

API_URL = "https://openaccess-api.clevelandart.org/api/artworks/{}"
CACHE_DIR = Path("data/cache")
DELAY_SECONDS = 1  # pause after each real API call, to be polite to the server


def download_file(url):
    """Download any URL (e.g. an image) and return its raw bytes. Pauses after."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "museum-quiz-pipeline/0.1"})
    with urllib.request.urlopen(request) as response:
        data = response.read()
    time.sleep(DELAY_SECONDS)
    return data


def fetch_artwork(artwork_id):
    """Return the full artwork record (a dict). Uses the cache when possible."""
    cache_file = CACHE_DIR / f"{artwork_id}.json"

    # 1. Already downloaded before? Read it from disk, no internet needed.
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    # 2. Otherwise ask the API (with our own User-Agent, see explore_artwork.py).
    request = urllib.request.Request(
        API_URL.format(artwork_id),
        headers={"User-Agent": "museum-quiz-pipeline/0.1"})
    with urllib.request.urlopen(request) as response:
        artwork = json.load(response)["data"]

    # 3. Save it so the next run doesn't need the API.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(artwork, indent=2, ensure_ascii=False),
                          encoding="utf-8")
    time.sleep(DELAY_SECONDS)
    return artwork
