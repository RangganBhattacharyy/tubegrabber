# TubeGrabber

A simple YouTube downloader with two ways to use it:

1. **Command line** — `tubegrabber.py`
2. **Local web app** — `webapp.py` (a small Flask UI in your browser)

Built on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp), which does the actual
heavy lifting of talking to YouTube.

## ⚠️ Before you use it

Only download videos you own, that are in the public domain, or that you have
the rights or explicit permission to save (e.g. Creative Commons content, your
own channel's uploads). Downloading copyrighted material without permission can
violate YouTube's Terms of Service and copyright law where you live. This tool
doesn't check that for you — that's on you.

## Setup

You'll need Python 3.8+ and `ffmpeg` (used to merge video/audio and convert to mp3).

```bash
# 1. Install ffmpeg
#    macOS:   brew install ffmpeg
#    Ubuntu:  sudo apt install ffmpeg
#    Windows: https://ffmpeg.org/download.html

# 2. Install Python dependencies
pip install -r requirements.txt
```

## Option A: Command line

```bash
python tubegrabber.py "https://www.youtube.com/watch?v=XXXXXXXXXXX"
```

Common flags:

| Flag | What it does |
|---|---|
| `-o, --output` | Where to save files (default: `./downloads`) |
| `-q, --quality` | `best`, `1080p`, `720p`, `480p`, `360p`, `worst` |
| `--audio-only` | Extract audio and save as mp3 |
| `--playlist` | Download the whole playlist, not just the one video |
| `--subs` | Download subtitles |
| `--sub-lang` | Subtitle language code (default: `en`) |

Examples:

```bash
# Best quality video
python tubegrabber.py "https://youtu.be/XXXXXXXXXXX"

# Audio only, mp3
python tubegrabber.py "https://youtu.be/XXXXXXXXXXX" --audio-only

# Whole playlist at 720p, with English subtitles
python tubegrabber.py "https://youtube.com/playlist?list=XXXX" --playlist -q 720p --subs

# Multiple links at once (just list them, space-separated)
python tubegrabber.py "https://youtu.be/AAA" "https://youtu.be/BBB" "https://youtu.be/CCC"

# Multiple links from a text file (one URL per line)
python tubegrabber.py --file links.txt --audio-only
```

## Option B: Web app

```bash
python webapp.py
```

Then open **http://127.0.0.1:5000** in your browser. Paste a URL, pick your
options, hit **Grab it**, and watch the progress bar. Finished files show up
in the `downloads/` folder next to the app, and you can also grab them
directly from `http://127.0.0.1:5000/downloads/<filename>`.

**Downloading several links at once:** paste one link per line (or separate
them with commas) into the URL box. TubeGrabber queues them and downloads
one after another, showing both the current file's progress and an overall
"Queue: 2 of 5" style progress bar. If a couple of links in the batch fail
(bad URL, private video, etc.), the rest still download — you'll get a
summary of how many succeeded and how many failed at the end.

## Project structure

```
tubegrabber/
├── tubegrabber.py      # CLI tool
├── webapp.py           # Flask web UI (backend)
├── templates/
│   └── index.html      # Web UI (frontend)
├── requirements.txt
├── README.md
└── downloads/          # created automatically, where files are saved
```

## Troubleshooting

- **"ffmpeg not found"** — install ffmpeg and make sure it's on your PATH
  (`ffmpeg -version` should work in your terminal).
- **Download fails / "Unable to extract"** — yt-dlp is updated frequently to
  keep up with YouTube changes. Try `pip install -U yt-dlp` to get the latest
  version.
- **Playlist only downloads one video** — add `--playlist` (CLI) or check the
  "Full playlist" box (web app).
