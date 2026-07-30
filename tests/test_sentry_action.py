from pathlib import Path

import yaml


ACTION = Path(__file__).parent.parent / "sentry" / "github" / "action.yml"


def action() -> dict:
    return yaml.safe_load(ACTION.read_text(encoding="utf-8"))


def test_sentry_is_thin_native_composite():
    manifest = action()
    assert manifest["runs"]["using"] == "composite"
    commands = " ".join(step.get("run", "") for step in manifest["runs"]["steps"])
    assert "decided sentry" in commands
    assert "--sarif" in commands
    assert "python" not in commands
    assert "pip install" not in commands


def test_sentry_supports_diff_and_full_tree_modes():
    inputs = action()["inputs"]
    assert inputs["base"]["default"] == ""
    assert inputs["full"]["default"] == "false"
    assert inputs["asdecided-version"]["default"] == "0.26.0"
    commands = " ".join(step.get("run", "") for step in action()["runs"]["steps"])
    assert "--full" in commands
    assert '--base "$BASE"' in commands
    assert "$SENTRY_MODE" not in commands
    assert "$GITHUB_ENV" not in commands


def test_sentry_uploads_one_sarif_and_resurfaces_exit():
    steps = action()["runs"]["steps"]
    uploads = [step for step in steps if "upload-sarif" in str(step.get("uses", ""))]
    assert len(uploads) == 1
    assert uploads[0]["with"]["category"] == "asdecided-sentry"
    commands = " ".join(step.get("run", "") for step in steps)
    assert 'exit "$EXIT_CODE"' in commands
