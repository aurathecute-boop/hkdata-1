"""Guards the skill's discoverability.

The agent runtime discovers skills by globbing ``{*.md,**/SKILL.md}``
**recursively** under every skill root — following symlinks — and stores the
results in a map keyed by the *parent directory's name*. The last file scanned
wins, so a second ``SKILL.md`` inside a directory also called ``hkdata`` (a
stale clone, a fixture, a vendored package) silently replaces the real skill:
the agent then reads an outdated ``SKILL.md`` and never sees the program
library.

These tests keep that from happening.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Trees that are not part of the published skill (regenerated, vendored, or
#: tool-managed). A SKILL.md inside them is not ours to police — but it still
#: must not claim this skill's runtime id.
VENDORED = {".git", ".venv", "node_modules", ".cache", ".pytest_cache"}


def _skill_files(include_vendored=False):
    """Yield every ``SKILL.md`` under the repo, as ``(path, runtime_id)``.

    ``runtime_id`` mirrors the runtime's rule: the name of the directory that
    holds the file.
    """
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = Path(dirpath).relative_to(ROOT)
        top = rel.parts[0] if rel.parts else ""
        if top == ".git":
            dirnames[:] = []
            continue
        if top in VENDORED:
            if not include_vendored:
                dirnames[:] = []
                continue
        if "SKILL.md" in filenames:
            yield Path(dirpath), Path(dirpath).name


def test_root_skill_is_the_only_discoverable_skill():
    """No stray SKILL.md may sit inside the published skill tree."""
    found = sorted(path for path, _ in _skill_files())
    assert found == [ROOT], (
        "a second SKILL.md inside the repo is discovered by the agent runtime "
        f"and can replace the real skill — remove it: {found}"
    )


def test_skill_id_is_unique_in_the_repo():
    """Nothing inside the repo may claim this skill's runtime id."""
    mine = ROOT.name
    claimants = sorted(
        str(path) for path, skill_id in _skill_files(include_vendored=True)
        if skill_id == mine
    )
    assert claimants == [str(ROOT)], (
        f"a nested directory named {mine!r} carries its own SKILL.md and "
        f"collides with this skill's runtime id: {claimants}"
    )


def test_skill_md_resolves_skill_dir():
    """SKILL.md must define $SKILL_DIR — every command in it depends on it."""
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "SKILL_DIR" in content, "SKILL.md never mentions $SKILL_DIR"
    assert "HKDATA_SKILL_DIR" in content, (
        "SKILL.md must ship a $SKILL_DIR resolver (HKDATA_SKILL_DIR override "
        "plus the standard install locations) — otherwise every documented "
        "command runs against an unset variable"
    )


def test_skill_md_documents_the_program_library():
    """The runtime entrypoint must expose the two-path contract."""
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for needle in ("programs-search", "catalog-search", "reindex", "hk.sh"):
        assert needle in content, f"SKILL.md lost the {needle!r} reference"
