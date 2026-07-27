"""Structural tests for the Registrar (validate) composite action (ADR-058).

The action is a thin wrapper over `decided validate --sarif`; its behaviour is owned
by the (separately tested) CLI. These tests pin the action's *contract* — that it
stays a composite action that runs `decided validate --sarif`, uploads SARIF, and
re-surfaces the CLI exit code — so the wiring cannot silently drift.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ACTION = Path(__file__).parent.parent / "registrar" / "github" / "action.yml"


def _action() -> dict:
    return yaml.safe_load(ACTION.read_text(encoding="utf-8"))


def test_action_is_composite():
    a = _action()
    assert a["runs"]["using"] == "composite"
    assert a["name"] == "As Decided Registrar"


def test_action_declares_expected_inputs():
    inputs = _action()["inputs"]
    for name in ("path", "upload-sarif", "sarif-file", "asdecided-version"):
        assert name in inputs, f"missing input: {name}"
    assert inputs["path"]["default"] == "decisions"
    assert inputs["upload-sarif"]["default"] == "true"


def test_action_runs_rac_validate_sarif():
    steps = _action()["runs"]["steps"]
    run_steps = " ".join(s.get("run", "") for s in steps)
    assert "decided validate" in run_steps
    assert "--sarif" in run_steps


def test_action_uploads_sarif():
    steps = _action()["runs"]["steps"]
    uploads = [s for s in steps if "upload-sarif" in str(s.get("uses", ""))]
    assert uploads, "no SARIF upload step"
    # Upload even on failure so findings still annotate the PR.
    assert "always()" in uploads[0]["if"]


def test_action_resurfaces_exit_code():
    steps = _action()["runs"]["steps"]
    run_steps = " ".join(s.get("run", "") for s in steps)
    assert 'exit "$EXIT_CODE"' in run_steps


def test_action_installs_verified_native_engine():
    run_steps = " ".join(s.get("run", "") for s in _action()["runs"]["steps"])
    assert "shared/install-native.sh" in run_steps
    assert "pip install" not in run_steps
    assert _action()["inputs"]["asdecided-version"]["default"] == "0.24.0"
