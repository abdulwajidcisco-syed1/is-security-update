# Implementation status

Updated 2026-09-20. GitHub Release, private YouTube, and public GitHub Pages publishing have been exercised successfully.

| Plan task | State | Evidence / next step |
|---|---|---|
| P01 | In progress | Repository visibility is public to support GitHub Pages. Operator schedule, audience, retention and quiet-day decisions remain open. |
| P02 | Blocked on input | Reference pipeline code was not supplied; no reuse claim is made. |
| P03 | In progress | Source register created; live CISA, NVD and Hacker News collection passed. Vendor-specific coverage remains. |
| P04 | In progress | Public repository and Project created; repository visibility was changed with explicit approval to support Pages. YouTube OAuth refresh and destination ownership preflight passed for the configured private playlist. Groq generation, YouTube OAuth preflight, release publishing, and public GitHub Pages hosting pass. |
| P05 | Done | Validated YAML configuration, data records, dry-run CLI, structured manifest and ignored secrets/tooling. |
| P06 | Substantially implemented | Live RSS, NVD, and Hacker News adapters; bounded public-host fetching; fixed window, timestamp validation, ranking, coverage and exact dedupe. Vendor-specific feeds and semantic dedupe remain. |
| P07 | Substantially implemented | Groq structured output, claim/evidence mapping, citation/identifier validation, prompt-injection isolation and deterministic safety gates are implemented. Live Groq structured generation passed in GitHub Actions. |
| P08 | Substantially implemented | Kokoro narration, actual-chunk caption timing, MP3/WAV output and FFmpeg H.264/AAC video rendering passed on a GitHub CPU runner. Human pronunciation and sampled caption review remain. |
| P09 | Substantially implemented | Checksum-aware GitHub Release publisher creates a draft, uploads seven validated assets, reconciles matching remote SHA-256 digests, blocks ambiguous collisions, and publishes only after completion. Cross-run artifact recovery and injected interruption tests remain. |
| P10 | Substantially implemented | OAuth preflight, exact-edition reconciliation, private resumable upload, synthetic-media disclosure, idempotent playlist insertion, video-ID persistence and immediate verification passed. Post-processing playback and token-revocation exercises remain. |
| P11 | Done | Public GitHub Pages deployment verified at the repository base path and dated episode path, with archive, citations, disclosure, packaged audio/video, responsive controls, and HTTPS. |
| P12-P15 | Not started | Daily orchestration, integrated acceptance, pilot and handover remain. |

Current validation: 36 local tests pass. Live source smoke test succeeded for all three configured endpoints, collecting 581 records and selecting seven candidates. YouTube OAuth preflight passed in GitHub Actions run 35445880562. The live collection, Groq generation, safety/evidence validation, article rendering and review-artifact upload passed in run 35446699138. The live-preview workflow remains review-only; publishing uses separately confirmed workflows.
Media acceptance increment: GitHub Actions run 35447459904 rendered a 106.15-second briefing with nine caption cues. WAV, MP3, SRT and MP4 artifacts were non-empty and checksummed; the review bundle is retained for seven days.

GitHub Release acceptance increment: run 35449085064 published private tag episode-2026-09-19 with seven assets. GitHub-reported SHA-256 digests were verified during upload; the release is neither draft nor prerelease.

YouTube acceptance increment: run 35452631380 uploaded private video FCr6LP-Y3Tc and inserted it into the configured playlist. Immediate verification returned private visibility and processing status; playback-after-processing remains to be checked.

Website acceptance completed: run 35465726072 deployed the public site from commit 8fb6d79. The workflow and an independent fetch verified HTTP 200 at the repository base path and dated episode path, with packaged audio/video, synthetic-narration disclosure, citations and archive structure. The repository is public and Pages uses HTTPS.
