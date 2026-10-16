<div align="center">

# 🎵 Spodo

**A sleek, high-performance desktop Spotify playlist, album, and track downloader with embedded ID3 metadata, album artwork, bilingual UI, and automated YouTube anti-bot bypass.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![yt--dlp](https://img.shields.io/badge/Engine-yt--dlp-red.svg?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20Nederlands-orange.svg)](#-languages--talen)

[English](#-english) • [Nederlands](#-nederlands)

---

</div>

## 🌐 Languages / Talen
Spodo has full native bilingual support! Switch seamlessly between **English** and **Nederlands** with 1 click directly in the top header without restarting.

---

<a name="-english"></a>
## 🇬🇧 English

### ✨ Key Features
- **⚡ Fast Spotify Downloading**: Fetch tracks, albums, or full playlists via public Spotify URLs or via OAuth login.
- **🏷️ High-Quality ID3 Tagging**: Automatically embeds track title, artists, album title, release year, track number, and high-resolution album artwork into the output file.
- **🎧 Audio Format Options**:
  - MP3 (up to 320 kbps)
  - M4A / AAC
  - FLAC (Lossless)
  - OPUS
- **🍪 Smart YouTube Anti-Bot Bypass**:
  - Automatically handles YouTube "Sign in to confirm you're not a bot" challenges.
  - One-click browser cookie synchronization (Brave, Chrome, Edge, Firefox, Opera, Safari, Vivaldi).
  - Securely caches extracted cookies in a local text file so you can download even while your browser stays open!
  - Alternative support for standard `cookies.txt` files.
- **🎨 Modern Dark & Light Mode**:
  - Built with CustomTkinter.
  - Instant theme toggle (`🌙` / `☀️`) in the top navigation bar.
- **📦 Zero-Config FFmpeg**: Automatically detects or downloads a standalone FFmpeg binary on Windows so you don't need manual PATH configuration.

---

### 🚀 Getting Started

#### 1. Prerequisites
- [Python 3.10 or higher](https://www.python.org/downloads/)
- (Optional) A modern web browser (Brave, Chrome, Edge, Firefox) for YouTube cookies if downloading large playlists.

#### 2. Installation
Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/spodo.git
cd spodo
```

#### 3. Quick Launch
- **Windows**: Double-click `run.bat` or run:
  ```cmd
  run.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

*The launch script automatically creates a Python virtual environment (`venv`), installs all required dependencies from `requirements.txt`, and boots Spodo.*

---

### ⚙️ Spotify API Credentials (Optional)
Spodo works out-of-the-box in **Public Mode** for any public playlist or song link. To view your own private playlists and Liked Songs:
1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in and click **Create App**.
3. Set **Redirect URI** to: `http://127.0.0.1:3001/api/callback`
4. Copy your **Client ID** and **Client Secret**.
5. Click the **⚙ (Settings)** button in Spodo and paste your credentials.

---

### 🍪 Preventing YouTube Bot Blocks
If YouTube prompts you with *"Sign in to confirm you’re not a bot"*:
1. Open Spodo's **⚙ (Settings)**.
2. Under **YouTube Cookies**, select your everyday browser (e.g., *Brave*, *Chrome*, *Edge*, *Firefox*).
3. Click **🔄 Synchronize from [Browser]**.
4. Spodo will safely extract your YouTube cookies into an isolated file, preventing database lock errors and ensuring uninterrupted downloads.

---

<br/>

---

<a name="-nederlands"></a>
## 🇳🇱 Nederlands

### ✨ Belangrijkste Functies
- **⚡ Snel Spotify Downloaden**: Download complete afspeellijsten, albums of losse nummers via een Spotify-link of je eigen account.
- **🏷️ Volledige ID3 Metadata**: Automatische toevoeging van artiesten, titel, album, jaartal, tracknummer en hoge resolutie albumcover.
- **🎧 Audioformaten**:
  - MP3 (tot 320 kbps)
  - M4A / AAC
  - FLAC (Lossless)
  - OPUS
- **🍪 Slimme YouTube Bot-Bypass**:
  - Voorkomt YouTube 'Sign in to confirm you’re not a bot' meldingen.
  - Synchroniseer met 1 klik je YouTube-cookies vanuit Brave, Chrome, Edge, Firefox of Opera.
  - Slaat cookies lokaal op zodat downloaden ALTIJD werkt, zelfs terwijl je browser geopend is.
  - Ondersteunt tevens `cookies.txt` bestanden.
- **🎨 Licht & Donker Thema**:
  - Prachtige CustomTkinter interface.
  - Direct schakelen tussen Donker (`🌙`) en Licht (`☀️`) in de bovenbalk.
- **📦 Automatische FFmpeg**: Spodo installeert indien nodig zelfstandig een draagbare FFmpeg zodat je direct aan de slag kunt.

---

### 🚀 Installatie & Starten

#### 1. Vereisten
- [Python 3.10 of hoger](https://www.python.org/downloads/)

#### 2. Klonen
```bash
git clone https://github.com/JOUW_GEBRUIKERSNAAM/spodo.git
cd spodo
```

#### 3. Starten
- **Windows**: Dubbelklik op `run.bat`
- **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

### 📄 Licentie
Dit project valt onder de [MIT Licentie](LICENSE).

---

<div align="center">
  <sub>Gemaakt met passie voor muziek 🎵</sub>
</div>
