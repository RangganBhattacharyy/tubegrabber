#!/usr/bin/env python3
"""
TubeGrabber Web UI
==================
A tiny Flask app that wraps tubegrabber.py and extracts direct stream URLs via yt-dlp.
"""

import os
import threading
import uuid

from flask import Flask, render_template, request, jsonify
import yt_dlp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

JOBS = {}

QUALITY_MAP = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
}

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_direct_url(url, quality, audio_only, playlist):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": not playlist,
    }
    if audio_only:
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = QUALITY_MAP.get(quality, QUALITY_MAP["best"])

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info.get("url"), info.get("title", "download")

def run_extraction(job_id, urls, quality, audio_only, playlist):
    job = JOBS[job_id]
    job["total"] = len(urls)
    job["completed"] = []
    job["failed"] = []

    for i, url in enumerate(urls):
        job["current_index"] = i
        try:
            direct_url, title = get_direct_url(url, quality, audio_only, playlist)
            if direct_url:
                job["completed"].append({"url": url, "direct_url": direct_url, "title": title})
            else:
                job["failed"].append({"url": url, "error": "Could not extract link."})
        except Exception as e:
            job["failed"].append({"url": url, "error": str(e)})

    if job["completed"]:
        job["status"] = "done"
        job["filename"] = job["completed"][0]["title"]
        job["direct_url"] = job["completed"][0]["direct_url"]
    else:
        job["status"] = "error"
        job["error"] = job["failed"][0]["error"] if job["failed"] else "Extraction failed."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(force=True)
    raw = data.get("urls") or data.get("url") or ""
    
    if isinstance(raw, list):
        candidates = raw
    else:
        candidates = []
        for line in str(raw).splitlines():
            candidates.extend(line.split(","))

    urls = [u.strip() for u in candidates if u.strip()]
    seen = set()
    urls = [u for u in urls if not (u in seen or seen.add(u))]

    if not urls:
        return jsonify({"error": "At least one URL is required"}), 400

    quality = data.get("quality", "best")
    audio_only = bool(data.get("audio_only", False))
    playlist = bool(data.get("playlist", False))

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "starting",
        "progress": 0,
        "total": len(urls),
        "current_index": 0,
    }

    thread = threading.Thread(
        target=run_extraction, args=(job_id, urls, quality, audio_only, playlist), daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id, "count": len(urls)})

@app.route("/api/status/<job_id>")
def api_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "unknown job"}), 404
    return jsonify(job)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

    
