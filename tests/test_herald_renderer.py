"""Behavioral battery for the Herald renderer (`herald/github/render.py`).

Unlike the structural action-contract tests, these exercise the real published
engine: build a tiny corpus, shell `render.py` (which shells
`rac decisions-for --json` per changed path — the same contract the wrapper
consumes in the field, ADR-063), and pin the rendered comment. Facts, never
verdicts (ADR-034): governed and ungoverned diffs both exit 0, and the same
corpus and diff must render byte-identical output.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RENDER = Path(__file__).parent.parent / "herald" / "github" / "render.py"

# The `rac` console script installed alongside the interpreter running pytest.
RAC_BIN = Path(sys.executable).parent / "rac"

LINK_BASE = "https://example.com/blob/HEAD"


def _write_decision(repo: Path, stem: str, number: int, title: str, scope: str) -> None:
    path = repo / "rac" / "decisions" / f"{stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
schema_version: 1
id: ACT-{number:04d}
type: decision
---
# {title}

## Context

Recorded for the Herald renderer battery.

## Decision

{title}.

## Consequences

The scope below is governed.

## Status

Accepted

## Applies To

- {scope}
""",
        encoding="utf-8",
    )


def _make_repo(tmp_path: Path, scopes: dict[str, str]) -> Path:
    """A tmp repository: `.rac/config.yaml` plus one decision per scope."""
    repo = tmp_path / "repo"
    (repo / ".rac").mkdir(parents=True)
    (repo / ".rac" / "config.yaml").write_text(
        "repository_key: ACT\n", encoding="utf-8"
    )
    for number, (stem, scope) in enumerate(sorted(scopes.items()), start=1):
        _write_decision(repo, stem, number, stem.replace("-", " ").title(), scope)
    return repo


def _render(
    repo: Path, changed_paths: list[str], max_inline: int = 5
) -> tuple[subprocess.CompletedProcess, str]:
    paths_file = repo / "changed-paths.txt"
    paths_file.write_text("".join(f"{p}\n" for p in changed_paths), encoding="utf-8")
    out = repo / "comment.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(RENDER),
            "--corpus",
            "rac",
            "--paths-file",
            str(paths_file),
            "--link-base",
            LINK_BASE,
            "--max-inline",
            str(max_inline),
            "--out",
            str(out),
            "--rac-bin",
            str(RAC_BIN),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return proc, out.read_text(encoding="utf-8")


def test_governing_decisions_render_sorted_and_deduplicated(tmp_path):
    repo = _make_repo(
        tmp_path,
        {"alpha-rule": "src/**/*.py", "beta-rule": "docs/**"},
    )
    proc, body = _render(repo, ["src/app.py", "src/pkg/util.py", "docs/guide.md"])
    assert "2 governing decision(s)" in proc.stdout
    # One bullet per decision, sorted by id, however many changed paths matched.
    assert body.count("- **[alpha-rule") == 1
    assert body.index("alpha-rule") < body.index("beta-rule")
    assert "applies to `src/**/*.py`" in body
    assert f"[alpha-rule — Alpha Rule]({LINK_BASE}/rac/decisions/alpha-rule.md)" in body
    assert "`src/app.py`, `src/pkg/util.py`" in body


def test_ungoverned_diff_renders_the_empty_state(tmp_path):
    repo = _make_repo(tmp_path, {"alpha-rule": "src/**/*.py"})
    proc, body = _render(repo, ["README.md"])
    assert "No recorded decisions govern" in body
    assert "has_decisions=false" in proc.stdout


def test_a_bad_changed_path_does_not_take_down_the_comment(tmp_path):
    repo = _make_repo(tmp_path, {"alpha-rule": "src/**/*.py"})
    proc, body = _render(repo, ["no/such/file.py", "src/app.py"])
    assert proc.returncode == 0
    assert "alpha-rule" in body


def test_overflow_collapses_into_a_details_expander(tmp_path):
    repo = _make_repo(
        tmp_path,
        {
            "alpha-rule": "src/**/*.py",
            "beta-rule": "docs/**",
            "gamma-rule": "tools/**",
        },
    )
    _, body = _render(
        repo, ["src/app.py", "docs/guide.md", "tools/run.sh"], max_inline=2
    )
    assert "<details><summary>1 more governing decision</summary>" in body
    assert body.index("gamma-rule") > body.index("<details>")


def test_rendering_is_byte_deterministic(tmp_path):
    scopes = {"alpha-rule": "src/**/*.py", "beta-rule": "docs/**"}
    changed = ["src/app.py", "docs/guide.md", "src/pkg/util.py"]
    _, forward = _render(_make_repo(tmp_path / "a", scopes), changed)
    _, backward = _render(_make_repo(tmp_path / "b", scopes), list(reversed(changed)))
    assert forward == backward
