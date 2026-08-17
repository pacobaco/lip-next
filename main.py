#!/usr/bin/env python3
"""
lip – International newspaper headline scraper + ranker
Minimal working version covering upgrades 1–4
"""

import os
import yaml
import logging
from pathlib import Path
from typing import List

# Local imports (adjust path if needed)
from src.lip.scraper import scrape_sources
from src.lip.ranking import rank_articles
from src.lip.db import insert_url, insert_keyword, link_keyword_to_url
from src.lip.utils import logger  # assumes logger is defined there

# -------------------------------------------------
# Config
# -------------------------------------------------
CONFIG_PATH = Path("config/sources.yaml")
MAX_PAGES = 12
TOP_N = 20
SEED_KEYWORDS = ["election", "economy", "climate", "war", "technology"]  # customize

def load_sources() -> List[str]:
    if not CONFIG_PATH.exists():
        logger.error(f"Config not found: {CONFIG_PATH}")
        return []
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    return [s if isinstance(s, str) else s["url"] for s in data.get("sources", [])]

def store_results(ranked: List[dict]):
    """Safely store ranked headlines into MySQL (item 1 + 3)."""
    for item in ranked:
        url_id = insert_url(item["url"])
        if not url_id:
            continue
        # Simple keyword extraction from headline text
        words = [w.lower().strip(".,!?;:\"'") for w in item["text"].split() if len(w) > 3]
        for w in set(words):
            kid = insert_keyword(w)
            if kid:
                link_keyword_to_url(kid, url_id)

def main():
    logger.info("Starting lip pipeline (scrape → rank → store)")

    sources = load_sources()
    if not sources:
        logger.error("No sources loaded. Exiting.")
        return

    # 2. Scrape
    raw_pages = scrape_sources(sources, max_pages=MAX_PAGES)

    # Flatten headlines
    articles = []
    for page in raw_pages:
        for h in page.get("headlines", []):
            articles.append({
                "text": h["text"],
                "url": h["url"],
                "source": page["url"],
                "images": page.get("images", [])
            })

    if not articles:
        logger.warning("No headlines extracted.")
        return

    # 4. Rank
    ranked = rank_articles(articles, seed_keywords=SEED_KEYWORDS)

    # Store (1 + 3)
    try:
        store_results(ranked[:50])  # store top 50
        logger.info("Stored results in database.")
    except Exception as e:
        logger.error(f"DB storage failed: {e}")

    # Output
    print("\n=== TOP RANKED HEADLINES ===\n")
    for i, item in enumerate(ranked[:TOP_N], 1):
        print(f"{i:2d}. [{item['score']:.3f}] {item['text'][:100]}")
        print(f"    {item['url']}")
        print(f"    sentiment={item['sentiment']:.2f}  relevance={item['relevance']:.3f}  recency={item['recency']:.2f}\n")
    # ---------- Item 5: TTS + Multimedia ----------
    from src.lip.tts import create_daily_narration
    from src.lip.multimedia import create_slideshow

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    try:
        audio_file = create_daily_narration(ranked, output_dir, max_items=8)
        video_file = create_slideshow(
            ranked,
            audio_file,
            output_dir / f"daily_briefing_{Path.cwd().name}.mp4",
            max_items=8
        )
        logger.info(f"Daily multimedia ready: {video_file}")
    except Exception as e:
        logger.error(f"Multimedia generation failed: {e}")
if __name__ == "__main__":
    main()
