"""CLI entry point for agent-screencast."""

from __future__ import annotations

import argparse
import sys

from agent_screencast.pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="agent-screencast",
        description="Record narrated, captioned video demos of web applications.",
    )
    parser.add_argument("script", help="Path to segment script JSON file")
    parser.add_argument("-o", "--output", default="demo.mp4", help="Output MP4 path")
    parser.add_argument("--voice", default=None, help="Override TTS voice (e.g. en-US-GuyNeural)")
    parser.add_argument(
        "--session-dir", default=None, help="Working directory for intermediate files"
    )
    parser.add_argument(
        "--skip-narration", action="store_true", help="Skip TTS generation (reuse existing audio)"
    )
    parser.add_argument(
        "--skip-recording",
        action="store_true",
        help="Skip browser recording (reuse existing video)",
    )
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    parser.add_argument(
        "--cdp", type=int, default=None, help="Connect to existing Chrome via CDP port"
    )
    parser.add_argument(
        "--auto-connect", action="store_true", help="Auto-discover running Chrome instance"
    )

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
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0
