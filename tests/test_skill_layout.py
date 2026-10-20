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


def test_skill_md_answers_before_it_remembers():
    """The program write must not sit between the user and the answer.

    Writing a program is a speculative investment: it pays off on the *next*
    question, so it goes last. A silent reordering back to write-then-answer
    puts minutes of authoring in front of a five-second answer.
    """
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    path_b = content[content.index("### Path B"):]
    path_b = path_b[:path_b.index("\n## ", 1)] if "\n## " in path_b else path_b

    answer_at = path_b.index("**Answer now**")
    remember_at = path_b.index("**Remember**")
    assert answer_at < remember_at, (
        "Path B must answer before it writes the program "
        f"(answer at {answer_at}, remember at {remember_at})"
    )
    assert "never waits" in path_b, (
        "Path B must state that the answer does not wait for the program write"
    )


def test_agents_md_keeps_the_delegation_order():
    """A delegated agent must not invert discover → answer → remember."""
    content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    section = content[content.index("## Subagent delegation"):]
    section = section[:section.index("\n## ", 1)]
    assert "Answer first" in section, (
        "the delegation rule must keep the answer ahead of the program write"
    )
