# Validation report

Date: 2026-09-12. Scope: initial offline foundation only.

- Runtime: official workspace-local Python 3.13.13 on Windows.
- Dependency: PyYAML 6.0.2.
- `python -m unittest discover -s tests -v`: **14 tests passed**.
- Fixture dry-run: **passed**, two stories selected, one item quarantined, no publication.
- Same-input resume: **passed**, verified artifact hashes and reused results.
- Staged source/document scan: no credential-pattern matches before initial commit.
- Git push using Windows Credential Manager: **passed**; repository verified private.
- GitHub Actions: **passed** on Ubuntu/Python 3.13: [run 34706412678](https://github.com/abdulwajidcisco-syed1/is-security-update/actions/runs/34706412678), commit `429330c`. Tests and dry-run/resume completed successfully.
- Private Project: verified with all 15 implementation issues and current statuses.

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
## 2026-09-20 integrated orchestration increment

- Local suite: **40 tests passed**, including bounded source rate-limit retry, archive preservation, publication reconciliation, and workflow contract checks.
- GitHub-hosted CI: run 35466649276 passed on commit `3c13bb0`.
- Integrated recovery: run 35466879235 restored the existing checksummed edition, reconciled the GitHub Release and private YouTube video/playlist without duplicates, preserved the Pages archive, redeployed, and verified all destination URLs.
- Schedule: daily 03:00 UTC trigger is installed; `PILOT_ENABLED` controls scheduled execution.
- Editorial acceptance now verifies one corrective retry followed by fail-closed behavior; local suite: **41 tests passed**.
- Publication record from run 35466879235 confirms YouTube video FCr6LP-Y3Tc is private, reconciled, in the playlist, and has processing status succeeded.
- Editorial prompt now targets 1,800–2,700 spoken words on evidence-rich active days and explicitly requires shorter output rather than padding sparse days.
