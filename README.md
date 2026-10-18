<div align="center">

# 🎵 Spodo

**A sleek, high-performance desktop Spotify playlist, album, and track downloader with embedded ID3 metadata, album artwork, bilingual UI, and automated YouTube anti-bot bypass.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pair Programmed with Gemini](https://img.shields.io/badge/AI%20Assisted-Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-8b5cf6?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](LICENSE)

[Features](#-key-features) • [Quickstart](#-quickstart) • [Anti-Bot Bypass](#-preventing-youtube-bot-blocks) • [About](#-about) • [Contributors](#-contributors)

---

</div>

> [!TIP]
> 🇳🇱 **Nederlandstalig?** Spodo is bedacht door een Nederlandse IT-student en bevat volledige ondersteuning voor Nederlands en Engels. Wissel direct tussen talen via de knop rechtsboven (`🇳🇱 NL`).

> [!NOTE]
> <a name="-about"></a>
> ### ℹ️ Project Context
> **Full disclosure:** I am an IT student, not a software developer, and don't know the deep ins and outs of how this code runs under the hood.
> 
> Frustrated by existing downloaders breaking or getting blocked by YouTube bot checks, I built Spodo together with **Google Gemini**, which handled the Python architecture, code, and bug fixes.
> 
> If you encounter any bugs, feel free to open a [GitHub Issue](https://github.com/jente509/spodo/issues)!

---

### ✨ Key Features
- **⚡ Multi-Threaded Parallel Downloads**: Download multiple tracks concurrently (1 to 4 threads) powered by a thread-safe worker pool. *(Recommended: 2–3 threads for optimal speed without triggering YouTube rate limits).*
- **📜 Smooth Large Playlist Handling**: Chunked progressive UI rendering ensures instant responsiveness even with massive playlists (500 to 3,000+ tracks).
- **🎵 Fast Spotify Metadata Fetching**: Fetch tracks, albums, or entire playlists via public Spotify URLs or your connected personal Spotify account with automatic multi-tier web fallback (API, scraper & embed).
- **🏷️ Studio-Quality ID3 Tagging**: Automatically embeds track title, artists, album title, release year, track number, and high-resolution album artwork into the file.
- **🎧 Audio Formats & Bitrates**:
  - MP3 (up to 320 kbps)
  - M4A / AAC
  - FLAC (Lossless)
  - OPUS
- **🍪 Smart YouTube Anti-Bot Bypass**:
  - Automatically avoids YouTube *"Sign in to confirm you’re not a bot"* challenges.
  - 1-click cookie synchronization from your preferred browser (Brave, Chrome, Edge, Firefox, Opera, Safari, Vivaldi).
  - Securely caches extracted cookies into an isolated file so downloads work seamlessly **even while your browser remains open**.
  - Alternative support for standard `cookies.txt` imports.
- **🎨 Modern Dark & Light Mode**:
  - Beautiful CustomTkinter interface.
  - Instant toggle (`🌙` / `☀️`) in the top navigation bar.
- **📦 Zero-Config FFmpeg**: Automatically detects, downloads, and injects a standalone FFmpeg into both the active process `PATH` and Windows system environment so downloads work immediately without manual setup.
- **🌐 Bilingual UI**: Seamless 1-click toggle between **English** and **Nederlands** directly in the header (`🇬🇧 EN` / `🇳🇱 NL`).

---

### 🚀 Quickstart

#### 1. Requirements
- [Python 3.10 or higher](https://www.python.org/downloads/)
- (Optional) A web browser (Brave, Chrome, Edge, Firefox) for YouTube cookies if downloading large playlists.

#### 2. Clone Repository
```bash
git clone https://github.com/jente509/spodo.git
cd spodo
```

#### 3. Launch
- **Windows**: Double-click `run.bat` or run:
  ```cmd
  run.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

*The launch script automatically creates a Python virtual environment (`venv`), installs dependencies from `requirements.txt`, and boots Spodo.*

---

### ⚙️ Spotify API Credentials (Optional)
Spodo works out-of-the-box in **Public Mode** for any public playlist or track link. To access your private playlists and Liked Songs:
1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Create a free app and set **Redirect URI** to: `http://127.0.0.1:3001/api/callback`
3. Click the **⚙ (Settings)** button in Spodo and enter your Client ID and Client Secret.

---

### 🍪 Preventing YouTube Bot Blocks
If YouTube prompts you with *"Sign in to confirm you’re not a bot"*:
1. Open Spodo's **⚙ (Settings)**.
2. Under **YouTube Cookies**, select your everyday browser (e.g., *Brave*, *Chrome*, *Edge*, *Firefox*).
3. Click **🔄 Synchronize from [Browser]**.
4. Spodo will safely extract your YouTube cookies into an isolated file, preventing database lock errors and ensuring uninterrupted downloads.

---

### ⚡ Parallel Downloads & Speed
Under **⚙ (Settings) ➜ Audio & Speed**, you can configure the number of concurrent download threads:
- **1 Thread**: Safest against IP rate-limiting and YouTube bot challenges.
- **2 to 3 Threads (Recommended)**: The ideal sweet spot. Downloads up to 3× faster while keeping YouTube stream requests reliable.
- **4 Threads**: Maximum performance. Great for bulk downloads, though aggressive rate-limiting on individual streams may occasionally require a quick re-run.

---

<a name="-contributors"></a>
## 👥 Contributors

| Contributor | Role |
| :--- | :--- |
| **[Jente (@jente509)](https://github.com/jente509)** | Project Creator *(IT student)* |
| **[Gemini (Google DeepMind)](https://deepmind.google/technologies/gemini/)** | AI Code Architecture & Development |

---

### 📄 License
Distributed under the [MIT License](LICENSE).

<div align="center">
  <sub>Crafted because i wanted a downloader that works</sub>
</div>
