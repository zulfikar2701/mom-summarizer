#!/usr/bin/env python3
"""
Push a local .mp3 to the EC2 service and wait for processing.
Usage:
    python send_recording.py path/to/meeting.mp3
Environment variables (or edit the constants below):
    API_URL  –  complete base, e.g. 'https://api.example.com/api/v1/recordings'
    API_KEY  –  matches X-API-Key header expected by the server (optional)
"""
import os
import sys
import time
import pathlib

import requests

API_ROOT = os.getenv("API_URL", "http://13.251.26.7:8000/api/v1/recordings")
API_KEY = os.getenv("API_KEY", "supersecret")

def upload(mp3: pathlib.Path) -> int:
    r = requests.post(
        API_ROOT,
        headers={"X-API-Key": API_KEY} if API_KEY else {},
        files={"file": mp3.open("rb")},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["id"]

def wait_until_done(rid: int, delay=5):
    while True:
        data = requests.get(f"{API_ROOT}/{rid}", timeout=30).json()
        if data["summary"]:       # finished
            print("\n=== SUMMARY ===")
            print(data["summary"])
            break
        print("processing…", end="\r")
        time.sleep(delay)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: send_recording.py file.mp3")
    mp3_path = pathlib.Path(sys.argv[1])
    if not mp3_path.is_file():
        sys.exit("File not found")
    rec_id = upload(mp3_path)
    print("Uploaded. Record ID =", rec_id)
    wait_until_done(rec_id)
