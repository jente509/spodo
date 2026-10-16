<div align="center">

# 🎵 Spodo

**A sleek, high-performance desktop Spotify playlist, album, and track downloader with embedded ID3 metadata, album artwork, bilingual UI, and automated YouTube anti-bot bypass.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Vibe Coded](https://img.shields.io/badge/Vibe%20Coded-100%25-ff69b4?style=for-the-badge&logo=visual-studio-code&logoColor=white)](#-vibe-coded-disclaimer)
[![Pair Programmed with Gemini](https://img.shields.io/badge/Pair%20Programmed%20with-Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-8b5cf6?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](LICENSE)

[English](#-english) • [Nederlands](#-nederlands) • [Vibe Disclaimer](#-vibe-coded-disclaimer) • [Contributors](#-contributors)

---

</div>

> [!IMPORTANT]
> <a name="-vibe-coded-disclaimer"></a>
> ### 🧘‍♂️ 100% Vibe-Coded Disclaimer / Vibe-Coding Verklaring
> **English**: This entire application was brainstormed, architected, and vibe-coded live through an organic pair-programming session between **Jente** ([@jente509](https://github.com/jente509)) and **Gemini** (Google DeepMind). Driven purely by passion for music, caffeine, and immaculate AI vibes. Things might be wild under the hood, but it runs like a dream. Built for fun, personal use, and pristine vibes! 🎧✨
> 
> **Nederlands**: Deze hele applicatie is live bedacht, opgebouwd en gevibecoded in een organische pair-programming sessie tussen **Jente** ([@jente509](https://github.com/jente509)) en **Gemini** (Google DeepMind). Aangedreven door pure muziekliefde, koffie en uitstekende AI-vibes. Geen garanties, puur voor plezier en eigen gebruik. Geniet van je tunes! ✌️🎵

---

## 🌐 Languages / Talen
Spodo features full native bilingual support! Switch instantly between **English** and **Nederlands** with 1 click directly in the top header (`🇬🇧 EN` / `🇳🇱 NL`) without restarting the app.

---

<a name="-english"></a>
## 🇬🇧 English

### ✨ Key Features
- **⚡ Fast Spotify Downloading**: Fetch tracks, albums, or entire playlists via public Spotify URLs or your connected personal Spotify account.
- **🏷️ Studio-Quality ID3 Tagging**: Automatically embeds track title, artists, album title, release year, track number, and high-resolution album artwork into the file.
- **🎧 Audio Formats & Bitrates**:
  - MP3 (up to 320 kbps)
  - M4A / AAC
  - FLAC (Lossless)
  - OPUS
- **🍪 YouTube Anti-Bot Bypass**:
  - Automatically avoids YouTube *"Sign in to confirm you’re not a bot"* challenges.
  - 1-click cookie synchronization from your preferred browser (Brave, Chrome, Edge, Firefox, Opera, Safari, Vivaldi).
  - Securely caches extracted cookies in an isolated file so downloads work seamlessly **even while your browser stays open**.
  - Also supports standard `cookies.txt` imports.
- **🎨 Modern Dark & Light Mode**:
  - Beautiful CustomTkinter interface.
  - Instant toggle (`🌙` / `☀️`) in the top navigation bar.
- **📦 Zero-Config FFmpeg**: Automatically detects or downloads a standalone FFmpeg on Windows so you never need to configure system PATH variables.

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

<br/>

---

<a name="-nederlands"></a>
## 🇳🇱 Nederlands

### ✨ Belangrijkste Functies
- **⚡ Razendsnel Spotify Downloaden**: Download complete afspeellijsten, albums of losse nummers via een Spotify-link of je eigen account.
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
git clone https://github.com/jente509/spodo.git
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

<a name="-contributors"></a>
## 👥 Contributors

This project is co-created with love:

| Contributor | Role | Link |
| :--- | :--- | :--- |
| 🧑‍💻 **Jente** | Creator, Project Lead & Vibe Curator | [@jente509](https://github.com/jente509) |
| 🤖 **Gemini** | AI Pair Programmer & Code Architect | [Google DeepMind](https://deepmind.google/technologies/gemini/) |

---

### 📄 Licentie
Gedistribueerd onder de [MIT Licentie](LICENSE).

<div align="center">
  <sub>Gemaakt met passie voor muziek en AI-vibes 🎵✨</sub>
</div>
