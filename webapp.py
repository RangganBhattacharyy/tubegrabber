#!/usr/bin/env python3
"""
TubeGrabber Web UI
==================
A tiny local Flask app that wraps tubegrabber.py in a simple browser form.

Run:
    python webapp.py

Then open http://127.0.0.1:5000 in your browser.

This starts downloads in a background thread and shows live status so the
page doesn't hang while a video is downloading. Downloaded files are saved
to the `downloads/` folder next to this script.
"""

import os
import threading
import uuid

from flask import Flask, render_template, request, jsonify, send_from_directory

import yt_dlp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Optional: place a cookies.txt (Netscape format) file next to this script
# to let yt-dlp download Instagram/Facebook content that requires login.
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

# In-memory job tracker: {job_id: {"status": ..., "progress": ..., "filename": ...}}
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


def find_direct_media_url(page_url):
    """Fallback for sites yt-dlp doesn't recognize: fetch the page like a
    real browser would and look for an <audio>/<video> tag, a <source>
    tag, or an og:audio/og:video meta tag pointing at a playable file.
    Returns (media_url, suggested_title) or (None, None) if nothing found.
    """
    resp = requests.get(page_url, headers=BROWSER_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "download"

    candidates = []

    for tag in soup.find_all(["audio", "video"]):
        src = tag.get("src")
        if src:
            candidates.append(src)
        for source in tag.find_all("source"):
            if source.get("src"):
                candidates.append(source["src"])

    for meta_name in ("og:audio", "og:audio:url", "og:video", "og:video:url", "og:video:secure_url"):
        tag = soup.find("meta", property=meta_name)
        if tag and tag.get("content"):
            candidates.append(tag["content"])

    for c in candidates:
        if c and any(c.lower().split("?")[0].endswith(ext) for ext in (".mp3", ".m4a", ".wav", ".mp4", ".webm")):
            return urljoin(page_url, c), title

    return None, None


def download_direct_file(media_url, title, job_id, audio_only):
    """Stream a direct media URL to disk, updating job progress as it goes."""
    ext = media_url.split("?")[0].rsplit(".", 1)[-1].lower()
    if ext not in ("mp3", "m4a", "wav", "mp4", "webm"):
        ext = "mp3" if audio_only else "mp4"

    safe_title = "".join(c for c in title if c not in '\\/:*?"<>|').strip()[:120] or "download"
    dest = os.path.join(DOWNLOAD_DIR, f"{safe_title}.{ext}")

    job = JOBS[job_id]
    job["filename"] = os.path.basename(dest)
    job["status"] = "downloading"

    with requests.get(media_url, headers=BROWSER_HEADERS, stream=True, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    job["file_progress"] = round(downloaded / total * 100, 1)

    job["file_progress"] = 100
    return dest


def make_hook(job_id):
    """Per-file progress hook. Updates the current file's own progress plus
    the job's overall progress across all queued URLs."""
    def hook(d):
        job = JOBS[job_id]
        total_urls = job["total"]
        done_urls = job["current_index"]  # how many URLs fully finished so far

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            file_pct = (downloaded / total * 100) if total else 0

            job["status"] = "downloading"
            job["filename"] = os.path.basename(d.get("filename", ""))
            job["file_progress"] = round(file_pct, 1)
            # overall progress = fully finished urls + fraction of current one
            job["progress"] = round((done_urls + file_pct / 100) / total_urls * 100, 1)

        elif d["status"] == "finished":
            job["status"] = "processing"
            job["file_progress"] = 100

    return hook


def run_download(job_id, urls, quality, audio_only, playlist):
    job = JOBS[job_id]
    job["total"] = len(urls)
    job["current_index"] = 0
    job["progress"] = 0
    job["file_progress"] = 0
    job["completed"] = []
    job["failed"] = []

    outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s [%(id)s].%(ext)s")
    base_opts = {
        "outtmpl": outtmpl,
        "noplaylist": not playlist,
        "progress_hooks": [make_hook(job_id)],
        "quiet": True,
        "no_warnings": True,
        # Instagram often needs a logged-in session even for content that
        # looks public in a browser -- without cookies, yt-dlp gets
        # rate-limited or blocked. If a cookies.txt file (Netscape format,
        # exported from a browser extension) exists next to this script,
        # use it automatically.
        **({"cookiefile": COOKIES_FILE} if os.path.exists(COOKIES_FILE) else {}),
        # NOTE: ignoreerrors is intentionally left off here. When it's on,
        # yt-dlp swallows per-video failures and the job can end up marked
        # "done" even though nothing was actually downloaded (e.g. an
        # unsupported site, a private video, a dead link). Each URL below
        # is downloaded in its own try/except instead, so real failures
        # are captured and shown to the user.
    }

    if audio_only:
        base_opts["format"] = "bestaudio/best"
        base_opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    else:
        base_opts["format"] = QUALITY_MAP.get(quality, QUALITY_MAP["best"])
        base_opts["merge_output_format"] = "mp4"

    for i, url in enumerate(urls):
        job["current_index"] = i
        job["current_url"] = url
        job["file_progress"] = 0
        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                ydl.download([url])
            job["completed"].append(url)
        except Exception as yt_error:
            # Sites yt-dlp *does* recognize (youtube.com, instagram.com,
            # facebook.com) should never fall through to the generic
            # HTML-scrape fallback below -- that fallback only works on
            # plain pages with a raw <video>/<audio> tag, and Instagram
            # renders everything with JavaScript, so it will never find
            # anything there. Falling through just hides the real error.
            known_site = any(
                d in url for d in ("youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch")
            )

            if known_site:
                job["failed"].append({"url": url, "error": str(yt_error)})
            else:
                # Unknown/generic site (e.g. a podcast page like Aaro
                # Ananda): try a plain-HTML fallback -- fetch the page like
                # a browser and look for a direct audio/video file.
                try:
                    media_url, title = find_direct_media_url(url)
                    if media_url:
                        download_direct_file(media_url, title, job_id, audio_only)
                        job["completed"].append(url)
                    else:
                        raise RuntimeError(
                            "yt-dlp doesn't support this site and no direct "
                            "audio/video file could be found on the page."
                        )
                except Exception as fallback_error:
                    job["failed"].append({
                        "url": url,
                        "error": f"{yt_error}\n(fallback also failed: {fallback_error})",
                    })

        # mark this url as done for overall progress purposes
        job["current_index"] = i + 1
        job["progress"] = round((i + 1) / job["total"] * 100, 1)

    if job["failed"] and not job["completed"]:
        job["status"] = "error"
        first_reason = job["failed"][0]["error"]
        # Prefer showing why the fallback failed, since that's the more
        # specific/actionable reason when yt-dlp doesn't support the site.
        if "(fallback also failed:" in first_reason:
            fallback_part = first_reason.split("(fallback also failed:", 1)[1].rstrip(")")
            short_reason = fallback_part.strip()[:200]
        else:
            short_reason = first_reason.split("\n")[0][:300]
        job["error"] = f"Could not download: {short_reason}"
    else:
        job["status"] = "done"
        job["progress"] = 100


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(force=True)

    # Accept either a single "url" field or a multi-line "urls" field.
    # Splitting on newlines/commas/whitespace lets people paste a whole
    # block of links copied from a chat or a notes app.
    raw = data.get("urls")
    if raw is None:
        raw = data.get("url") or ""

    if isinstance(raw, list):
        candidates = raw
    else:
        # split on newlines and commas
        candidates = []
        for line in str(raw).splitlines():
            candidates.extend(line.split(","))

    urls = [u.strip() for u in candidates if u.strip()]
    # de-duplicate while keeping order
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
        "file_progress": 0,
        "filename": "",
        "total": len(urls),
        "current_index": 0,
    }

    thread = threading.Thread(
        target=run_download, args=(job_id, urls, quality, audio_only, playlist), daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id, "count": len(urls)})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "unknown job"}), 404
    return jsonify(job)


@app.route("/downloads/<path:filename>")
def get_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


@app.route("/api/files")
def list_files():
    files = sorted(os.listdir(DOWNLOAD_DIR))
    return jsonify(files)


if __name__ == "__main__":
    app.run(debug=True, port=5000)