# Integrated acceptance record

Updated 2026-09-20. Evidence links should identify immutable commits, Actions runs, releases, videos, or dated pages.

| Test | State | Evidence / remaining exercise |
|---|---|---|
| AT01 | Passed | Configuration validation and config-only source/topic tests. |
| AT02 | Passed | Window, timezone, timestamp, duplicate, outage, and resume tests. |
| AT03 | Passed | Live cited Groq episode generation and identifier validation. |
| AT04 | Partial | No invented case-study behavior is implemented; operator review of a real incident edition remains. |
| AT05 | Passed | Quiet selection and all-source failure are distinct. |
| AT06 | Partial | Evidence and deterministic safety rejection pass; external checker-unavailable exercise remains. |
| AT07 | Partial | CPU media render, decode, and timing checks pass; human pronunciation review remains. |
| AT08 | Passed | Release hashes and public Pages article/media/archive verified. |
| AT09 | Partial | Private upload, playlist, disclosure, and immediate state verified; post-processing playback and token-revocation exercise remain. |
| AT10 | Passed | Run 35466879235 restored the existing release checkpoint, reconciled the same release/video/playlist without duplication, redeployed Pages, and verified all destinations after a prior verifier failure. Workflow concurrency prevents overlap. |
| AT11 | Partial | Timeouts, bounded source 429/5xx/network retries, partial coverage, and bounded Groq schema retry are tested. Quota exhaustion and operator notification receipt remain pilot exercises. |
| AT12 | In progress | Secret scan and independent GitHub-hosted execution pass; retention preview and assisted recovery remain. |
| AT13 | Not started | Requires seven consecutive scheduled pilot editions. |

## Release blockers

- Resolve operator schedule/timezone, audience, no-news policy, and alert recipient.
- Complete human media review and YouTube post-processing playback check.
- Exercise OAuth revocation/recovery without exposing secrets.
- Complete seven-day pilot and operator-assisted recovery.

## Acceptance sign-off

- Operator: pending
- Business author: pending
- Implementer: pending final AT01â€“AT12 review
- Go-live recommendation: pending AT13
