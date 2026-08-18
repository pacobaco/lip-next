# Lip – Rolling 24\-Hour World News Network

Lip is a rolling 24\-hour automated world news network that continuously scrapes, ranks, and delivers major international stories via synthesized TTS voiceover and short visual segments in an endless looping briefing cycle\.

## Features

- Continuous scraping of international newspaper sources \(region\-grouped\)
- Intelligent ranking focused on major world news \(conflict, elections, economy, climate, geopolitics\)
- Rolling 24\-hour queue of top stories with automatic expiry
- Short professional TTS voiceovers generated with `edge-tts`
- Auto\-generated M3U playlist for any audio player \(VLC, mpv, etc\.\)
- Optional image\-based video segments
- Persistent state \+ optional MySQL storage
- Fully modular Python package

## Project Structure

```text
lip/
├── config/
│   └── sources.yaml
├── src/
│   └── lip/
│       ├── __init__.py
│       ├── utils.py
│       ├── db.py
│       ├── scraper.py
│       ├── ranking.py
│       ├── tts.py
│       ├── network.py
│       └── multimedia.py
├── output/                  # created automatically
├── network_runner.py        # main continuous entrypoint
├── main.py                  # optional one-shot mode
├── requirements.txt
├── schema.sql
├── .gitignore
└── README.md
```

## Quick Start

```bash
# Clone or create the project directory
cd lip

# Create virtual environment
python -m venv venv
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure MySQL
export LIP_DB_HOST=localhost
export LIP_DB_USER=root
export LIP_DB_PASSWORD=yourpassword
export LIP_DB_NAME=lip

# Run the rolling 24-hour network
python network_runner.py
```

After the first cycle you will find:

- `output/network_state.json` – current live stories
- `output/audio/story_*.mp3` – TTS voiceovers
- `output/lip_world_news.m3u` – open this file in any audio player

## How It Works

1. Every 20 minutes the system scrapes the sources listed in `config/sources.yaml`\.
2. Headlines are ranked with TF\-IDF \+ sentiment \+ major\-news topic boosts\.
3. Only high\-scoring stories enter the rolling 24\-hour network queue\.
4. Missing TTS audio is generated automatically\.
5. A fresh M3U playlist is written so you can listen continuously\.

## Configuration

- **Sources:** Edit `config/sources.yaml` \(already grouped by region\)
- **Cycle frequency:** Change `CYCLE_MINUTES` in `network_runner.py`
- **Minimum score:** Adjust `MIN_SCORE` to control how selective the network is
- **Voice:** Change the voice parameter in `tts.py` \(edge\-tts voices\)

## One\-shot / Daily Mode

You can still run a single pass with:

```bash
python main.py
```

## Requirements

- Python 3\.10\+
- FFmpeg \(for optional video generation with MoviePy\)
- MySQL \(optional\)

## License

MIT \(or keep the original project license\)

## Original Project

This is an upgraded version of the original repository:

https://github\.com/pacobaco/lip
