import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging once
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lip")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException,)),
)
def safe_get(url: str, timeout: int = 20) -> requests.Response:
    """Robust GET with retries and polite User-Agent."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LipBot/0.2; "
            "+https://github.com/pacobaco/lip)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp
