# Validation report

Date: 2026-09-12. Scope: initial offline foundation only.

- Runtime: official workspace-local Python 3.13.13 on Windows.
- Dependency: PyYAML 6.0.2.
- `python -m unittest discover -s tests -v`: **14 tests passed**.
- Fixture dry-run: **passed**, two stories selected, one item quarantined, no publication.
- Same-input resume: **passed**, verified artifact hashes and reused results.
- Staged source/document scan: no credential-pattern matches before initial commit.
- Git push using Windows Credential Manager: **passed**; repository verified private.
- GitHub Actions: **not run**; token lacks workflow-write permission. Template is inactive in `ci/offline-checks.yml.example`.

## Covered behavior

Configuration validation and config-only topic addition; URL credential/local-host
rejection; half-open UTC window and offset handling; missing/naive dates; material
update ordering; duplicate evidence retention; relevance/ranking; exclusive edition
locks; changed-input and corrupt/incomplete-manifest resume rejection; and separate
partial, all-failed and empty-source outcomes.

## Not established by this report

Live feed coverage/access permissions, semantic cross-report deduplication, LLM
accuracy, content-safety gates, source prompt-injection resistance, narration,
caption synchronization, distributed recovery, public/private delivery behavior,
service cost, scheduled reliability, YouTube or Pages deployment. Those require
later acceptance tests from SRS.md.
