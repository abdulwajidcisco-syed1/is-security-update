# Integrated acceptance record

Updated 2026-09-26. Evidence links should identify immutable commits, Actions runs, releases, videos, or dated pages.

| Test | State | Evidence / remaining exercise |
|---|---|---|
| AT01 | Passed | Configuration validation and config-only source/topic tests. |
| AT02 | Passed | Window, timezone, timestamp, duplicate, outage, and resume tests. |
| AT03 | Passed | Live cited Groq episode generation and identifier validation. |
| AT04 | Partial | No invented case-study behavior is implemented; operator review of a real incident edition remains. |
| AT05 | Passed | Quiet selection and all-source failure are distinct. |
| AT06 | Passed | Unsupported citations and technical identifiers are rejected; source text is isolated as untrusted evidence; unsafe output receives one corrective retry and a second rejection fails closed. |
| AT07 | Partial | Short render passed. Active-day CPU benchmark run 35469753990 rendered 1,892 words to 1,017.45 seconds (16m57.45s) with 27 caption cues; the full job completed in 21m37s within the 90-minute budget. Human beginning/middle/end caption-alignment and technical-pronunciation review remains. |
| AT08 | Passed | Release hashes and public Pages article/media/archive verified. |
| AT09 | Partial | Private upload, disclosure, exact-edition reconciliation and playlist reuse pass; run 35466879235 records `processing_status: succeeded`. Post-rotation OAuth and playlist ownership preflight passed in run 35472898650. Provider-side old-secret disable/delete confirmation and the controlled token-revocation/reauthorization exercise remain. |
| AT10 | Passed | Run 35466879235 restored the existing release checkpoint, reconciled the same release/video/playlist without duplication, redeployed Pages, and verified all destinations after a prior verifier failure. Workflow concurrency prevents overlap. |
| AT11 | Partial | Timeouts, bounded source 429/5xx/network retries, partial coverage, and bounded Groq schema retry are tested. Quota exhaustion and operator notification receipt remain pilot exercises. |
| AT12 | Partial | Secret scan, independent GitHub-hosted execution, 30-edition archive preservation, and same-edition assisted reconciliation pass. Operator-led recovery sign-off remains. |
| AT13 | Passed | Seven pilot editions from 2026-09-20 through 2026-09-26 are recorded in `PILOT_LOG.csv`. The final [scheduled run 36213625587](https://github.com/abdulwajidcisco-syed1/is-security-update/actions/runs/36213625587) completed with all three sources healthy, zero quarantined records, an approved 4,904-word episode, 3,039.1 seconds of media, and 536 captions. Its GitHub Release contains seven checksummed assets, private YouTube video `VMG7geKTJNk` was inserted into the playlist, and the public archive and dated episode returned HTTP 200. Day-one source failure and day-five transient Groq rejection both failed safely and have verified corrective evidence. Human playback/content approval remains tracked under AT04, AT07, AT09, AT12 and P15. |

## Release blockers

- Complete human media review and YouTube post-processing playback check.
- Exercise OAuth revocation/recovery without exposing secrets.

## Acceptance sign-off

- Operator: pending
- Business author: pending
- Implementer: pending final AT01-AT12 review
- Go-live recommendation: conditional approval pending operator and business-author sign-off
