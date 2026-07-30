import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parent.parent


def test_manifest_names_all_six_capabilities():
    manifest = json.loads(
        (ROOT / "distribution" / "actions.json").read_text(encoding="utf-8")
    )
    assert [entry["name"] for entry in manifest["facades"]] == [
        "gatekeeper",
        "herald",
        "recordkeeper",
        "registrar",
        "watchkeeper",
        "sentry",
    ]


def test_packager_emits_root_actions_with_facade_relative_installer(tmp_path):
    output = tmp_path / "facades"
    subprocess.run(
        ["bash", str(ROOT / "scripts" / "package-facades.sh"), str(output)],
        cwd=ROOT,
        check=True,
    )
    assert sorted(path.name for path in output.iterdir()) == [
        "gatekeeper",
        "herald",
        "recordkeeper",
        "registrar",
        "sentry",
        "watchkeeper",
    ]
    for name in ("gatekeeper", "herald", "registrar", "sentry", "watchkeeper"):
        action = (output / name / "action.yml").read_text(encoding="utf-8")
        assert "$GITHUB_ACTION_PATH/shared/install-native.sh" in action
        assert "../../shared/install-native.sh" not in action
        assert (output / name / "shared" / "install-native.sh").is_file()
        assert "pip install" not in action
    sentry = output / "sentry"
    assert "Deterministic code enforcement" in (
        sentry / "README.md"
    ).read_text(encoding="utf-8")
    assert 'default: "0.26.0"' in (sentry / "action.yml").read_text(encoding="utf-8")
    installer = (sentry / "shared" / "install-native.sh").read_text(encoding="utf-8")
    assert 'version="${1:-0.26.0}"' in installer
    assert "4d7f2fa85686af8d1006aa530928f60e2cd3d13d8560b303495f2784d1b8bbed" in installer
    assert "239d01eb638433bd45c4ee3c977899eaaac19601b31d1b07c9444992fcd19da1" in installer
    assert "bd30ac366cfb5066e61aa53460beb228f873e68e1bf050393973fac8010c13cb" in installer
    assert not (output / "recordkeeper" / "action.yml").exists()
