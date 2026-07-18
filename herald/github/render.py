#!/usr/bin/env python3
"""Render the decisions-on-PR comment from `rac decisions-for --json`.

The thin-client half of the `pr-decision-surfacing` design (ADR-063): run the
engine's live-decisions lookup for each changed path, merge by decision id,
and emit one deterministic Markdown comment — facts, never verdicts (ADR-034).
Everything semantic (scope matching, liveness) is the engine's; this script
only joins, sorts, and formats. No wall-clock input: the same corpus and diff
render the same bytes.

Exit code is 0 whether or not decisions govern (advisory surfaces never fail
a check); only operational breakage — the `rac` binary missing outright —
exits non-zero. A lookup failure on one path is skipped with a warning so a
single odd path cannot take down the whole comment.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

MARKER = "<!-- lore-decisions-on-pr -->"

EMPTY_BODY = (
    f"{MARKER}\n"
    "### Decisions governing this change\n\n"
    "No recorded decisions govern the paths changed by this pull request.\n"
)

# Changed paths listed per decision before collapsing to a count.
_PATHS_SHOWN = 3


def _lookup(rac_bin: str, path: str, corpus: str) -> dict | None:
    """One `rac decisions-for <path> <corpus> --json` call, parsed, or None."""
    try:
        proc = subprocess.run(
            [rac_bin, "decisions-for", path, corpus, "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(f"error: rac binary not found: {rac_bin!r}", file=sys.stderr)
        raise SystemExit(1) from None
    if proc.returncode != 0:
        print(
            f"warning: decisions-for skipped {path!r} (exit {proc.returncode})",
            file=sys.stderr,
        )
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"warning: decisions-for emitted non-JSON for {path!r}", file=sys.stderr)
        return None


def collect(rac_bin: str, corpus: str, changed_paths: list[str]) -> list[dict]:
    """Governing decisions merged across paths, sorted by decision id.

    Each entry: id, title, status, path (the artifact file), matching entries
    and changed paths as sorted lists. The engine already scopes the answer to
    live decisions with a matching declared `## Applies To`.
    """
    merged: dict[str, dict] = {}
    for changed in changed_paths:
        result = _lookup(rac_bin, changed, corpus)
        if not result:
            continue
        for decision in result.get("decisions", []):
            entry = merged.setdefault(
                decision["id"],
                {
                    "id": decision["id"],
                    "title": decision["title"],
                    "status": decision["status"],
                    "path": decision["path"],
                    "matching_entries": set(),
                    "changed_paths": set(),
                },
            )
            entry["matching_entries"].add(decision["matching_entry"])
            entry["changed_paths"].add(changed)
    decisions = []
    for entry in sorted(merged.values(), key=lambda e: e["id"]):
        entry["matching_entries"] = sorted(entry["matching_entries"])
        entry["changed_paths"] = sorted(entry["changed_paths"])
        decisions.append(entry)
    return decisions


def _bullet(decision: dict, link_base: str) -> str:
    scopes = ", ".join(f"`{s}`" for s in decision["matching_entries"])
    shown = decision["changed_paths"][:_PATHS_SHOWN]
    changed = ", ".join(f"`{p}`" for p in shown)
    more = len(decision["changed_paths"]) - len(shown)
    if more > 0:
        changed += f" +{more} more"
    link = f"{link_base}/{decision['path']}" if link_base else decision["path"]
    return (
        f"- **[{decision['id']} — {decision['title']}]({link})**"
        f" ({decision['status']}) — applies to {scopes} — changed: {changed}"
    )


def render(decisions: list[dict], link_base: str, max_inline: int) -> str:
    """The comment body: marker, terse header, one bullet per decision."""
    if not decisions:
        return EMPTY_BODY
    count = len(decisions)
    plural = "" if count == 1 else "s"
    lines = [
        MARKER,
        "### Decisions governing this change",
        "",
        f"This pull request touches paths governed by {count} recorded "
        f"decision{plural} — review recommended.",
        "",
    ]
    inline = decisions[:max_inline] if max_inline > 0 else decisions
    rest = decisions[len(inline) :]
    lines.extend(_bullet(d, link_base) for d in inline)
    if rest:
        lines.append("")
        lines.append(f"<details><summary>{len(rest)} more governing decision"
                     f"{'' if len(rest) == 1 else 's'}</summary>")
        lines.append("")
        lines.extend(_bullet(d, link_base) for d in rest)
        lines.append("")
        lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--paths-file", required=True)
    parser.add_argument("--link-base", default="")
    parser.add_argument("--max-inline", type=int, default=5)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rac-bin", default="rac")
    args = parser.parse_args(argv)
    with open(args.paths_file, encoding="utf-8") as fh:
        changed_paths = sorted({line.strip() for line in fh if line.strip()})
    decisions = collect(args.rac_bin, args.corpus, changed_paths)
    body = render(decisions, args.link_base.rstrip("/"), args.max_inline)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(body)
    has_decisions = "true" if decisions else "false"
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"has_decisions={has_decisions}\n")
    print(f"{len(decisions)} governing decision(s); has_decisions={has_decisions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
