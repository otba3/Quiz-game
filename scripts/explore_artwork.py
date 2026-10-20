"""Fetch ONE artwork from the CMA Open Access API and show its main fields.

Usage:  py scripts/explore_artwork.py 157218
"""
import json
import sys
import urllib.request

artwork_id = sys.argv[1] if len(sys.argv) > 1 else "157218"
url = f"https://openaccess-api.clevelandart.org/api/artworks/{artwork_id}"

# The server rejects Python's default "Python-urllib" User-Agent (HTTP 403),
# so we identify ourselves politely instead.
request = urllib.request.Request(
    url, headers={"User-Agent": "museum-quiz-pipeline/0.1"})

with urllib.request.urlopen(request) as response:
    payload = json.load(response)  # turn the JSON text into Python dicts/lists

artwork = payload["data"]  # the API wraps the record in {"data": {...}}

print("All top-level fields:", sorted(artwork.keys()), "\n")

for field in ["id", "accession_number", "title", "creation_date",
              "culture", "technique", "share_license_status", "copyright"]:
    print(f"{field:22} = {artwork.get(field)!r}")

print("\ncreators:")
print(json.dumps(artwork.get("creators"), indent=2, ensure_ascii=False))

print("\nimages:")
print(json.dumps(artwork.get("images"), indent=2, ensure_ascii=False))
