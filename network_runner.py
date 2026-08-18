#!/usr/bin/env python3
"""Lip Rolling 24-Hour World News Network – continuous runner"""
import time
from pathlib import Path
import yaml
from src.lip.scraper import scrape_sources
from src.lip.ranking import rank_articles
from src.lip.network import NewsNetwork
from src.lip.tts import generate_missing_audio
from src.lip.utils import logger

CONFIG = Path("config/sources.yaml")
OUTPUT = Path("output")
AUDIO = OUTPUT / "audio"
CYCLE_MINUTES = 20
MAX_PAGES = 12
MIN_SCORE = 0.38
SEEDS = ["war", "conflict", "election", "economy", "climate", "china", "russia",
         "ukraine", "israel", "gaza", "markets", "sanctions", "disaster"]

def load_sources():
    data = yaml.safe_load(CONFIG.read_text())
    return [s if isinstance(s, str) else s.get("url") for s in data.get("sources", [])]

def run_cycle(net: NewsNetwork):
    logger.info("=== Network cycle start ===")
    sources = load_sources()
    raw = scrape_sources(sources, max_pages=MAX_PAGES)
    articles = []
    for page in raw:
        for h in page.get("headlines", []):
            articles.append({"text": h["text"], "url": h["url"],
                             "source": page["url"], "images": page.get("images", [])})
    if not articles:
        logger.warning("No headlines this cycle")
        return
    ranked = rank_articles(articles, seed_keywords=SEEDS)
    playlist = net.update(ranked, min_score=MIN_SCORE)
    needing = net.get_stories_needing_audio()
    if needing:
        generate_missing_audio(needing, AUDIO)
        for s in needing:
            if s.get("audio_file"):
                net.mark_audio_generated(s["url"], s["audio_file"])
    m3u = net.export_m3u()
    print("\n" + "="*70)
    print(f"LIP WORLD NEWS – {len(playlist)} major stories live")
    print("="*70)
    for i, s in enumerate(playlist[:10], 1):
        mark = "🔊" if s.get("audio_file") else "…"
        print(f"{i:2}. {mark} [{s['score']:.3f}] {s['text'][:85]}")
    print("="*70)
    logger.info(f"Playlist ready: {m3u}")

def main():
    logger.info("Starting Lip 24-Hour World News Network")
    OUTPUT.mkdir(exist_ok=True)
    AUDIO.mkdir(exist_ok=True)
    net = NewsNetwork(max_stories=25, max_age_hours=24,
                      state_file=OUTPUT / "network_state.json")
    while True:
        try:
            run_cycle(net)
        except Exception as e:
            logger.exception(f"Cycle error: {e}")
        logger.info(f"Sleeping {CYCLE_MINUTES} min…")
        time.sleep(CYCLE_MINUTES * 60)

if __name__ == "__main__":
    main()
