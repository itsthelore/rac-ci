# As Decided Sentry

Deterministic code enforcement for engineering decisions.

Sentry checks machine-readable constraints carried by your decision artifacts
against the source changes in a pull request. It supports required and
forbidden patterns, import boundaries, full-tree certification, and SARIF
annotations—without embeddings, network calls, or an LLM judge.

## Use it

```yaml
name: Sentry

on:
  pull_request:

permissions:
  contents: read
  security-events: write

jobs:
  sentry:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: asdecided/sentry@v0.26.0
```

By default, Sentry checks added lines against the pull request base and uploads
one SARIF report to GitHub Code Scanning.

Use `full: "true"` to certify the complete repository tree:

```yaml
      - uses: asdecided/sentry@v0.26.0
        with:
          full: "true"
```

## Decision constraints

Add a `Code Constraints` block to an accepted decision:

```yaml
version: 1
eligibility: eligible
reason: "The dependency boundary is deterministic and repository-local."
rules:
  - id: domain-has-no-database-driver
    kind: forbid_import
    path_glob: "src/domain/**/*.rs"
    pattern: "^(sqlx|diesel)(::|$)"
    message: "Domain code must not import a database driver."
```

Supported rule kinds:

- `forbid_import`
- `forbid_pattern`
- `require_pattern`

Sentry deliberately has no model-judged escape hatch. A decision is either
enforced through a deterministic rule, explicitly ineligible, or visibly
unclassified.

## Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `path` | `decisions` | Decision corpus directory |
| `repository` | `.` | Source repository root |
| `base` | PR base SHA | Git base revision for diff mode |
| `full` | `false` | Check the complete tree |
| `upload-sarif` | `true` | Upload Code Scanning results |
| `sarif-file` | `asdecided-sentry.sarif` | SARIF output path |
| `asdecided-version` | `0.26.0` | Native release to install |

Authoritative development lives in
[asdecided/ci](https://github.com/asdecided/ci/tree/main/sentry).
