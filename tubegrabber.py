#!/usr/bin/env python3
"""
TubeGrabber
===========
A simple, friendly command-line YouTube downloader built on top of yt-dlp.

Features
--------
- Download single videos or entire playlists
- Choose video quality, or extract audio only (mp3)
- Download subtitles (if available)
- Clean progress bar in the terminal
- Saves everything into an organized `downloads/` folder by default

Usage
-----
    python tubegrabber.py <url> [options]

Examples
--------
    # Download best quality video
    python tubegrabber.py "https://youtube.com/watch?v=XXXX"

    # Download audio only, as mp3
    python tubegrabber.py "https://youtube.com/watch?v=XXXX" --audio-only

    # Download a whole playlist at 720p
    python tubegrabber.py "https://youtube.com/playlist?list=XXXX" --quality 720p

    # Download with subtitles, save to a custom folder
    python tubegrabber.py "https://youtube.com/watch?v=XXXX" --subs -o my_videos

IMPORTANT
---------
Only download content you own, that is in the public domain, or that you have
the rights/permission to download (e.g. Creative Commons videos, your own
uploads). Downloading copyrighted material without permission may violate
YouTube's Terms of Service and copyright law in your country.
"""

import argparse
import os
import sys

try:
    import yt_dlp
except ImportError:
    print("Missing dependency 'yt-dlp'. Install it first:\n")
    print("    pip install -r requirements.txt\n")
    sys.exit(1)


QUALITY_MAP = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
    "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]",
    "worst": "worst",
}


class ProgressBar:
    """Minimal terminal progress bar hooked into yt-dlp."""

    def __call__(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            filename = os.path.basename(d.get("filename", ""))

            if total:
                pct = downloaded / total * 100
                bar_len = 30
                filled = int(bar_len * pct / 100)
                bar = "#" * filled + "-" * (bar_len - filled)
                sys.stdout.write(
                    f"\r[{bar}] {pct:5.1f}%  {filename[:35]:<35}  {speed}  ETA {eta}   "
                )
            else:
                sys.stdout.write(f"\rDownloading {filename}...   ")
            sys.stdout.flush()

        elif d["status"] == "finished":
            sys.stdout.write("\n")
            print(f"Done downloading, now post-processing: {os.path.basename(d.get('filename', ''))}")


def build_options(args):
    outtmpl = os.path.join(args.output, "%(title)s [%(id)s].%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "noplaylist": not args.playlist,
        "progress_hooks": [ProgressBar()],
        "quiet": True,
        "no_warnings": True,
        "continuedl": True,
    }

    if args.audio_only:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        ydl_opts["format"] = QUALITY_MAP.get(args.quality, QUALITY_MAP["best"])
        ydl_opts["merge_output_format"] = "mp4"

    if args.subs:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = [args.sub_lang]
        ydl_opts["embedsubtitles"] = not args.audio_only

    return ydl_opts


def main():
    parser = argparse.ArgumentParser(
        prog="tubegrabber",
        description="Download YouTube videos or audio from the command line.",
    )
    parser.add_argument(
        "urls", nargs="*",
        help="One or more YouTube video/playlist URLs (space-separated)",
    )
    parser.add_argument(
        "-f", "--file",
        help="Path to a text file with one URL per line",
    )
    parser.add_argument(
        "-o", "--output", default="downloads",
        help="Output folder (default: ./downloads)",
    )
    parser.add_argument(
        "-q", "--quality", default="best", choices=list(QUALITY_MAP.keys()),
        help="Video quality (default: best)",
    )
    parser.add_argument(
        "--audio-only", action="store_true",
        help="Extract audio only and save as mp3",
    )
    parser.add_argument(
        "--playlist", action="store_true",
        help="Download the full playlist if the URL is part of one",
    )
    parser.add_argument(
        "--subs", action="store_true",
        help="Download subtitles if available",
    )
    parser.add_argument(
        "--sub-lang", default="en",
        help="Subtitle language code (default: en)",
    )

    args = parser.parse_args()

    urls = list(args.urls)
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                urls.extend(line.strip() for line in f if line.strip())
        except OSError as e:
            print(f"Could not read --file {args.file}: {e}")
            sys.exit(1)

    # de-duplicate while preserving order
    seen = set()
    urls = [u for u in urls if not (u in seen or seen.add(u))]

    if not urls:
        parser.error("Provide at least one URL (as an argument or via --file).")

    os.makedirs(args.output, exist_ok=True)
    ydl_opts = build_options(args)

    print(f"TubeGrabber starting...")
    print(f"Queued: {len(urls)} link{'s' if len(urls) != 1 else ''}")
    print(f"Mode: {'audio (mp3)' if args.audio_only else f'video ({args.quality})'}")
    print(f"Output: {os.path.abspath(args.output)}\n")

    failed = []
    for i, url in enumerate(urls, start=1):
        if len(urls) > 1:
            print(f"\n[{i}/{len(urls)}] {url}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            print(f"\nDownload failed for {url}: {e}")
            failed.append(url)
        except KeyboardInterrupt:
            print("\nCancelled by user.")
            sys.exit(1)

    if failed:
        print(f"\nDone with {len(failed)} failure(s):")
        for u in failed:
            print(f"  - {u}")
        sys.exit(1)

    print("\nAll done! Check your downloads folder.")


if __name__ == "__main__":
    main()
