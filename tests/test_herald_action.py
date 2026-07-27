"""Structural tests for the native As Decided Herald action.

The action is a thin wrapper (ADR-063) over `decided herald`: compute
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
    assert a["name"] == "As Decided Herald"


def test_action_declares_exactly_expected_inputs():
    inputs = _action()["inputs"]
    assert set(inputs) == {"path", "max-inline", "asdecided-version"}
    assert inputs["path"]["default"] == "decisions"
    assert inputs["max-inline"]["default"] == "5"


def test_action_installs_verified_native_engine():
    run_steps = " ".join(s.get("run", "") for s in _action()["runs"]["steps"])
    assert "shared/install-native.sh" in run_steps
    assert "pip install" not in run_steps
    assert _action()["inputs"]["asdecided-version"]["default"] == "0.24.0"


def test_action_diffs_from_the_merge_base():
    diff = _step("Compute changed paths")["run"]
    # Triple-dot: what the PR itself changes, even when base has moved ahead.
    assert '"$BASE_SHA...$HEAD_SHA"' in diff
    assert "pull_request events only" in diff


def test_action_delegates_rendering_to_native_engine():
    render = _step("Render governing decisions")["run"]
    assert "decided herald" in render
    assert "--github-output" in render
    assert "python" not in render
    assert not (ACTION.parent / "render.py").exists()


def test_action_comment_step_updates_in_place_and_never_gates():
    script = _step("Post or update the comment")["with"]["script"]
    assert "lore-decisions-on-pr" in script  # the update-in-place marker
    assert "updateComment" in script
    assert "createComment" in script
    # Advisory surfaces never fail the check: a read-only token degrades to
    # the step summary with a warning.
    assert "core.warning" in script
    assert "core.summary" in script
