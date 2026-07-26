# AsDecided CI

**Make recorded decisions part of the merge gate.**

AsDecided CI adds native validation, relationship checks, knowledge review, and
decision surfacing to GitHub pull requests. Each action downloads a
checksum-verified [`asdecided/core`](https://github.com/asdecided/core) release
and delegates policy to the public `decided` CLI instead of reimplementing the
engine in workflow code.

```yaml
- uses: asdecided/ci/gatekeeper/github@v1
  with:
    path: decisions
```

Use a commit SHA instead of `v1` when your dependency policy requires immutable
action references.

## Capabilities

| Capability | Subdir | Wraps | Consumed as |
| --- | --- | --- | --- |
| Watchkeeper | [`watchkeeper/github/`](watchkeeper/github/) | `decided watchkeeper` (PR knowledge review) | `uses: asdecided/ci/watchkeeper/github@<ref>` |
| Gatekeeper | [`gatekeeper/github/`](gatekeeper/github/) | `decided gate --sarif` (required merge gate) | `uses: asdecided/ci/gatekeeper/github@<ref>` |
| Registrar | [`registrar/github/`](registrar/github/) | `decided validate --sarif` (well-formedness, ADR-058) | `uses: asdecided/ci/registrar/github@<ref>` |
| Herald | [`herald/github/`](herald/github/) | `decided decisions-for --json` (advisory governing-decisions comment on PRs) | `uses: asdecided/ci/herald/github@<ref>` |
| Recordkeeper | [`recordkeeper/`](recordkeeper/) | read-access audit recorder (ADR-084) | *placeholder — not yet shipped* |

A reusable Watchkeeper workflow is also published at
[`.github/workflows/watchkeeper.yml`](.github/workflows/watchkeeper.yml)
(`uses: asdecided/ci/.github/workflows/watchkeeper.yml@<ref>`).

`bitbucket/` and `jenkins/` platform wrappers join under each capability when
demanded; the engine is already platform-neutral (SARIF/JSON), so that work is in
the wrappers, not the engine.

## History

The `watchkeeper/`, `gatekeeper/`, and `registrar/` wrappers moved here from
`asdecided/core` with history preserved (ADR-092 convergence). Consumers pinned to the
old `asdecided/core@<tag>`, `…/pr-gate-action@v0`, or `…/validate-action@v0`
paths keep resolving on those tags; new consumers use the `asdecided/ci` paths
above.
