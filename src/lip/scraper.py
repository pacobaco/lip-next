from urllib.parse import urljoin, urlparse
from typing import List, Dict
from bs4 import BeautifulSoup
import logging

from .utils import safe_get, logger


def extract_headlines(base_url: str, html: str, min_length: int = 20) -> List[Dict]:
    """Extract meaningful headlines instead of every <a> tag."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    # Prefer semantic / common news selectors
    candidates = (
        soup.select(
            "h1 a, h2 a, h3 a, article a, .headline a, .title a, "
            ".story-title a, .news-title a, [class*='headline'] a"
        )
        or soup.find_all("a", href=True)
    )

    for a in candidates:
        text = " ".join(a.get_text(strip=True).split())
        if len(text) < min_length:
            continue

        href = a.get("href")
        if not href:
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.scheme not in ("http", "https"):
            continue
        if full_url in seen or full_url.rstrip("/") == base_url.rstrip("/"):
            continue

        seen.add(full_url)
        results.append({"text": text, "url": full_url})

    return results


def extract_images(base_url: str, html: str, limit: int = 8) -> List[Dict]:
    """Extract images with resolved absolute URLs."""
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img in soup.find_all("img", src=True):
        src = urljoin(base_url, img["src"])
        alt = img.get("alt") or img.get("title") or ""
        if src.startswith("http"):
            images.append({"src": src, "alt": alt})
        if len(images) >= limit:
            break
    return images


def scrape_page(url: str) -> Dict:
    """Scrape a single page and return structured data."""
    try:
        resp = safe_get(url)
        headlines = extract_headlines(url, resp.text)
        images = extract_images(url, resp.text)

        return {
            "url": url,
            "headlines": headlines,
            "images": images,
            "status": "ok",
        }
    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return {
            "url": url,
            "headlines": [],
            "images": [],
            "status": "error",
            "error": str(e),
        }


def scrape_sources(source_urls: List[str], max_pages: int = 20) -> List[Dict]:
    """Scrape a list of source pages."""
    results = []
    for url in source_urls[:max_pages]:
        logger.info(f"Scraping {url}")
        results.append(scrape_page(url))
    return results
