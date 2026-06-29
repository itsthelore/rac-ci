# rac-ci

The CI delivery surface for [RAC](https://github.com/itsthelore/rac-core)
(requirements-as-code) — one subdir per **capability**, with delivery platforms
nested inside (`github/` first). Per ADR-092 (one repo per concern, subdir per
member) this consolidates the CI wrappers that previously lived in `rac-core` and
in the standalone `rac-actions` / `lore-watchkeeper` / `lore-gatekeeper` repos.

Every capability is a **thin wrapper over the public `rac` CLI** (ADR-063); all
analysis and policy live in the engine package. The wrappers install the
published `rac-core` from PyPI (pin with the `rac-version` input).

## Capabilities

| Capability | Subdir | Wraps | Consumed as |
| --- | --- | --- | --- |
| Watchkeeper | [`watchkeeper/github/`](watchkeeper/github/) | `rac watchkeeper` (PR knowledge review) | `uses: itsthelore/rac-ci/watchkeeper/github@<ref>` |
| Gatekeeper | [`gatekeeper/github/`](gatekeeper/github/) | `rac gate --sarif` (required merge gate) | `uses: itsthelore/rac-ci/gatekeeper/github@<ref>` |
| Registrar | [`registrar/github/`](registrar/github/) | `rac validate --sarif` (well-formedness, ADR-058) | `uses: itsthelore/rac-ci/registrar/github@<ref>` |
| Recordkeeper | [`recordkeeper/`](recordkeeper/) | read-access audit recorder (ADR-084) | *placeholder — not yet shipped* |

A reusable Watchkeeper workflow is also published at
[`.github/workflows/watchkeeper.yml`](.github/workflows/watchkeeper.yml)
(`uses: itsthelore/rac-ci/.github/workflows/watchkeeper.yml@<ref>`).

`bitbucket/` and `jenkins/` platform wrappers join under each capability when
demanded; the engine is already platform-neutral (SARIF/JSON), so that work is in
the wrappers, not the engine.

## History

The `watchkeeper/`, `gatekeeper/`, and `registrar/` wrappers moved here from
`rac-core` with history preserved (ADR-092 convergence). Consumers pinned to the
old `itsthelore/rac-core@<tag>`, `…/pr-gate-action@v0`, or `…/validate-action@v0`
paths keep resolving on those tags; new consumers use the `rac-ci` paths above.
