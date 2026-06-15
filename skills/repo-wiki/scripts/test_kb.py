"""Tests for kb.py fixes — run with: python3 -m pytest skills/repo-wiki/scripts/test_kb.py"""
import json
import sys
import types
import textwrap
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Bootstrap: add scripts dir to sys.path so we can import kb without installing.
# ---------------------------------------------------------------------------
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import kb  # noqa: E402  (after sys.path fixup)


# ===========================================================================
# Helpers
# ===========================================================================

def _fake_head_sha(root):  # noqa: D401
    return "abc1234"


def _run_verify(tmp_path, page_rel, page_content, note=None):
    """Write a page into a fake wiki, run cmd_verify on it, return updated text."""
    wiki = tmp_path / "repo-wiki"
    wiki.mkdir()
    page = wiki / page_rel
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(page_content, encoding="utf-8")

    args = MagicMock()
    args.wiki = str(wiki)
    args.page = page_rel
    args.note = note

    with patch.object(kb, "repo_root", return_value=tmp_path), \
         patch.object(kb, "head_sha", side_effect=_fake_head_sha), \
         patch.object(kb, "load_surfaced", return_value={}), \
         patch.object(kb, "save_surfaced", return_value=None):
        kb.cmd_verify(args)

    return page.read_text(encoding="utf-8")


# ===========================================================================
# Blocker test — BLOCKER fix #1
# ===========================================================================

class TestCmdVerifyMalformedFrontmatter:
    """Page with unclosed frontmatter (--- ... but no closing ---).

    After kb verify:
    - Original content lines are still present (not dropped).
    - A valid leading frontmatter block with verified_against exists.
    """

    def test_unclosed_frontmatter_preserves_original_content(self, tmp_path):
        # A page that opens with --- but has no closing --- — malformed.
        page_content = "---\ntitle: x\n## Body\nSome content here.\n"
        result = _run_verify(tmp_path, "page.md", page_content)

        # Must still contain the original lines.
        assert "title: x" in result, "original frontmatter key must be preserved"
        assert "## Body" in result, "original body heading must be preserved"
        assert "Some content here." in result, "original body text must be preserved"

        # Must have a valid leading frontmatter block with verified_against.
        assert result.startswith("---\n"), "result must start with frontmatter fence"
        first_close = result.find("\n---", 3)
        assert first_close != -1, "result must have a closing --- for the new frontmatter"
        fm_content = result[3:first_close]
        assert "verified_against: abc1234" in fm_content, \
            "new frontmatter must contain verified_against"

    def test_unclosed_frontmatter_no_parse_ambiguity(self, tmp_path):
        """The new frontmatter block must be valid (complete) and the original text kept as body.

        The old bug would produce:
          ---\\nverified_against: ...\\n---\\n---\\ntitle: x\\n...
        meaning parse_frontmatter could see the original --- as a new fence, silently
        losing `title: x`.  The fix separates with a blank line so the only complete
        frontmatter block is the new one.
        """
        page_content = "---\ntitle: x\n## Body\n"
        result = _run_verify(tmp_path, "page.md", page_content)

        # The leading frontmatter must be complete (exactly one open+close pair at top).
        assert result.startswith("---\n"), "must start with frontmatter open"
        first_close_pos = result.find("\n---", 3)
        assert first_close_pos != -1, "must have a closing --- for the new frontmatter"

        # After the first closing --- there must be a blank separator before original content
        # (not another immediate --- that would form a valid but confusing frontmatter).
        after_close = result[first_close_pos + 4:]  # text after "\n---"
        assert after_close.startswith("\n\n"), \
            "a blank line must separate new frontmatter from the original body"

        # The original content still follows the blank line.
        assert "title: x" in after_close
        assert "## Body" in after_close


class TestCmdVerifyWellFormedFrontmatterRegression:
    """Normal well-formed page → verify still works as before."""

    def test_bumps_verified_against(self, tmp_path):
        page_content = textwrap.dedent("""\
            ---
            title: foo
            verified_against: oldhash
            ---

            ## Body
            Content.
        """)
        result = _run_verify(tmp_path, "page.md", page_content)
        assert "verified_against: abc1234" in result
        assert "oldhash" not in result

    def test_prepends_timeline_entry(self, tmp_path):
        page_content = textwrap.dedent("""\
            ---
            title: bar
            ---

            ## Timeline
            - 2025-01-01 — old entry
        """)
        result = _run_verify(tmp_path, "page.md", page_content)
        # New entry should appear before the old one.
        new_pos = result.index("re-verified @abc1234")
        old_pos = result.index("old entry")
        assert new_pos < old_pos, "new Timeline entry should precede old entries"

    def test_no_frontmatter_gets_prepended(self, tmp_path):
        page_content = "# Just a heading\nSome text.\n"
        result = _run_verify(tmp_path, "page.md", page_content)
        assert result.startswith("---\nverified_against: abc1234\n---\n")
        assert "# Just a heading" in result


# ===========================================================================
# Fix #2 — save_surfaced is now atomic
# ===========================================================================

class TestSaveSurfacedAtomic:
    def test_uses_temp_replace(self, tmp_path):
        """Verify that save_surfaced writes via a temp file (atomic swap)."""
        data = {"some|key": True}

        replaced_paths = []
        original_replace = Path.replace

        def spy_replace(self, target):
            replaced_paths.append((str(self), str(target)))
            return original_replace(self, target)

        with patch.object(Path, "replace", spy_replace), \
             patch.object(kb, "surfaced_path", return_value=tmp_path / ".kb" / "surfaced.json"):
            kb.save_surfaced(tmp_path, data)

        assert replaced_paths, "Path.replace must have been called (atomic swap)"
        _, dest = replaced_paths[0]
        assert dest.endswith("surfaced.json"), "destination must be the surfaced.json path"

    def test_written_content_is_correct(self, tmp_path):
        data = {"page|sha": True}
        with patch.object(kb, "surfaced_path", return_value=tmp_path / "surfaced.json"):
            kb.save_surfaced(tmp_path, data)
        written = json.loads((tmp_path / "surfaced.json").read_text(encoding="utf-8"))
        assert written == data


# ===========================================================================
# Fix #3 — count_uningested_chat_sessions drops dangling IDs
# ===========================================================================

class TestCountUningestedDropsDanglingId:
    def test_dangling_id_is_dropped(self, tmp_path):
        """An ID: line with no following File: line must not appear in count."""
        recall_output = textwrap.dedent("""\
            [1] 2026-06-15 | slug | title [claude]
                /path/to/project
                ID: dangling-id-no-file

            [2] 2026-06-14 | slug2 | title2 [claude]
                /path/to/project
                ID: real-id-001
                File: /Users/me/projects/slug2/abc.jsonl
        """)
        # Patch RECALL to exist and subprocess.run to return our fake output.
        fake_recall = tmp_path / "recall.py"
        fake_recall.write_text("# stub", encoding="utf-8")

        with patch.object(kb, "RECALL", fake_recall), \
             patch.object(kb, "load_watermark", return_value={}), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=recall_output)
            count = kb.count_uningested_chat_sessions(tmp_path)

        # dangling-id-no-file should be dropped; only real-id-001 counted.
        assert count == 1, f"expected 1, got {count}"


# ===========================================================================
# Fix #4 — install_post_commit_hook idempotency
# ===========================================================================

class TestInstallPostCommitHookIdempotency:
    def _make_hook_dir(self, tmp_path):
        hooks_dir = tmp_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)
        return hooks_dir

    def _patch_git_cmd(self, tmp_path):
        """Patch git() to return the .git/hooks path."""
        hooks_path = str(tmp_path / ".git" / "hooks")
        return patch.object(kb, "git", return_value=(hooks_path, 0))

    def test_adds_line_when_only_kbpy_and_postcommit_present_but_not_repowiki(self, tmp_path):
        """Existing hook has 'kb.py' and 'post-commit' but not 'repo-wiki' → add our line."""
        hooks_dir = self._make_hook_dir(tmp_path)
        hook_file = hooks_dir / "post-commit"
        # User's hook that happens to mention kb.py and post-commit but is NOT ours.
        hook_file.write_text("#!/bin/sh\n# this references kb.py and post-commit somehow\n",
                              encoding="utf-8")
        hook_file.chmod(0o755)

        with self._patch_git_cmd(tmp_path):
            added = kb.install_post_commit_hook(tmp_path)

        assert added is True, "should have added our line"
        content = hook_file.read_text(encoding="utf-8")
        assert "repo-wiki" in content, "our hook line (with repo-wiki path) should now be present"

    def test_skips_when_our_line_already_present(self, tmp_path):
        """Running init twice must not duplicate our hook line."""
        hooks_dir = self._make_hook_dir(tmp_path)

        with self._patch_git_cmd(tmp_path):
            kb.install_post_commit_hook(tmp_path)  # first install
            content_after_first = (hooks_dir / "post-commit").read_text(encoding="utf-8")
            kb.install_post_commit_hook(tmp_path)  # second install
            content_after_second = (hooks_dir / "post-commit").read_text(encoding="utf-8")

        assert content_after_first == content_after_second, \
            "second install must not change the hook file"
