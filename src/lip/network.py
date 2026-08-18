from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict
from collections import OrderedDict
from .utils import logger

class NewsNetwork:
    def __init__(self, max_stories: int = 25, max_age_hours: float = 24.0,
                 state_file: Path = Path("output/network_state.json")):
        self.max_stories = max_stories
        self.max_age = timedelta(hours=max_age_hours)
        self.state_file = state_file
        self.stories: OrderedDict[str, Dict] = OrderedDict()
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                for item in data.get("stories", []):
                    self.stories[item["url"]] = item
            except Exception as e:
                logger.warning(f"State load failed: {e}")

    def _save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": datetime.now(timezone.utc).isoformat(),
                   "stories": list(self.stories.values())}
        self.state_file.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def update(self, ranked: List[Dict], min_score: float = 0.38) -> List[Dict]:
        now = datetime.now(timezone.utc).isoformat()
        # expire old
        for url in [u for u, s in self.stories.items()
                    if datetime.now(timezone.utc) - datetime.fromisoformat(s["added_at"]) > self.max_age]:
            del self.stories[url]
        # merge new
        for art in ranked:
            if art.get("score", 0) < min_score:
                continue
            url = art["url"]
            if url in self.stories:
                self.stories[url].update({"score": art["score"], "text": art.get("text"),
                                          "last_seen": now})
            else:
                self.stories[url] = {**art, "added_at": now, "last_seen": now,
                                     "audio_file": None, "play_count": 0}
        # keep top N
        top = sorted(self.stories.values(), key=lambda x: x.get("score", 0), reverse=True)[:self.max_stories]
        self.stories = OrderedDict((s["url"], s) for s in top)
        self._save()
        return list(self.stories.values())

    def get_playlist(self) -> List[Dict]:
        return list(self.stories.values())

    def get_stories_needing_audio(self) -> List[Dict]:
        return [s for s in self.stories.values() if not s.get("audio_file")]

    def mark_audio_generated(self, url: str, path: str):
        if url in self.stories:
            self.stories[url]["audio_file"] = path
            self._save()

    def export_m3u(self, path: Path = Path("output/lip_world_news.m3u")) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["#EXTM3U",
                 "#PLAYLIST:Lip World News – Rolling 24-Hour Network",
                 "#EXTENC:UTF-8",
                 f"# Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                 ""]
        for i, s in enumerate(self.get_playlist(), 1):
            audio = s.get("audio_file")
            if not audio or not Path(audio).exists():
                continue
            title = (s.get("text") or "Lip World News")[:120].replace("\n", " ")
            lines.append(f"#EXTINF:-1,{i}. {title}")
            lines.append(str(Path(audio).resolve()))
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"M3U written → {path}")
        return path
