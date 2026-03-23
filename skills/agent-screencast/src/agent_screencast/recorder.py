"""Browser recording synced to narration timing using agent-browser."""

from __future__ import annotations

import json
import shlex
import subprocess

from agent_screencast.models import Script


def _ab_cmd(base_args: list[str], *args: str) -> list[str]:
    """Build an agent-browser command with base args."""
    return ["agent-browser", *base_args, *args]


def _run_ab(base_args: list[str], *args: str) -> str:
    """Run an agent-browser command and return stdout.

    Args are split on whitespace so that JSON actions like
    {"cmd": "wait", "arg": "--load networkidle"} work correctly.
    """
    # Use shlex to split args that contain spaces, preserving quoted strings
    # e.g. 'text "comments" click' -> ['text', 'comments', 'click']
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
        # Some agent-browser commands return non-zero but still succeed
        if "error" in stderr.lower() or "failed" in stderr.lower():
            raise RuntimeError(
                f"agent-browser failed: {' '.join(cmd)}\nstderr: {stderr}\nstdout: {stdout}"
            )
    return result.stdout.strip()


def _inject_overlay(base_args: list[str], text: str) -> None:
    """Inject a floating caption overlay into the page."""
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
    """Remove the caption overlay."""
    _run_ab(base_args, "eval", "document.getElementById('demo-overlay')?.remove()")


def record_demo(
    script: Script,
    output_path: str,
    *,
    headed: bool = False,
    cdp_port: int | None = None,
    auto_connect: bool = False,
) -> None:
    """Record the browser session synced to narration durations."""
    # Build base agent-browser args
    base_args: list[str] = []
    if headed:
        base_args.append("--headed")
    if cdp_port:
        base_args.extend(["--cdp", str(cdp_port)])
    if auto_connect:
        base_args.append("--auto-connect")

    # Navigate to the first page
    first_segment = script.segments[0]
    first_open = next(
        (a for a in first_segment.actions if a.cmd == "open"),
        None,
    )
    if first_open:
        print(f"  Opening {first_open.arg}")
        _run_ab(base_args, "open", first_open.arg)
        _run_ab(base_args, "wait", "--load", "networkidle")

    # Brief pause before recording starts
    _run_ab(base_args, "wait", "1000")

    # Start recording
    print(f"  Starting recording -> {output_path}")
    _run_ab(base_args, "record", "start", output_path)

    for segment in script.segments:
        print(f"  Recording segment: {segment.id} ({segment.duration_ms}ms)")

        # Inject caption overlay if specified
        if segment.caption_overlay:
            _inject_overlay(base_args, segment.caption_overlay)

        # Execute browser actions
        for action in segment.actions:
            # Skip the initial 'open' if it's the first segment (already opened)
            if action.cmd == "open" and segment is first_segment and first_open:
                continue
            # Route eval through --stdin to avoid shell quoting issues with JS
            if action.cmd == "eval":
                cmd = _ab_cmd(base_args, "eval", "--stdin")
                subprocess.run(
                    cmd, input=action.arg, capture_output=True, text=True, timeout=30
                )
            else:
                _run_ab(base_args, action.cmd, action.arg)

        # Wait for the narration duration
        if segment.duration_ms:
            _run_ab(base_args, "wait", str(segment.duration_ms))

        # Remove overlay
        if segment.caption_overlay:
            _remove_overlay(base_args)

    # Stop recording
    _run_ab(base_args, "record", "stop")
    print(f"  Recording saved to {output_path}")
