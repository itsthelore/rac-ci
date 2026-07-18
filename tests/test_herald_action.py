"""Structural tests for the Lore decisions-on-PR (Herald) composite action.

The action is a thin wrapper (ADR-063) over `rac decisions-for --json`: compute
the PR's merge-base diff, render one deterministic advisory comment, and post it
update-in-place. Matching and liveness are the engine's; these tests pin the
action's *contract* — inputs, the triple-dot diff, the renderer hand-off, and
the never-gate comment step — so the wiring cannot silently drift.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ACTION = Path(__file__).parent.parent / "herald" / "github" / "action.yml"


def _action() -> dict:
    return yaml.safe_load(ACTION.read_text(encoding="utf-8"))


def _step(name_fragment: str) -> dict:
    for step in _action()["runs"]["steps"]:
        if name_fragment in step.get("name", ""):
            return step
    raise AssertionError(f"no step named like {name_fragment!r}")


def test_action_is_composite():
    a = _action()
    assert a["runs"]["using"] == "composite"
    assert a["name"] == "Lore decisions on PR"


def test_action_declares_exactly_expected_inputs():
    inputs = _action()["inputs"]
    assert set(inputs) == {"path", "max-inline", "rac-version"}
    assert inputs["path"]["default"] == "rac"
    assert inputs["max-inline"]["default"] == "5"


def test_action_installs_published_rac_core():
    # Published engine only (pinned via rac-version, else latest); no
    # source-install mode reaching outside the action directory.
    run_steps = " ".join(s.get("run", "") for s in _action()["runs"]["steps"])
    assert "rac-core" in run_steps
    assert "GITHUB_ACTION_PATH/.." not in run_steps


def test_action_diffs_from_the_merge_base():
    diff = _step("Compute changed paths")["run"]
    # Triple-dot: what the PR itself changes, even when base has moved ahead.
    assert '"$BASE_SHA...$HEAD_SHA"' in diff
    assert "pull_request events only" in diff


def test_action_delegates_rendering_to_render_py():
    render = _step("Render governing decisions")["run"]
    assert "$GITHUB_ACTION_PATH/render.py" in render
    assert (ACTION.parent / "render.py").is_file()


def test_action_comment_step_updates_in_place_and_never_gates():
    script = _step("Post or update the comment")["with"]["script"]
    assert "lore-decisions-on-pr" in script  # the update-in-place marker
    assert "updateComment" in script
    assert "createComment" in script
    # Advisory surfaces never fail the check: a read-only token degrades to
    # the step summary with a warning.
    assert "core.warning" in script
    assert "core.summary" in script
