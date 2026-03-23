.PHONY: dev lint format test demo check-deps

dev:
	uv sync --all-groups

lint:
	uv run ruff format --check . && uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

check-deps:
	@which agent-browser > /dev/null || (echo "MISSING: npm i -g agent-browser && agent-browser install" && exit 1)
	@uv run edge-tts --version > /dev/null 2>&1 || (echo "MISSING: uv add edge-tts" && exit 1)
	@which ffmpeg > /dev/null || (echo "MISSING: brew install ffmpeg" && exit 1)
	@echo "All dependencies available."

# Record the sample Hacker News demo (headless, agent-browser's own Chromium)
demo: check-deps
	uv run agent-screencast samples/hackernews.json -o demo-hackernews.mp4 --session-dir ./session

# Record using your running Chrome instance
demo-cdp: check-deps
	uv run agent-screencast samples/hackernews.json -o demo-hackernews.mp4 --session-dir ./session --auto-connect

# Record with visible browser
demo-headed: check-deps
	uv run agent-screencast samples/hackernews.json -o demo-hackernews.mp4 --session-dir ./session --headed
