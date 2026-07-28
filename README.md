# AsDecided CI

The CI delivery surface for [RAC](https://github.com/asdecided/core)
(requirements-as-code) — one subdir per **capability**, with delivery platforms
nested inside (`github/` first). Per ADR-092 (one repo per concern, subdir per
member) this consolidates the CI wrappers that previously lived in `asdecided-core` and
in the standalone `rac-actions` / `lore-watchkeeper` / `lore-gatekeeper` repos.

Every capability is a **thin wrapper over the public `decided` CLI** (ADR-063);
all analysis, policy, and Herald rendering live in the native engine. The
wrappers download a checksum-verified `asdecided-core` release (pin with the
`asdecided-version` input). No action requires a Python runtime.

## Capabilities

| Capability | Subdir | Wraps | Consumed as |
| --- | --- | --- | --- |
| Watchkeeper | [`watchkeeper/github/`](watchkeeper/github/) | `decided watchkeeper` (PR knowledge review) | `uses: asdecided/ci/watchkeeper/github@<ref>` |
| Gatekeeper | [`gatekeeper/github/`](gatekeeper/github/) | `decided gate --sarif` (required merge gate) | `uses: asdecided/ci/gatekeeper/github@<ref>` |
| Registrar | [`registrar/github/`](registrar/github/) | `decided validate --sarif` (well-formedness, ADR-058) | `uses: asdecided/ci/registrar/github@<ref>` |
| Herald | [`herald/github/`](herald/github/) | `decided herald` (advisory governing-decisions comment on PRs) | `uses: asdecided/ci/herald/github@<ref>` |
| Recordkeeper | [`recordkeeper/`](recordkeeper/) | read-access audit recorder (ADR-084) | *placeholder — not yet shipped* |
| Sentry | [`sentry/github/`](sentry/github/) | `decided sentry --sarif` (deterministic decision-to-code enforcement) | `uses: asdecided/ci/sentry/github@<ref>` |

A reusable Watchkeeper workflow is also published at
[`.github/workflows/watchkeeper.yml`](.github/workflows/watchkeeper.yml)
(`uses: asdecided/ci/.github/workflows/watchkeeper.yml@<ref>`).

`bitbucket/` and `jenkins/` platform wrappers join under each capability when
demanded; the engine is already platform-neutral (SARIF/JSON), so that work is in
the wrappers, not the engine.

## Distribution facades

Development remains in this repository. Marketplace-facing repositories are
generated release facades so each action can carry a root `action.yml`:

`asdecided/gatekeeper`, `asdecided/herald`, `asdecided/recordkeeper`,
`asdecided/registrar`, `asdecided/watchkeeper`, and `asdecided/sentry`.

`distribution/actions.json` is the source manifest and
`scripts/package-facades.sh <empty-output-directory>` builds all six
deterministically. Recordkeeper is packaged as a companion-repository
placeholder but is not marked Marketplace-ready until its execution wrapper
ships; the other five contain root action manifests.

## History

The `watchkeeper/`, `gatekeeper/`, and `registrar/` wrappers moved here from
`asdecided-core` with history preserved (ADR-092 convergence). Consumers pinned to the
old `asdecided/core@<tag>`, `…/pr-gate-action@v0`, or `…/validate-action@v0`
paths keep resolving on those tags; new consumers use the `asdecided/ci` paths
above.
