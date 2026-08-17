import asyncio
from pathlib import Path
from typing import List, Dict
import logging
import edge_tts

logger = logging.getLogger("lip")


async def _generate_audio(text: str, output_path: Path, voice: str = "en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    logger.info(f"Audio saved → {output_path}")


def generate_audio(text: str, output_path: Path, voice: str = "en-US-JennyNeural") -> Path:
    """Synchronous wrapper for edge-tts."""
    asyncio.run(_generate_audio(text, output_path, voice))
    return output_path


def create_daily_narration(
    ranked: List[Dict],
    output_dir: Path,
    max_items: int = 8,
    voice: str = "en-US-JennyNeural",
) -> Path:
    """Create one combined daily briefing audio from ranked headlines."""
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "daily_briefing.mp3"

    lines = ["Here is your international news briefing for today."]
    for i, item in enumerate(ranked[:max_items], 1):
        text = item.get("text") or item.get("title") or ""
        lines.append(f"Story number {i}. {text}.")

    full_text = " ".join(lines)
    return generate_audio(full_text, audio_path, voice)
