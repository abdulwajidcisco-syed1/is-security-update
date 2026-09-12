# Implementation Action Plan
## IS Security Update — Database Security & Data Protection Podcast

| Field | Value |
|---|---|
| Version / status | 1.0 / Proposed execution plan |
| Date | 2026-09-12 |
| Inputs | [BRD.md](BRD.md) v0.2 and [SRS.md](SRS.md) v1.0 |
| Current state | BRD, SRS, and action plan prepared; application code, feeds, accounts, and deployment not validated |
| Planning assumption | One implementer, with operator participation for account setup and acceptance |
| Effort estimate | 18–25 engineering working days, plus a seven-calendar-day scheduled pilot and external account/policy lead times |

## 1. Delivery approach

Build an independent repository under the receiving operator's account. Reuse permitted pipeline code after inspecting it, then implement verified source coverage, evidence/safety gates, media generation, and resumable publication. Use local fixtures and dry-runs while account decisions are pending. Start the production schedule only after the pilot and operational handover.

The estimates below are planning ranges, not commitments. They assume the reference pipeline is available and substantially reusable. No new service subscriptions, deployments, or public uploads have been performed as part of preparing these documents.

## 2. Phased work breakdown

All tasks are initially **Not started**. “Implementer” means the person building the pipeline; “operator” means the friend receiving it. Dependencies refer to task IDs, not dates.

| ID | Phase / action | Owner | Depends on | Deliverable and completion evidence | Effort |
|---|---|---|---|---|---|
| P01 | Confirm persona, audience, operator identity, timezone/ready-time, retention preferences, and no-news policy; record SRS decisions D01–D03, D05–D08. | Operator + business author | None | Decision log with named owners, selected values and remaining blockers. | 0.5–1 day |
| P02 | Inspect the reference pipeline, its license, dependency versions, safety gate, timing output and uploader; identify reusable modules and required changes. | Implementer + business author | Access to reference code | Reuse inventory; no inherited credentials, branding, quotas or live dependencies. | 0.5–1 day |
| P03 | Verify public Thales and Imperva release/advisory sources and general DB-security feeds; inspect timestamps, permissions and sample payloads. Check proposed API/model/free-tier feasibility. | Implementer | None | Source register with working URLs, sample items, access method, policy review dates, timestamp rules and coverage gaps; D04/D10 evidence. | 1–2 days |
| P04 | Establish operator-owned repo/accounts, Pages configuration, channel/playlist, Groq key and local YouTube OAuth; confirm visibility and applicable upload/token constraints. | Operator, assisted by implementer | P01 | Ownership checklist, secret names only, successful authorization preflight; D07/D11 recorded. External waiting time tracked separately. | 0.5–1 day |
| P05 | Scaffold Python pipeline, validated configuration, schemas, structured logs, dry-run/manual interface, ignore rules and fixture test harness. | Implementer | P02 | Local dry-run and schema checks pass; proposed modules established. | 1 day |
| P06 | Implement source adapters, fixed-window normalization, retries, deduplication, relevance ranking and coverage reporting. | Implementer | P03, P05 | AT01–AT02 pass; source outage and all-source-failure behavior demonstrated. | 2–3 days |
| P07 | Adapt scripting and incident selection; implement claim/evidence mapping, exact identifier checks, unknown-detail handling, one-retry safety gates and prompt-injection isolation. | Implementer | P06; P01 editorial decisions | AT03–AT06 pass; reviewed approved script/article samples and withholding records. | 3–4 days |
| P08 | Integrate Kokoro and FFmpeg; generate captions from narration timing, preserve source citations in transcript and validate audio/video artifacts. | Implementer | P07 | AT07 passes; benchmark short and 12–18-minute samples on intended CPU runner. | 1–2 days |
| P09 | Implement durable run manifests, same-edition locking, checksums, Release publishing and reconciliation on retries. | Implementer | P05, P08; P04 for integration | Verified release assets; failure-after-upload and same-date rerun tests pass. | 1 day |
| P10 | Implement YouTube upload, returned-ID persistence, playlist insertion, disclosure, visibility checks and token-failure recovery. | Implementer | P04, P08, P09 | AT09 passes; uncertain upload outcome cannot cause blind duplicate creation. | 1 day |
| P11 | Build article templates, audio/video embeds, dated paths and archive; deploy Pages explicitly through Actions; support verified release-video fallback and later YouTube update. | Implementer | P07, P09; P04 for deployment | AT08 passes on the actual hosted site, including repo base path; D11 implemented. | 1–2 days |
| P12 | Wire daily/manual workflow, UTC schedule, time budget, minimum permissions, quota ceilings, stage resumption, destination verification and alerts. | Implementer | P09–P11; P01 schedule decisions | End-to-end run from operator-owned Actions; AT10–AT11 pass. | 1 day |
| P13 | Execute integrated acceptance, safety/provenance review, secret-marker checks, independent-ownership and recovery exercises; fix release blockers. | Implementer + operator | P12 | AT01–AT12 evidence, defects resolved, retention/recovery policy configured. | 2 days |
| P14 | Run seven consecutive daily scheduled pilot editions; inspect content, readiness, coverage, publication success and free-tier usage. | Implementer + operator | P13 | AT13 report; each failure corrected and relevant scenario rerun; go-live recommendation. | 7 calendar days; 1 engineering day monitoring effort |
| P15 | Deliver setup/operations guide, source/config reference, OAuth recovery, correction and resume instructions; operator performs assisted recovery, then enable normal operation. | Implementer + operator | P14 | Signed acceptance record, operator-owned operational responsibility and 30-day measurement sheet. | 1 day |

## 3. Milestones and sequence

| Milestone | Exit condition | Indicative timing |
|---|---|---|
| M0 — Feasibility and baseline | P01–P04 complete, usable primary-product sources found, reuse and deployment decisions recorded. | Week 1 |
| M1 — Approved content | P05–P07 complete; evidence, safety and quiet-day tests pass. | Weeks 2–3 |
| M2 — End-to-end publishing | P08–P12 complete; all three destinations verified with resumption. | Weeks 3–4 |
| M3 — Acceptance ready | P13 complete; no critical outstanding defects. | Weeks 4–5 |
| M4 — Operational handover | Seven-day pilot and P15 complete. | Approximately Weeks 5–6, subject to external dependencies |

Primary dependency chain: P02 → P05 → P06 → P07 → P08 → P09 → publishing integrations → P12 → P13 → P14 → P15. Source discovery P03 feeds P06; account setup P04 gates live integrations. Source validation and operator account work can progress independently of the local scaffold.

## 4. First actions to execute

1. Record operator decisions D01–D03, D05–D08; leave unprovided details explicitly unresolved.
2. Obtain the reference source repository or a permitted code export and complete P02.
3. Create a source register and validate at least one usable official public source for CipherTrust Manager and one for Imperva DAM, plus general database-security coverage. If unavailable, document the coverage gap for a scope decision instead of implying support exists.
4. Validate account-specific quotas, model availability, YouTube eligibility, and explicit Pages deployment approach.
5. Start fixture-based implementation in the independent repository; validate editorial gates before any external publication.

## 5. Required artifacts

| Artifact | Contents | Produced by |
|---|---|---|
| `DECISIONS.md` | Resolved D01–D11, date, decision owner and rationale; no secrets. | P01–P04 |
| `SOURCE_REGISTER.md` | Exact public endpoints, topics, timestamp basis, permitted method, sample results, policy-review date, health and fallback. | P03 |
| `sources.yaml` and show config | Enabled feeds/topics, aliases, ranking, schedule, voice/model, targets, retention and limits; validated schema. | P05–P06 |
| `pipeline/` and dependency lock/pins | Reused/adapted stages, data contracts, auth helper, safety gates and publishers. | P05–P12 |
| `.github/workflows/` | Daily/manual pipeline, scoped credentials, concurrency, explicit Pages deployment and failure reporting. | P12 |
| `docs/` | Static article templates/output and archive, with repository-aware URLs. | P11 |
| Test fixtures and acceptance report | AT01–AT13 evidence, run URLs, artifact checksums, sample content review and defect closure. | P05–P14 |
| `OPERATIONS.md` | Setup, secrets by name, schedule, monitoring, rerun/resume, OAuth recovery, correction, retention and pause procedures. | P15 |

These are planned implementation artifacts; only the SRS and this action plan are delivered at the documentation stage.

## 6. Risk and response register

| Risk | Impact | Response / verification | Owner |
|---|---|---|---|
| Vendor release/support data is gated or has unreliable dates | Core product coverage incomplete | Validate sources early; accept only public permitted alternatives; make coverage gaps explicit before baseline approval. | Implementer |
| Reference source is unavailable or incompatible | Increased implementation effort | Inspect before estimating reuse savings; revise P05–P10 estimate if components must be rebuilt. | Business author + implementer |
| Fabricated versions, CVEs or incident resolutions | Misleading client-facing material | Evidence mapping, identifier checks, unknown labels, withholding and reviewed pilot examples. | Implementer |
| Harmful material leaks from source into output | Violates hard BRD guardrail | Untrusted-source isolation, per-segment gate, one retry, final-output checks and fail-closed behavior. | Implementer |
| OAuth expiry, revocation, or upload eligibility restrictions | YouTube interruption or unexpected visibility | Validate actual account/API state; rehearsed reauthorization and partial-publication recovery; no promise of permanent tokens. | Operator |
| Pages source commits do not deploy | Missing daily article despite workflow commit success | Explicit artifact deployment and post-deploy URL/media checks; SRS §6.1. | Implementer |
| CPU generation or service quotas exceed free allowance | Late episode or cost target failure | Benchmark representative episode, measure usage, apply caps, avoid automatic paid fallbacks; resolve feasibility before launch. | Implementer + operator |
| Runner dies after remote upload | Duplicate videos or inconsistent targets | Durable IDs/checkpoints, reconciliation, stage-level resume and failure-injection tests. | Implementer |
| No qualifying news or all content withheld | Ambiguous daily-delivery behavior | Resolve D08; distinguish quiet coverage, collection failure and safety withholding. | Operator + business author |
| Unknown retention/sharing expectations | Broken archives or unintended visibility | Resolve D05/D06 before publishing; no automatic deletion initially; verify target visibility. | Operator |

## 7. Test execution and release gates

1. **Local gate:** AT01–AT07 pass using recorded/synthetic fixtures; dry-run performs no public writes.
2. **Integration gate:** AT08–AT12 pass under operator-owned resources and selected visibility; verify outputs in actual destinations, not only API success responses.
3. **Pilot gate:** AT13 completes for seven calendar days. Review factual support, technical pronunciation, captions, relevant coverage, readiness time and resource use. Fix blockers and rerun affected scenarios before acceptance.
4. **Handover gate:** operator can change supported source configuration, identify a failure, resume an interrupted edition, reauthorize YouTube, and pause scheduling using the runbook.

Do not mark full success when only Release/YouTube succeeds and Pages fails, or when Pages/Release succeeds and YouTube fails. The complete product includes all three targets.

## 8. Ongoing operating plan

| Cadence / trigger | Action | Owner |
|---|---|---|
| Every run | Capture stage states, source coverage, withheld items, duration, target URLs/IDs and quota use; verify outputs before reporting success. | Automated pipeline |
| Failed, partial or late run | Notify via chosen route; inspect sanitized error, correct cause and resume the failed stage with the original edition/window. | Operator |
| Daily during pilot | Review claims/citations and media samples; record usability feedback and defects. | Operator + implementer |
| Weekly after launch, proposed | Check source health and gaps, review a sample for accuracy/safety, examine usage and OAuth health. | Operator |
| Rolling 30 days | Measure all-target on-time delivery against ≥95%, content defects, withheld segments, runtime distribution and actual spend against $0. | Operator |
| Source/service change | Revalidate adapter, policy, quota or model behavior; run affected tests before re-enabling. | Maintainer |
| Published factual error | Apply explicit correction revision, update text/media/destinations, verify links and retain correction record. | Operator + maintainer |

## 9. Definition of done

- Every BRD FR-1–FR-14 maps to implemented SRS behavior and passing acceptance evidence.
- Public-source-only and safety restrictions apply to every published surface.
- Operator-owned daily pipeline produces release assets, a working dated article/archive and YouTube playlist video without the original author's infrastructure or PC.
- Failure recovery avoids duplicate publication; secret handling, actual free-tier feasibility and archive integrity are demonstrated.
- All launch-blocking decisions are closed, pilot is accepted, and setup/recovery documentation has been exercised by the operator.
- The 30-day reliability measurement continues after handover; a seven-day pilot is not presented as proof of a 30-day service level.
