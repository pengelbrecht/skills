"""End-to-end pipeline orchestrator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from agent_screencast.assembly import assemble_video
from agent_screencast.models import Script
from agent_screencast.narration import generate_narration
from agent_screencast.recorder import record_demo


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
) -> None:
    """Run the full agent-screencast pipeline."""
    # Load script
    script = Script.load(script_path)
    if voice_override:
        script.voice = voice_override

    # Set up session directory
    if session_dir:
        work_dir = Path(session_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="agent-screencast-"))

    print(f"Session directory: {work_dir}")
    raw_video = str(work_dir / "demo-raw.webm")

    # Phase 1 & 2: Generate narration audio + SRT
    if not skip_narration:
        print("\n[1/3] Generating narration...")
        script = generate_narration(script, work_dir)
    else:
        # Load enriched script if skipping narration
        enriched = work_dir / "script-enriched.json"
        if enriched.exists():
            script = Script.load(enriched)
            print("Loaded existing narration from enriched script.")
        else:
            raise FileNotFoundError(
                f"--skip-narration requires {enriched} to exist. Run narration first."
            )

    # Phase 3: Record browser session
    if not skip_recording:
        print("\n[2/3] Recording browser session...")
        record_demo(
            script,
            raw_video,
            headed=headed,
            cdp_port=cdp_port,
            auto_connect=auto_connect,
        )
    else:
        if not Path(raw_video).exists():
            raise FileNotFoundError(
                f"--skip-recording requires {raw_video} to exist. Run recording first."
            )
        print("Reusing existing recording.")

    # Phase 4: Assemble final video
    print("\n[3/3] Assembling final video...")
    assemble_video(script, raw_video, output_path, work_dir)

    print(f"\nDone! Output: {output_path}")
