# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "edge-tts>=7.2.8",
# ]
# ///
"""Record narrated, captioned video demos of web applications.

Usage:
    uv run agent-screencast.py <script.json> -o output.mp4 --session-dir ./session
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Narration (edge-tts)
# ---------------------------------------------------------------------------


def get_audio_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


async def generate_segment_audio(
    segment_id: str, text: str, output_dir: Path, voice: str = "en-US-GuyNeural"
) -> tuple[str, str, int]:
    import edge_tts

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
    return str(audio_path), str(srt_path), round(duration * 1000)


async def generate_all_narration(script: Script, output_dir: Path) -> Script:
    output_dir.mkdir(parents=True, exist_ok=True)

    for segment in script.segments:
        print(f"  Generating narration for segment: {segment.id}")
        audio_path, srt_path, duration_ms = await generate_segment_audio(
            segment.id, segment.narration, output_dir, script.voice
        )
        segment.audio_path = audio_path
        segment.srt_path = srt_path
        segment.duration_ms = duration_ms
        print(f"    Duration: {duration_ms}ms")

    enriched_path = output_dir / "script-enriched.json"
    script.save(enriched_path)
    print(f"  Enriched script saved to {enriched_path}")
    return script


def generate_narration(script: Script, output_dir: Path) -> Script:
    return asyncio.run(generate_all_narration(script, output_dir))


# ---------------------------------------------------------------------------
# Recording (agent-browser)
# ---------------------------------------------------------------------------


def _ab_cmd(base_args: list[str], *args: str) -> list[str]:
    return ["agent-browser", *base_args, *args]


def _run_ab(base_args: list[str], *args: str) -> str:
    split_args: list[str] = []
    for a in args:
        if " " in a:
            split_args.extend(shlex.split(a))
        else:
            split_args.append(a)
    cmd = _ab_cmd(base_args, *split_args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        if "error" in stderr.lower() or "failed" in stderr.lower():
            raise RuntimeError(
                f"agent-browser failed: {' '.join(cmd)}\nstderr: {stderr}\nstdout: {stdout}"
            )
    return result.stdout.strip()


def _inject_overlay(base_args: list[str], text: str) -> None:
    escaped = json.dumps(text)
    js = f"""(() => {{
    const prev = document.getElementById('demo-overlay');
    if (prev) prev.remove();
    const el = document.createElement('div');
    el.id = 'demo-overlay';
    el.textContent = {escaped};
    el.style.cssText = [
        'position: fixed',
        'bottom: 80px',
        'left: 50%',
        'transform: translateX(-50%)',
        'background: rgba(15, 15, 35, 0.9)',
        'color: #fff',
        'padding: 12px 28px',
        'border-radius: 8px',
        'font-size: 20px',
        'font-family: system-ui, sans-serif',
        'font-weight: 600',
        'z-index: 99999',
        'box-shadow: 0 4px 20px rgba(0,0,0,0.4)',
        'backdrop-filter: blur(8px)',
        'border: 1px solid rgba(255,255,255,0.1)',
    ].join(';');
    document.body.appendChild(el);
}})();"""
    cmd = _ab_cmd(base_args, "eval", "--stdin")
    subprocess.run(cmd, input=js, capture_output=True, text=True, timeout=30)


def _remove_overlay(base_args: list[str]) -> None:
    _run_ab(base_args, "eval", "document.getElementById('demo-overlay')?.remove()")


@dataclass
class TimingEntry:
    """Records when a segment actually started/ended in the video timeline."""

    segment_id: str
    video_start_ms: int
    video_end_ms: int
    audio_duration_ms: int


# Minimum wait after actions complete so the viewer can see the final state
_MIN_HOLD_MS = 500


def dry_run(
    script: Script,
    session_dir: Path,
    *,
    headed: bool = False,
    cdp_port: int | None = None,
    auto_connect: bool = False,
) -> bool:
    """Replay all segment actions without recording, taking a screenshot after
    each segment to verify the script works. Returns True if all pass."""
    base_args: list[str] = []
    if headed:
        base_args.append("--headed")
    if cdp_port:
        base_args.extend(["--cdp", str(cdp_port)])
    if auto_connect:
        base_args.append("--auto-connect")

    shots_dir = session_dir / "dry-run"
    shots_dir.mkdir(parents=True, exist_ok=True)

    all_passed = True
    for segment in script.segments:
        print(f"  Segment: {segment.id}")
        seg_failed = False
        for action in segment.actions:
            try:
                if action.cmd == "eval":
                    cmd = _ab_cmd(base_args, "eval", "--stdin")
                    result = subprocess.run(
                        cmd, input=action.arg, capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0 and (
                        "error" in result.stderr.lower() or "failed" in result.stderr.lower()
                    ):
                        print(f"    FAIL: eval error: {result.stderr.strip()[:200]}")
                        seg_failed = True
                else:
                    _run_ab(base_args, action.cmd, action.arg)
            except RuntimeError as e:
                print(f"    FAIL: {action.cmd} {action.arg} — {e}")
                seg_failed = True

        # Screenshot after each segment for visual verification
        shot_path = str(shots_dir / f"{segment.id}.png")
        try:
            _run_ab(base_args, "screenshot", shot_path)
            print(f"    Screenshot: {shot_path}")
        except RuntimeError:
            print(f"    WARN: screenshot failed")

        # Log URL to catch navigation failures (e.g. stuck on login)
        try:
            url = _run_ab(base_args, "get", "url")
            print(f"    URL: {url}")
        except RuntimeError:
            pass

        status = "FAIL" if seg_failed else "OK"
        print(f"    Result: {status}")
        if seg_failed:
            all_passed = False

    try:
        _run_ab(base_args, "close")
    except RuntimeError:
        pass

    return all_passed


def record_demo(
    script: Script,
    output_path: str,
    *,
    headed: bool = False,
    cdp_port: int | None = None,
    auto_connect: bool = False,
) -> list[TimingEntry]:
    """Record the browser session. Returns a timing manifest for assembly."""
    base_args: list[str] = []
    if headed:
        base_args.append("--headed")
    if cdp_port:
        base_args.extend(["--cdp", str(cdp_port)])
    if auto_connect:
        base_args.append("--auto-connect")

    first_segment = script.segments[0]
    first_open = next((a for a in first_segment.actions if a.cmd == "open"), None)
    if first_open:
        print(f"  Opening {first_open.arg}")
        _run_ab(base_args, "open", first_open.arg)
        _run_ab(base_args, "wait", "--load", "networkidle")

    _run_ab(base_args, "wait", "1000")

    print(f"  Starting recording -> {output_path}")
    _run_ab(base_args, "record", "start", output_path)

    rec_start = time.monotonic()
    manifest: list[TimingEntry] = []

    for segment in script.segments:
        audio_dur = segment.duration_ms or 0
        print(f"  Recording segment: {segment.id} (audio {audio_dur}ms)")

        seg_start = time.monotonic()
        video_start_ms = int((seg_start - rec_start) * 1000)

        if segment.caption_overlay:
            _inject_overlay(base_args, segment.caption_overlay)

        for action in segment.actions:
            if action.cmd == "open" and segment is first_segment and first_open:
                continue
            if action.cmd == "eval":
                cmd = _ab_cmd(base_args, "eval", "--stdin")
                subprocess.run(cmd, input=action.arg, capture_output=True, text=True, timeout=30)
            else:
                _run_ab(base_args, action.cmd, action.arg)

        # Wait for the remaining narration time, minus what actions already consumed
        elapsed_ms = int((time.monotonic() - seg_start) * 1000)
        remaining = max(_MIN_HOLD_MS, audio_dur - elapsed_ms)
        print(f"    Actions took {elapsed_ms}ms, holding {remaining}ms")
        _run_ab(base_args, "wait", str(remaining))

        if segment.caption_overlay:
            _remove_overlay(base_args)

        video_end_ms = int((time.monotonic() - rec_start) * 1000)
        manifest.append(TimingEntry(
            segment_id=segment.id,
            video_start_ms=video_start_ms,
            video_end_ms=video_end_ms,
            audio_duration_ms=audio_dur,
        ))

    _run_ab(base_args, "record", "stop")
    print(f"  Recording saved to {output_path}")
    return manifest


# ---------------------------------------------------------------------------
# Assembly (ffmpeg)
# ---------------------------------------------------------------------------


def _format_srt_time(ms: int) -> str:
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    remainder = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{remainder:03d}"


def _parse_srt_time(t: str) -> int:
    parts = t.replace(",", ":").split(":")
    return int(parts[0]) * 3600000 + int(parts[1]) * 60000 + int(parts[2]) * 1000 + int(parts[3])


def _build_mixed_audio(
    script: Script, manifest: list[TimingEntry], output_dir: Path
) -> Path:
    """Place each segment's audio at its real video-timeline offset.

    Uses ffmpeg adelay + amix so each clip lands at the moment its segment
    actually started in the recording, rather than assuming sequential concat
    lines up.
    """
    inputs: list[str] = []
    filter_parts: list[str] = []
    stream_labels: list[str] = []

    seg_by_id = {s.id: s for s in script.segments}
    input_idx = 0

    for entry in manifest:
        seg = seg_by_id.get(entry.segment_id)
        if not seg or not seg.audio_path:
            continue

        inputs.extend(["-i", seg.audio_path])
        delay_ms = entry.video_start_ms
        label = f"a{input_idx}"
        # adelay: delay in ms, pad to keep the stream alive after the clip ends
        filter_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[{label}]")
        stream_labels.append(f"[{label}]")
        input_idx += 1

    if not stream_labels:
        raise RuntimeError("No audio segments to mix")

    # amix with dropout_transition=0 prevents volume ducking across segments
    mix = "".join(stream_labels) + f"amix=inputs={len(stream_labels)}:dropout_transition=0[out]"
    filter_parts.append(mix)
    filter_graph = ";".join(filter_parts)

    full_audio = output_dir / "narration-synced.wav"
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", filter_graph,
         "-map", "[out]", "-ac", "2", "-ar", "44100", str(full_audio)],
        capture_output=True, text=True, check=True,
    )
    return full_audio


def _build_synced_subtitles(
    script: Script, manifest: list[TimingEntry], output_dir: Path
) -> Path:
    """Offset per-segment SRT cues to their real video-timeline positions."""
    seg_by_id = {s.id: s for s in script.segments}
    cue_index = 1
    output_lines: list[str] = []

    for entry in manifest:
        seg = seg_by_id.get(entry.segment_id)
        if not seg or not seg.srt_path or not seg.duration_ms:
            continue

        srt_path = Path(seg.srt_path)
        if not srt_path.exists():
            continue

        content = srt_path.read_text().strip()
        if not content:
            continue

        offset_ms = entry.video_start_ms

        for block in content.split("\n\n"):
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                start_str, end_str = lines[1].split(" --> ")
                start_ms = _parse_srt_time(start_str.strip()) + offset_ms
                end_ms = _parse_srt_time(end_str.strip()) + offset_ms
                output_lines.append(str(cue_index))
                output_lines.append(
                    f"{_format_srt_time(start_ms)} --> {_format_srt_time(end_ms)}"
                )
                output_lines.append("\n".join(lines[2:]))
                output_lines.append("")
                cue_index += 1

    full_srt = output_dir / "captions-synced.srt"
    full_srt.write_text("\n".join(output_lines))
    return full_srt


def _has_subtitles_filter() -> bool:
    result = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
    return "subtitles" in result.stdout


def _save_manifest(manifest: list[TimingEntry], output_dir: Path) -> Path:
    """Write the timing manifest to JSON for debugging / re-assembly."""
    path = output_dir / "timing-manifest.json"
    data = [
        {
            "segment_id": e.segment_id,
            "video_start_ms": e.video_start_ms,
            "video_end_ms": e.video_end_ms,
            "audio_duration_ms": e.audio_duration_ms,
        }
        for e in manifest
    ]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def assemble_video(
    script: Script,
    video_path: str,
    output_path: str,
    session_dir: Path,
    manifest: list[TimingEntry],
) -> None:
    _save_manifest(manifest, session_dir)

    print("  Mixing audio with per-segment timing offsets...")
    full_audio = _build_mixed_audio(script, manifest, session_dir)

    print("  Building synced subtitle track...")
    full_srt = _build_synced_subtitles(script, manifest, session_dir)

    print(f"  Assembling final video -> {output_path}")

    has_subs = _has_subtitles_filter()
    if not has_subs:
        print("  Note: ffmpeg lacks libass — embedding subtitles as soft track")

    if has_subs:
        subtitle_style = (
            "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BackColour=&H80000000,"
            "BorderStyle=4,Outline=1,Shadow=0,MarginV=40"
        )
        srt_escaped = (
            str(full_srt.resolve())
            .replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        vf = f"subtitles={srt_escaped}:force_style='{subtitle_style}'"
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-i", str(full_audio), "-vf", vf,
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k", "-shortest", output_path],
            check=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-i", str(full_audio), "-i", str(full_srt),
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text",
             "-metadata:s:s:0", "language=eng", "-shortest", output_path],
            check=True,
        )

    print(f"  Final video: {output_path}")
    if not has_subs:
        print("  Tip: brew install ffmpeg --with-libass for burned-in subtitles")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_pipeline(
    script_path: str,
    output_path: str = "demo.mp4",
    *,
    voice_override: str | None = None,
    session_dir: str | None = None,
    skip_narration: bool = False,
    skip_recording: bool = False,
    headed: bool = False,
    cdp_port: int | None = None,
    auto_connect: bool = False,
    dry_run_only: bool = False,
) -> None:
    script = Script.load(script_path)
    if voice_override:
        script.voice = voice_override

    if session_dir:
        work_dir = Path(session_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="agent-screencast-"))

    print(f"Session directory: {work_dir}")

    if dry_run_only:
        print("\n[dry-run] Validating script actions...")
        passed = dry_run(
            script, work_dir, headed=headed, cdp_port=cdp_port, auto_connect=auto_connect
        )
        if passed:
            print("\n[dry-run] All segments passed. Screenshots in: "
                  f"{work_dir / 'dry-run'}")
        else:
            print("\n[dry-run] Some segments FAILED. Review screenshots in: "
                  f"{work_dir / 'dry-run'}")
            sys.exit(1)
        return

    raw_video = str(work_dir / "demo-raw.webm")

    if not skip_narration:
        print("\n[1/3] Generating narration...")
        script = generate_narration(script, work_dir)
    else:
        enriched = work_dir / "script-enriched.json"
        if enriched.exists():
            script = Script.load(enriched)
            print("Loaded existing narration from enriched script.")
        else:
            raise FileNotFoundError(
                f"--skip-narration requires {enriched} to exist. Run narration first."
            )

    if not skip_recording:
        print("\n[2/3] Recording browser session...")
        manifest = record_demo(
            script, raw_video, headed=headed, cdp_port=cdp_port, auto_connect=auto_connect
        )
    else:
        if not Path(raw_video).exists():
            raise FileNotFoundError(
                f"--skip-recording requires {raw_video} to exist. Run recording first."
            )
        print("Reusing existing recording.")
        # Load the real timing manifest saved during the original recording.
        # Falling back to audio-duration estimates only if no manifest exists.
        manifest_path = work_dir / "timing-manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest_data = json.load(f)
            manifest = [
                TimingEntry(
                    segment_id=e["segment_id"],
                    video_start_ms=e["video_start_ms"],
                    video_end_ms=e["video_end_ms"],
                    audio_duration_ms=e["audio_duration_ms"],
                )
                for e in manifest_data
            ]
            print(f"  Loaded timing manifest from {manifest_path}")
        else:
            print("  WARNING: No timing manifest found — using audio-duration estimates.")
            print("  Audio/subtitle sync may be inaccurate. Re-record for precise timing.")
            offset = 0
            manifest = []
            for seg in script.segments:
                dur = seg.duration_ms or 0
                manifest.append(TimingEntry(
                    segment_id=seg.id,
                    video_start_ms=offset,
                    video_end_ms=offset + dur,
                    audio_duration_ms=dur,
                ))
                offset += dur

    print("\n[3/3] Assembling final video...")
    assemble_video(script, raw_video, output_path, work_dir, manifest)
    print(f"\nDone! Output: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="agent-screencast",
        description="Record narrated, captioned video demos of web applications.",
    )
    parser.add_argument("script", help="Path to segment script JSON file")
    parser.add_argument("-o", "--output", default="demo.mp4", help="Output MP4 path")
    parser.add_argument("--voice", default=None, help="Override TTS voice")
    parser.add_argument("--session-dir", default=None, help="Working directory for intermediate files")
    parser.add_argument("--skip-narration", action="store_true", help="Reuse existing audio")
    parser.add_argument("--skip-recording", action="store_true", help="Reuse existing video")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    parser.add_argument("--cdp", type=int, default=None, help="Connect to Chrome via CDP port")
    parser.add_argument("--auto-connect", action="store_true", help="Auto-discover running Chrome")
    parser.add_argument("--dry-run", action="store_true", help="Validate script actions without recording (takes screenshots per segment)")

    args = parser.parse_args()

    try:
        run_pipeline(
            script_path=args.script,
            output_path=args.output,
            voice_override=args.voice,
            session_dir=args.session_dir,
            skip_narration=args.skip_narration,
            skip_recording=args.skip_recording,
            headed=args.headed,
            cdp_port=args.cdp,
            auto_connect=args.auto_connect,
            dry_run_only=args.dry_run,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
