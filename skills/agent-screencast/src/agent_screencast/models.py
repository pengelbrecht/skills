"""Data models for segment scripts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Action:
    cmd: str
    arg: str

    def to_dict(self) -> dict:
        return {"cmd": self.cmd, "arg": self.arg}


@dataclass
class Segment:
    id: str
    narration: str
    actions: list[Action]
    caption_overlay: str | None = None

    # Populated after narration generation
    audio_path: str | None = None
    srt_path: str | None = None
    duration_ms: int | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "id": self.id,
            "narration": self.narration,
            "actions": [a.to_dict() for a in self.actions],
            "caption_overlay": self.caption_overlay,
        }
        if self.audio_path:
            d["_audio_path"] = self.audio_path
        if self.srt_path:
            d["_srt_path"] = self.srt_path
        if self.duration_ms is not None:
            d["_duration_ms"] = self.duration_ms
        return d


@dataclass
class Script:
    title: str
    base_url: str
    voice: str = "en-US-GuyNeural"
    segments: list[Segment] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "base_url": self.base_url,
            "voice": self.voice,
            "segments": [s.to_dict() for s in self.segments],
        }

    def save(self, path: str | Path) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> Script:
        with open(path) as f:
            data = json.load(f)

        segments = []
        for seg_data in data.get("segments", []):
            actions = [Action(**a) for a in seg_data.get("actions", [])]
            seg = Segment(
                id=seg_data["id"],
                narration=seg_data["narration"],
                actions=actions,
                caption_overlay=seg_data.get("caption_overlay"),
                audio_path=seg_data.get("_audio_path"),
                srt_path=seg_data.get("_srt_path"),
                duration_ms=seg_data.get("_duration_ms"),
            )
            segments.append(seg)

        return cls(
            title=data.get("title", "Untitled"),
            base_url=data.get("base_url", ""),
            voice=data.get("voice", "en-US-GuyNeural"),
            segments=segments,
        )
