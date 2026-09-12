# Operations — offline milestone

## Development

Install Python 3.11+ and the pinned requirements, then use the commands in
[README.md](README.md). The workspace-local `.tools` directory is development
tooling only and must not be committed. No credentials are needed for tests.

## Inspect and resume

Each edition is stored under `runs/<show-id>/<UTC-date>/`. Read `manifest.json`
for source outcomes, coverage, selection status, counts, and hashes. It records
`selection_complete`, never published success. Quarantine files contain record
indices and sanitized reason codes, not raw errors/credentials.

Use the same configuration, fixture and `--window-end` with `--resume`. A checksum
mismatch blocks resume. Preserve the corrupted run for diagnosis and generate a
new test result with `--output runs-recheck`; never claim an unverified result is
valid. A changed window/configuration also requires a separate output directory.

The `.lock` file prevents simultaneous local writers. After a crash, inspect its
PID and confirm no process owns that edition before manually removing the exact
stale lock. Never clear another active run's lock. This local lock is not yet a
distributed lock for Actions runners; future publishing must add workflow
concurrency and durable remote state reconciliation.

## Failure meanings

- Partial source failure: continue only from successful sources and label coverage.
- All sources failed: failed collection, never a quiet-news result.
- Missing/invalid metadata: quarantine with record index.
- Empty successful selection: no qualifying items; no synthetic episode generated.
- Invalid configuration or changed/corrupt resume: fail with nonzero exit.

No live source, Groq, TTS, FFmpeg, OAuth or publisher is enabled yet. These must be
implemented and tested before operational scheduling or content publication.
