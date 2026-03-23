"""FFmpeg assembly: merge video + audio + subtitles into final MP4."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agent_screencast.models import Script


def _format_srt_time(ms: int) -> str:
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    remainder = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{remainder:03d}"


def _parse_srt_time(t: str) -> int:
    parts = t.replace(",", ":").split(":")
    return int(parts[0]) * 3600000 + int(parts[1]) * 60000 + int(parts[2]) * 1000 + int(parts[3])


def concatenate_audio(script: Script, output_dir: Path) -> Path:
    """Concatenate all segment audio files into one track."""
    list_file = output_dir / "audio-list.txt"
    with open(list_file, "w") as f:
        for seg in script.segments:
            if seg.audio_path:
                abs_path = Path(seg.audio_path).resolve()
                f.write(f"file '{abs_path}'\n")

    full_audio = output_dir / "narration-full.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(full_audio),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return full_audio


def concatenate_subtitles(script: Script, output_dir: Path) -> Path:
    """Concatenate all segment SRT files with offset timestamps."""
    offset_ms = 0
    cue_index = 1
    output_lines: list[str] = []

    for seg in script.segments:
        if not seg.srt_path or not seg.duration_ms:
            continue

        srt_path = Path(seg.srt_path)
        if not srt_path.exists():
            offset_ms += seg.duration_ms
            continue

        content = srt_path.read_text().strip()
        if not content:
            offset_ms += seg.duration_ms
            continue

        blocks = content.split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                times = lines[1]
                start_str, end_str = times.split(" --> ")
                start_ms = _parse_srt_time(start_str.strip()) + offset_ms
                end_ms = _parse_srt_time(end_str.strip()) + offset_ms
                text = "\n".join(lines[2:])

                output_lines.append(str(cue_index))
                output_lines.append(f"{_format_srt_time(start_ms)} --> {_format_srt_time(end_ms)}")
                output_lines.append(text)
                output_lines.append("")
                cue_index += 1

        offset_ms += seg.duration_ms

    full_srt = output_dir / "captions-full.srt"
    full_srt.write_text("\n".join(output_lines))
    return full_srt


def _has_subtitles_filter() -> bool:
    """Check if ffmpeg has the subtitles filter (requires libass)."""
    result = subprocess.run(
        ["ffmpeg", "-filters"],
        capture_output=True,
        text=True,
    )
    return "subtitles" in result.stdout


def assemble_video(
    script: Script,
    video_path: str,
    output_path: str,
    session_dir: Path,
) -> None:
    """Merge video + audio + subtitles into final MP4."""
    print("  Concatenating audio tracks...")
    full_audio = concatenate_audio(script, session_dir)

    print("  Building subtitle track...")
    full_srt = concatenate_subtitles(script, session_dir)

    print(f"  Assembling final video -> {output_path}")

    has_subs_filter = _has_subtitles_filter()
    if not has_subs_filter:
        print("  Note: ffmpeg lacks libass — embedding subtitles as soft track")

    if has_subs_filter:
        # Burn subtitles into video using libass
        subtitle_style = (
            "FontName=Arial,"
            "FontSize=22,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H80000000,"
            "BorderStyle=4,"
            "Outline=1,"
            "Shadow=0,"
            "MarginV=40"
        )
        srt_abs = str(full_srt.resolve())
        srt_escaped = (
            srt_abs.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        vf = f"subtitles={srt_escaped}:force_style='{subtitle_style}'"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", str(full_audio),
                "-vf", vf,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                output_path,
            ],
            check=True,
        )
    else:
        # No libass: embed SRT as a soft subtitle track in MP4
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", str(full_audio),
                "-i", str(full_srt),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-c:s", "mov_text",
                "-metadata:s:s:0", "language=eng",
                "-shortest",
                output_path,
            ],
            check=True,
        )

    print(f"  Final video: {output_path}")
    if not has_subs_filter:
        print("  Tip: brew install ffmpeg --with-libass for burned-in subtitles")
