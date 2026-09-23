# Business Requirements Document (BRD)
## Project: IS Security Update — Database Security & Data Protection Podcast

| Field | Value |
|---|---|
| Document Owner | Shahbaz (author — this is being handed off, not self-operated) |
| Operator / Deployer | A friend (name/GitHub username TBD — see Section 13) |
| Status | Draft v0.2 |
| Last Updated | 2026-09-12 |
| Platform | Audio podcast + video (YouTube), reusing the `shahbaz-daily-updates` pipeline pattern |
| Infrastructure | **Fully independent deployment** — separate PC, separate GitHub account/repo, separate GitHub Actions, separate YouTube channel and API credentials. No shared secrets, billing, or infra with `shahbaz-daily-updates`. |

---

## 1. Executive Summary

An automated daily audio podcast (converted to video) that aggregates the last 24 hours of
vendor updates, product news, version/patch releases, advisories, incidents, and case studies
across the data-security tooling the user supports professionally — **Thales CipherTrust
Manager**, **Thales data-protection products more broadly (Thales docs/support ecosystem)**, and
**Imperva Data Activity Monitoring (DAM)** — plus general **database security** news (breaches,
CVEs, research) from major and community security-news sources. The goal is for the operator — a
friend of the original author, presumed to have a similar cybersecurity-consultancy/government-
client context (to confirm, Section 13) — to walk into client conversations already current on
what changed, what broke, and how it was fixed, without manually trawling vendor docs, release
notes, and security news sites every day.

This is a **hand-off, not a shared deployment**: `shahbaz-daily-updates` is the architecture and
requirements reference, but this project runs entirely on the friend's own PC, GitHub account,
and API credentials — see Section 13 for exactly what that requires him to set up.

## 2. Problem Statement

The user leads a cybersecurity consulting practice and personally advises government clients on
database security, encryption/key management, and data-activity monitoring. Staying current
requires tracking:
- Thales support/docs updates: CipherTrust Manager releases, patches, add-ons, and known-issue
  advisories, scattered across Thales's docs portal, support/community site, and product blog.
- Imperva DAM product news, version changes, and community discussion.
- Real-world database-security incidents worldwide and how they were resolved — material the
  user can reference as case studies with clients.
- General cybersecurity news relevant to database security, pulled from major outlets as well as
  practitioner community sites.

Doing this manually across many sources daily is time-consuming and easy to fall behind on,
especially since being behind directly weakens the credibility of advice given to clients.

## 3. Objectives (V1)

1. Every day, generate one audio episode (at least 30 minutes on every scheduled day) summarizing the
   prior 24 hours of notable activity across Thales/CipherTrust Manager, Imperva DAM, and
   database security generally. Every scheduled edition runs at least 30 minutes. When current news is sparse,
   the remaining time uses rotating, cited historical CVE references related to supported database products;
   invented, tangential, or repetitive filler is prohibited.
2. Content must be simple, conversational English, but precise enough to be client-conversation
   ready (correct product/version names, correct CVE IDs, no vague hand-waving).
3. Content should highlight, where available:
   - What changed (new release, patch, add-on, advisory, EOL notice).
   - Version-to-version change detail for CipherTrust Manager and Imperva DAM specifically.
   - Real-world incidents/breaches involving database security, and how they were detected,
     contained, and resolved (the case-study angle the user explicitly wants for client use).
4. Publish the episode as audio + a captioned video + a written article, through three targets:
   a GitHub repo release (raw file hosting), a **GitHub Pages website that gets a new daily
   article page** (embedding the audio player and the video), and a YouTube upload.
5. Never reproduce exploit code, working attack steps, or anything that reads as an attack
   how-to — see the safety guardrail in Section 9. This show reports on vulnerabilities and
   incidents; it does not teach exploitation.

## 4. Target User / Persona

- **Primary user (v1):** The friend receiving this project — modeled on the original author's own
  role (team leader in a cybersecurity consultancy, advising government-sector clients, direct
  responsibility for database-security-related engagements involving Thales CipherTrust Manager
  and Imperva DAM). **Assumption to confirm with him:** if his actual role/use case differs, the
  content focus in Section 7 and the client-facing framing in Section 3/11 should be adjusted
  accordingly before build.
- Single-user consumption in v1 (personal daily briefing), but content must be safe to reuse or
  paraphrase in client-facing conversations — see Section 9's sourcing/attribution rules.
- **Confidentiality boundary:** this pipeline only ever touches **public** sources (vendor sites,
  public news, public community posts). No client names, client environments, or engagement
  details are ever inputs to this pipeline — that would be a confidentiality breach and is
  explicitly out of scope, not just unimplemented.

## 5. Scope

### 5.1 In Scope (V1)
- Automated daily collection (trailing 24-hour window) covering the topic list in Section 7.
- Summarization/scripting into a single narrated episode script.
- Text-to-speech generation of that script into an audio file.
- Video rendering (cover art + burned-in captions synced to narration), reusing the existing
  pipeline's proven approach rather than designing a new visual style.
- Publish audio + transcript + video as GitHub release assets (raw file hosting).
- Publish a **daily article page to a GitHub Pages site**: written summary (derived from the
  script/transcript), embedded audio player, and embedded video, so each day's episode has a
  shareable, human-readable web page — not just downloadable files.
- Upload the video to YouTube (new playlist).
- A short **case-study segment**: one real database-security incident per day (when one exists in
  the lookback window), covering what happened, root cause, and resolution/mitigation.

### 5.2 Out of Scope (V1 — candidates for later phases)
- A dedicated Android/mobile app (the existing `shahbaz-daily-updates` Android app is tech-show
  specific; whether this show gets a mobile surface is a later decision, not v1).
- Push notifications / Firebase integration (no app to push to yet — see above).
- Multi-language support.
- Client-specific or engagement-specific content of any kind (see Section 4's confidentiality
  boundary — permanent exclusion, not a phase-2 item).
- Any content that includes working exploit code, PoCs, or step-by-step attack instructions (see
  Section 9 — permanent exclusion).
- Advanced multi-voice/dialogue format — v1 is single-narrator, matching the existing shows.

## 6. High-Level Solution Overview

Same pipeline shape already proven in `shahbaz-daily-updates`, reused rather than rebuilt:

1. **Collect** — Pull the last 24 hours of items per topic from vendor docs/blogs/RSS, GitHub
   Security Advisories/CVE feeds relevant to the tracked products, and community/news sources.
2. **Filter & Rank** — Deduplicate and rank by relevance/significance so the episode stays within
   its target runtime; drop noise.
3. **Summarize & Script** — LLM turns raw items into one cohesive narration script: per-topic
   roundup + the day's case-study segment, in simple but technically precise English.
4. **Narrate (TTS)** — Convert the script to audio (single narrator voice).
5. **Build video** — Cover art + captions burned in, synced to the narration's own timing data.
6. **Publish** — Push audio + transcript + video as GitHub release assets, generate and commit a
   new **GitHub Pages article page** for the day (written summary + embedded audio player +
   embedded video), and upload the video to YouTube (own playlist) — with the vendor/community
   source links kept in the transcript/article for follow-up and for citing in client
   conversations.

```
[Thales docs/blog, Imperva blog/community, CVE/advisories, security news/community sites]
   -> [Collector] -> [Filter/Rank] -> [LLM Script Writer: roundup + case study]
   -> [TTS] -> [Video build]
   -> [Publish: GitHub release assets] -> [Publish: GitHub Pages daily article]
   -> [Upload: YouTube]
```

## 7. Content Topics (V1 tracked list)

- **Thales CipherTrust Manager** — releases, patches, add-ons/connectors, known-issue and
  end-of-life advisories, docs/knowledge-base updates.
- **Thales data-protection portfolio (adjacent)** — other Thales data-security products
  referenced from the same docs/support ecosystem when relevant (e.g., Luna HSM, Data Security
  Platform integrations), kept as a lighter-weight adjacent category rather than a full topic of
  its own in v1.
- **Imperva Data Activity Monitoring (DAM)** — product news, version changes, advisories,
  community discussion.
- **Database security (general)** — vendor-agnostic news: CVEs affecting major database
  platforms, breach reports where a database was the point of compromise, research/advisory
  content from major security outlets.
- **Case studies / incidents (worldwide, real-time)** — actual publicized incidents relevant to
  database security or the tracked products, with resolution detail when publicly available.

> Topic list must be config-driven (mirrors the existing project's `sources.yaml` pattern), so
> topics/sources can be added or removed without code changes.

## 8. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | System shall collect content published within the trailing 24 hours for each configured topic. |
| FR-2 | System shall deduplicate and rank items, dropping low-signal/noise items to fit the target runtime. |
| FR-3 | System shall generate a single narration script per day covering all topics with meaningful updates (topics with no news are skipped or briefly noted). |
| FR-4 | Script tone shall be simple, conversational English, but precise on product names, version numbers, and CVE IDs — this content may be reused in client conversations. |
| FR-5 | Where applicable, script shall mention: what changed, affected versions, and — for incidents — root cause and resolution/mitigation. |
| FR-6 | System shall convert the script into an audio file. Every scheduled video shall contain at least 30 minutes of measured narration. Quiet days use rotating, cited historical CVE references rather than invented filler. |
| FR-7 | System shall render a captioned video from the audio + script, reusing the existing pipeline's cover-art/caption approach. |
| FR-8 | System shall publish the daily audio + transcript + video as GitHub release assets in the project's repo. |
| FR-9 | System shall generate and publish a new **GitHub Pages article page** each day: a written summary of the episode with an embedded audio player and embedded video, at a stable per-date URL, plus an updated index/archive page linking to all past daily articles. |
| FR-10 | System shall upload the daily video to YouTube (own playlist), with AI-generated-narration disclosure per platform policy. |
| FR-11 | Each episode's transcript/article shall include source links/citations for every claim, for verification and safe reuse with clients. |
| FR-12 | System shall include a daily case-study segment when a real, publicly reported database-security incident exists in the lookback window; it is skipped (not invented) on days without one. |
| FR-13 | System shall never include working exploit code, proof-of-concept payloads, or step-by-step attack/exploitation instructions in any segment (see Section 9). |
| FR-14 | System shall log pipeline run status (success/failure per stage) for troubleshooting. |

## 9. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Reliability | Daily pipeline completes on a fixed schedule with a defined buffer before the target-ready time; alert/fallback on failure. |
| Accuracy | Summaries must not fabricate facts, CVE IDs, version numbers, or resolutions; every notable claim traceable to a source link. |
| **Dual-use safety** | **Hard guardrail, same principle as the existing tech show's content-safety gate but stricter given the subject matter:** scripts report *that* a vulnerability/incident happened and *how it was mitigated*, never *how to reproduce or exploit it*. No exploit code, no attack payloads, no step-by-step compromise instructions, ever — enforced by a prompt-level instruction plus an automated per-segment check; a segment still flagged after one retry is withheld that day rather than published. |
| Confidentiality | No client-identifying or engagement-specific data is ever an input to this pipeline — public sources only (Section 4). |
| Cost | Target $0/month, reusing the existing project's free/open-source stack decisions (Section 15) rather than re-evaluating alternatives — the friend's own free-tier accounts (Section 13), not shared ones. |
| Compliance | Content collection respects source sites' ToS/robots.txt; prefer official APIs/RSS over scraping where available. |
| Scalability | Architecture allows adding more tracked products (e.g., another Thales or Imperva product line) without redesign. |
| Storage | Retain episode archive (audio + transcript + video) for a defined retention period (open question, Section 17). |

## 10. Candidate Content Sources (to be finalized)

- **Thales** — Thales docs portal / knowledge base and support/community site (Trust Community),
  Thales Blog, CipherTrust Manager release notes, GitHub Security Advisories for any Thales
  open-source components.
- **Imperva** — Imperva Blog, Imperva Community, DAM release notes/documentation updates.
- **Database security (general)** — NVD/CVE feeds filtered to major DB platforms and the tracked
  products; major outlets (e.g., BleepingComputer, The Hacker News, SecurityWeek, Dark Reading,
  CSO Online, KrebsOnSecurity); breach-tracking sites for the case-study segment.
- **Community signal** — Reddit (r/cybersecurity, r/netsec, r/databreaches), Hacker News (Algolia
  Search API) — used for "what's the buzz" and independent incident write-ups.

> Preference order, same as the existing project: **official vendor API/RSS/docs first**,
> scraping only as a fallback where no structured source exists.
>
> **Action for you before the first real run:** Thales's and Imperva's public RSS/feed
> availability is unverified as of this draft — confirm actual feed URLs (or whether their
> docs/community sites require scraping instead) before wiring up the collector.

## 11. Podcast Script Structure (per episode)

1. Intro (date, what's covered today) — ~15–20 sec.
2. Per-topic segments (only topics with real news that day): CipherTrust Manager, Imperva DAM,
   general database security — what changed, affected versions, why it matters for someone
   running or advising on these systems.
3. **Case Study segment** — one real, publicly reported database-security incident: what
   happened, root cause, resolution/mitigation, and the practical takeaway for a consultant
   advising clients. Skipped on days with nothing genuinely reportable, not invented.
4. Outro (recap + sign-off).

Target length: ~4,500–5,500 spoken words and at least 30 minutes of measured narration. Current developments remain distinct from a bounded historical CVE reference section. Products, services, dates, countries, locations, and industries are included only when explicit in cited evidence; missing attributes are identified as unreported.

## 12. Delivery / Consumption (V1)

Three publish targets every day, all from the same pipeline run, all under the friend's own
accounts:

- **GitHub Releases:** raw audio, transcript, and video files published as release assets in
  **the friend's own new repo** (e.g. `is-security-update`, under his GitHub account, not a fork
  of or a repo inside `shahbaz-daily-updates`) — the durable file-hosting layer other surfaces
  link back to.
- **GitHub Pages (the daily website):** a static site, built from the same repo, that gets a new
  page each day at a stable URL (e.g. `/episodes/2026-09-13/`) containing:
  - A written article version of that day's briefing (generated from the script/transcript, not
    a raw dump of it — readable as a stand-alone blog post).
  - An embedded HTML5 `<audio>` player pointing at that day's GitHub Release audio asset.
  - An embedded video (either the YouTube embed once uploaded, or the release video asset directly).
  - Source links/citations carried over from the transcript (FR-11).
  - An **index/archive page** auto-updated to list every past daily article (newest first),
    so the site is browsable, not just a pile of dated URLs.
  This is the "GitHub website" the friend can share a single link to, browse history on, and
  point clients at — GitHub Releases alone (files with no page) don't satisfy that on their own.
- **YouTube:** daily video uploaded to a dedicated playlist on **the friend's own YouTube
  channel** (resolves the earlier open question — since upload requires OAuth against a channel
  he controls, it cannot be a shared/existing channel belonging to the original author).

No dedicated mobile app in v1 (Section 5.2); the friend and anyone he shares the link with
consume via the GitHub Pages site (primary), YouTube, or the raw GitHub release assets.

## 13. Deployment & Ownership Model (separate PC, separate GitHub account)

This project is built **for** the friend but must run entirely **under his own identity** —
nothing here depends on the original author's machine, GitHub account, or API keys.

### 13.1 What's independent vs. what's reused
- **Reused:** the pipeline *design/pattern* from `shahbaz-daily-updates` (collect → script → TTS
  → video → publish → YouTube) and, practically, a copy of its pipeline source code as a starting
  point — this is architecture reuse, not a running dependency.
- **Independent (must be created fresh, owned by the friend):** GitHub account/repo, GitHub
  Actions runs/minutes, Groq API key, Reddit API app (if used), Google Cloud project + OAuth
  client, YouTube channel + refresh token, and every Actions secret. None of the original
  project's credentials, quotas, or channels are shared or reused.

### 13.2 One-time setup on his PC (only needed once, not for daily operation)
The daily pipeline itself runs unattended in GitHub Actions' cloud runners — his PC does **not**
need to stay on or be involved in day-to-day operation. His PC is only needed for:
1. Cloning the new repo and doing initial local test runs (Python 3.11+, `pip install -r
   pipeline/requirements.txt`).
2. The **one-time interactive YouTube OAuth flow** (`pipeline/auth/youtube_oauth_setup.py` or
   equivalent) — this must run locally because it opens a browser for him to sign into his own
   Google/YouTube account and grant upload access; it cannot run inside GitHub Actions.
3. Pushing the resulting refresh token into GitHub Actions secrets (never committed to the repo).

### 13.3 Accounts & credentials the friend must create (all free tier, all his own)
| # | Account/resource | Used for | Resulting secret(s) |
|---|---|---|---|
| 1 | GitHub account + new repository | Hosts code, runs Actions, publishes releases | n/a (repo itself) |
| 2 | GitHub Pages enabled on that repo (Settings → Pages → source: `docs/` folder on `main`) | Serves the daily article site (Section 12) | n/a — no external account, just a repo setting; Actions needs `contents: write` permission to commit the generated pages |
| 3 | [Groq Cloud](https://console.groq.com) account | Free-tier LLM API for script writing | `GROQ_API_KEY` |
| 4 | Reddit API app (optional — script type, free) | Community-signal collection | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` |
| 5 | Google Cloud project with YouTube Data API v3 enabled + OAuth Desktop client | Authorizes daily video upload | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` |
| 6 | One-time local OAuth run (Section 13.2) against his own YouTube channel | Mints the long-lived upload credential | `YOUTUBE_REFRESH_TOKEN` |
| 7 | A YouTube playlist on his channel (existing or new) for this show | Target for uploads | `YOUTUBE_PLAYLIST_ID` |
| 8 | GitHub repo → Settings → Secrets and variables → Actions | Stores all of the above for the scheduled workflow | all secrets above |

No Firebase project is needed (Section 5.2 — no app/push notifications in v1). GitHub Pages is
the one delivery surface here that needs **no external account at all** — just enabling it on the
repo he already owns from item 1.

### 13.4 Risk carried over: YouTube OAuth verification
Same risk the original project documents: an OAuth app that hasn't been through Google's
verification review is stuck in "Testing" status, and its refresh tokens expire after **7 days**
— fine for local testing, but it will silently break unattended daily uploads once scheduled.
**Decision needed from the friend:** either go through Google's (free) OAuth verification process
for a non-expiring token before relying on this daily, or accept manually re-running the local
OAuth step every ~7 days until verified.

### 13.5 Ownership of output
Because everything runs under his account, the friend owns the repo, the published
audio/video/transcripts, and the YouTube channel/videos outright — this is not a shared or
co-branded output of `shahbaz-daily-updates`.

## 14. Assumptions

- The pipeline can reuse `shahbaz-daily-updates`'s proven stack decisions wholesale (LLM, TTS,
  video build, GitHub Actions orchestration, YouTube upload) rather than re-evaluating them, per
  the explicit request for a "similar pipeline" — but reused as a *pattern/code starting point*
  only, never as a shared runtime dependency (Section 13.1).
- Single narrator voice, English-only, is acceptable for v1.
- A backend/cloud automation component is required (LLM + TTS + scraping can't run believably
  on-device); this is a scheduled GitHub Actions job, not an interactive app, and not something
  that needs his PC running continuously.
- Public-source-only content is sufficient for the stated goal (staying current, having citable
  case studies) — no need to ingest any private/licensed threat-intel feed for v1.
- The friend is comfortable creating and managing his own free-tier developer accounts
  (Section 13.3) — this BRD assumes no technical assistance from the original author beyond the
  design/code handed off.

## 15. Proposed Technology Stack (reuse of the confirmed `shahbaz-daily-updates` stack)

Decision proposed: this project is a **second, fully independent repo** (own account, own
credentials — Section 13) running the **same pattern** already confirmed in
`shahbaz-daily-updates` Section 14 — not a new evaluation. Every component below is $0/month at
this project's scale (single show, one 30–40-minute episode/day), on the friend's own free-tier
accounts.

| Stage | Tool | Notes |
|---|---|---|
| Content collection | RSS/Atom (`feedparser`), GitHub Security Advisories API, NVD/CVE feed, HN Algolia API, Reddit API (`PRAW`) | Same libraries as the existing project; new `sources.yaml` for this show's topics/feeds. |
| AI scripting | Groq free-tier API, open-weight model (e.g. `llama-3.3-70b-versatile`) | Same provider/model family as the existing project. |
| Text-to-speech | Kokoro-82M (open-weight, self-hosted, CPU) | Same TTS engine and convention as the existing project. |
| Video build | `ffmpeg` cover-art + burned-in captions from TTS timing data | Reuses the existing project's `video/build_video.py` approach. |
| Orchestration | GitHub Actions scheduled workflow | Own schedule/cron, staggered from the existing project's jobs to avoid Groq rate-limit contention. |
| Publish (files) | GitHub Release assets (audio, transcript, video) | Matches the existing project's GitHub-release fallback path; no Firebase needed since there's no app yet. |
| Publish (website) | GitHub Pages, built from plain Markdown/HTML templates committed by the workflow (no Jekyll/site-generator dependency needed for one page/day plus an index) | New pipeline stage, e.g. `publish/site.py`: renders the day's article page + rewrites the index page, commits both to the repo's Pages source (`docs/` folder on `main`, simplest option — no separate `gh-pages` branch to manage). |
| Video hosting | YouTube Data API v3 upload | New playlist on the friend's own channel (Section 12/13). |

### 15.1 Dual-use safety implementation note

Reuses (imports/adapts, doesn't reinvent) the existing project's `check_segment_safety` /
`ContentSafetyError` pattern from `pipeline/common.py` in `shahbaz-daily-updates`, with an
extended system prompt specific to this show: no exploit code, no attack payloads, no
step-by-step compromise instructions, in addition to the existing no-vulgarity/no-unethical-use
rules.

### 15.2 Cost Summary

| Component | Tool | Monthly cost |
|---|---|---|
| Content collection | RSS + CVE/GHSA APIs + HN + Reddit API | $0 |
| AI scripting | Groq free-tier API | $0 |
| Text-to-speech | Kokoro-82M (self-hosted) | $0 |
| Video build | ffmpeg | $0 |
| Orchestration | GitHub Actions | $0 |
| Publish/hosting | GitHub Releases + GitHub Pages + YouTube | $0 |
| **Total** | | **$0** |

## 16. Future Enhancements (Phase 2+)

- A mobile/app surface (own app, or a show toggle inside a future app, similar to how "Project
  Manager's Room" was added as a second show in `shahbaz-daily-updates`).
- Push notifications once there's an app to push to.
- Weekly "top incidents" recap episode for client-facing sharing.
- Expand tracked-product list (additional Thales product lines, other DAM/database-security
  vendors relevant to the friend's engagements).
- Pursue Google OAuth verification (Section 13.4) once the show is stable, to remove the 7-day
  token-refresh risk.

## 17. Open Questions

**Resolved by this update:**
- ~~Repo/hosting~~ — standalone GitHub repo, under the friend's own account (Section 13).
- ~~YouTube channel~~ — the friend's own channel, new playlist (Section 12/13.3).

**Still open:**
1. **Friend's identity/details:** His GitHub username and chosen repo name, and whether he
   already has a YouTube channel to reuse or needs a new one — needed before Section 13's
   accounts can actually be created.
2. **Role/context confirmation:** Does his day-to-day role actually match the
   consultancy/government-client framing this BRD reuses from the original author (Section 4)?
   If not, Section 7's topic list and Section 11's client-facing framing may need adjusting.
3. **Schedule/ready-time:** What daily ready-time should this target (the original tech show
   targets 8:00 AM AST)? Depends on the friend's own timezone, not the original author's — needs
   his input.
4. **Source confirmation:** Exact Thales and Imperva feed/RSS URLs are unverified as of this
   draft (Section 10) — need confirmation before the collector can be built against them.
5. **Retention:** How long to keep episode archives (GitHub Releases has no hard free-tier
   storage limit at this scale, so this is about signal/noise over time, not cost).
6. **Sharing:** Is this strictly personal to the friend, or intended to be shared with a
   team/clients of his own from day one? Affects whether Section 9's confidentiality/safety
   guardrails need a review step before external sharing.
7. **OAuth verification appetite (Section 13.4):** Is the friend willing to go through Google's
   verification process up front, or accept the 7-day manual re-auth cycle initially?

## 18. Success Metrics (V1)

- Episode successfully generated and published (GitHub release + YouTube) on ≥95% of days.
- Every scheduled video is at least 30 minutes. Quiet days use cited, rotating historical CVE context; invented or repetitive filler is prohibited.
- Zero fabricated facts, CVEs, versions, or resolutions — traceable to source links in the
  transcript.
- Zero instances of exploit code or attack how-to content passing the safety gate (Section 9).
- User (self-reported) finds the content accurate, current, and usable in real client
  conversations.
- Pipeline cost stays at $0/month.

---
*This BRD is a living document — update as decisions are made on the Open Questions in Section 17.*
