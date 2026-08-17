from pathlib import Path
from typing import List, Dict, Optional
import logging
import requests
from io import BytesIO

from PIL import Image
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    ColorClip,
)

logger = logging.getLogger("lip")


def download_image(url: str, save_path: Path, size=(1280, 720)) -> Optional[Path]:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img.thumbnail(size)
        # pad to exact size if needed
        background = Image.new("RGB", size, (20, 30, 50))
        offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
        background.paste(img, offset)
        background.save(save_path, "JPEG", quality=85)
        return save_path
    except Exception as e:
        logger.warning(f"Image download failed ({url}): {e}")
        return None


def create_slideshow(
    ranked: List[Dict],
    audio_path: Path,
    output_path: Path,
    max_items: int = 8,
    duration_per_slide: float = 7.0,
) -> Optional[Path]:
    """Create a simple image + text overlay + voiceover video."""
    clips = []
    temp_dir = output_path.parent / "temp_images"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for i, item in enumerate(ranked[:max_items]):
        img_path = None
        images = item.get("images") or []
        if images:
            img_url = images[0].get("src")
            if img_url:
                img_path = download_image(img_url, temp_dir / f"slide_{i:02d}.jpg")

        if img_path and img_path.exists():
            clip = ImageClip(str(img_path)).set_duration(duration_per_slide)
        else:
            clip = ColorClip(size=(1280, 720), color=(20, 30, 50)).set_duration(
                duration_per_slide
            )

        title = (item.get("text") or item.get("title") or "")[:140]
        if len(title) == 140:
            title += "..."

        txt = TextClip(
            title,
            fontsize=34,
            color="white",
            font="Arial-Bold",
            size=(1180, None),
            method="caption",
            align="center",
        ).set_position(("center", 0.75)).set_duration(duration_per_slide)

        final_slide = CompositeVideoClip([clip, txt])
        clips.append(final_slide)

    if not clips:
        logger.error("No slides could be created.")
        return None

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(str(audio_path))

    final_duration = min(video.duration, audio.duration)
    final = video.set_audio(audio).set_duration(final_duration)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,  # quieter
    )
    logger.info(f"Slideshow saved → {output_path}")
    return output_path
