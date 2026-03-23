"""TTS narration generation using edge-tts."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import edge_tts

from agent_screencast.models import Script


def get_audio_duration(path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


async def generate_segment_audio(
    segment_id: str,
    text: str,
    output_dir: Path,
    voice: str = "en-US-GuyNeural",
) -> tuple[str, str, int]:
    """Generate MP3 + SRT for a single segment. Returns (audio_path, srt_path, duration_ms)."""
    audio_path = output_dir / f"{segment_id}.mp3"
    srt_path = output_dir / f"{segment_id}.srt"

    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

    with open(srt_path, "w") as srt_file:
        srt_file.write(submaker.get_srt())

    duration = get_audio_duration(str(audio_path))
    duration_ms = int(duration * 1000)

    return str(audio_path), str(srt_path), duration_ms


async def generate_all_narration(script: Script, output_dir: Path) -> Script:
    """Generate audio for all segments and return enriched script."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for segment in script.segments:
        print(f"  Generating narration for segment: {segment.id}")
        audio_path, srt_path, duration_ms = await generate_segment_audio(
            segment_id=segment.id,
            text=segment.narration,
            output_dir=output_dir,
            voice=script.voice,
        )
        segment.audio_path = audio_path
        segment.srt_path = srt_path
        segment.duration_ms = duration_ms
        print(f"    Duration: {duration_ms}ms")

    # Save enriched script
    enriched_path = output_dir / "script-enriched.json"
    script.save(enriched_path)
    print(f"  Enriched script saved to {enriched_path}")

    return script


def generate_narration(script: Script, output_dir: Path) -> Script:
    """Sync wrapper for narration generation."""
    return asyncio.run(generate_all_narration(script, output_dir))
