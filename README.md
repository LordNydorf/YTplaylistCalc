# PlayPulse — YouTube Playlist Duration & Study Calculator

[![Netlify Status](https://api.netlify.com/api/v1/badges/1776a7ab-114a-4984-a7a3-9abf32fcc964/deploy-status)](https://app.netlify.com/projects/playpulse-duration/deploys)


We all know the struggle—you're cramming for an exam, and there's this massive playlist on YouTube that explains everything you need to know. But there's one problem... you have no idea how long it will take to watch the whole thing. If you're like me and tend to leave studying to the last minute, time becomes a big factor.
That's why I built this app! You just paste the link to a YouTube playlist, and it spits out the total duration, so you can know exactly how long the playlist is before diving in. Sure, it might enable some of my procrastination tendencies, but hey, it's still super useful!

This is a web application that calculates the total duration of all the videos in a YouTube playlist. The application is built with Python and Flask on the backend, and HTML and CSS on the frontend. It uses the YouTube Data API v3 to fetch video data from the playlist.

🌐 **Live Website**: [https://playpulse-duration.netlify.app](https://playpulse-duration.netlify.app)

---

## ✨ Features

- **⚡ Instant Total Duration**: Paste any YouTube playlist link or ID to fetch total runtime in days, hours, minutes, and seconds.
- **🚀 Multi-Speed Comparison Matrix**: See exact adjusted watch times and hours/minutes saved at **1.0x, 1.25x, 1.5x, 1.75x, and 2.0x** speeds.
- **🎚️ Smooth Custom Speed Slider**: Adjust playback speed continuously from **0.50x to 3.00x** with real-time recalculations.
- **📅 Daily Study Schedule Planner**: Choose your daily study commitment (**30 min, 1 hr, 2 hrs, 3 hrs/day**) to calculate the required days and exact projected completion date.
- **🎯 Custom Range & Video Filters**: Calculate specific subsets (e.g. video #5 to #25) or toggle individual videos on and off in the breakdown drawer.
- **📊 Deep Playlist Insights**: View average video length, identify the longest and shortest videos in the playlist, and track total indexed count.
- **📋 One-Click Formatted Export**: Copy a clean, emoji-formatted markdown summary for Discord, Slack, Notion, or personal study notes.
- **🌓 Dark & Light Luxe Themes**: Glassmorphic UI with animated glowing atmospheric orbs and `localStorage` persistence.
- **📱 PWA & Mobile Optimized**: Responsive grid layout with touch-friendly actions and `site.webmanifest` support.
- **🔍 SEO & Social Media Ready**: Complete OpenGraph, Twitter Cards, Schema.org JSON-LD, `robots.txt`, and `sitemap.xml`.

---

## 🛠️ Tech Stack

### Frontend
- **HTML5 & Vanilla CSS3**: Custom Dark Luxe design system with glassmorphism, responsive CSS grid, and micro-animations.
- **Vanilla ES6+ JavaScript**: Client-side state management, range filtering, and dynamic speed calculations.
- **Google Fonts**: Plus Jakarta Sans & JetBrains Mono.

### Backend & Serverless
- **Python / Flask**: Backend API handling YouTube Data API v3 pagination, batching, and ISO-8601 duration parsing.
- **Netlify Serverless Functions**: Native, zero-dependency Node.js (`netlify/functions/get_playlist_duration.js`) and Python handlers for CDN deployment.

---

## 🚀 Getting Started Locally

### Prerequisites
- Python 3.10+
- A Google Cloud YouTube Data API v3 key ([Get a free key here](https://console.cloud.google.com/))

### 1. Clone the repository
```bash
git clone https://github.com/LordNydorf/YTplaylistCalc.git
cd YTplaylistCalc
```

### 2. Create and activate a virtual environment
```bash
# On Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here
```

### 5. Run the development server
```bash
python app.py
```
Open your browser and visit: **`http://127.0.0.1:5000`**

---

## ☁️ Deployment (Netlify)

This project is pre-configured for one-click deployment on Netlify using the included `netlify.toml` and serverless functions:

1. Push your repository to GitHub.
2. Link the repository in **Netlify**.
3. Under **Site Settings → Environment Variables**, add:
   - `YOUTUBE_API_KEY`: Your YouTube API key.
4. Trigger deploy! Netlify will automatically serve the static CDN frontend from `public/` and route `/get_playlist_duration` to the serverless function.

---

## ⚖️ Legal & Compliance

This tool uses YouTube API Services. By using PlayPulse, users agree to be bound by the [YouTube Terms of Service](https://www.youtube.com/t/terms) and [Google Privacy Policy](https://policies.google.com/privacy).

PlayPulse is an independent utility and is not affiliated with, endorsed by, or sponsored by YouTube or Google LLC.

---

## ☕ Support

If PlayPulse helped you plan your studies or saved you time, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-lordnydorf-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/lordnydorf)

**Created by [Rohit Krishnan](https://lordnydorf.github.io/Portfolio/)**
