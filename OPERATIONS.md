# Operations guide

## Production surfaces

- Repository: `abdulwajidcisco-syed1/is-security-update` (public because GitHub Pages is public).
- Website: `https://abdulwajidcisco-syed1.github.io/is-security-update/`.
- GitHub Releases: one `episode-YYYY-MM-DD` release per UTC edition.
- YouTube: one private video per UTC edition, inserted into the configured playlist.
- Daily workflow: `.github/workflows/daily-publish.yml`, fixed 03:00 UTC window end.

The workflow runs on GitHub-hosted infrastructure. The operator PC is needed only for initial YouTube OAuth authorization or later reauthorization.

## Required repository secrets and variable

Configure these Actions secrets; never place their values in files, issues, logs, or workflow inputs:

- `GROQ_API_KEY`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `YOUTUBE_PLAYLIST_ID`

`PILOT_ENABLED` is the schedule switch. Set it to `true` only for an approved pilot or normal operation. Set it to `false` to pause scheduled publication. Manual runs remain available and require the confirmation value `RUN`.

The workflow uses the GitHub-provided token with only `contents: write`, `pages: write`, and `id-token: write`. It has a 90-minute publication budget and no paid fallback.

## Run and monitor

Scheduled runs start daily at 03:00 UTC and use the half-open window ending at `YYYY-MM-DDT03:00:00Z`. Open **Actions → Daily briefing publication** to inspect the run summary and stage logs. A complete run must show:

1. a checksummed GitHub Release,
2. a verified private YouTube video and playlist insertion,
3. a successful Pages deployment,
4. HTTP success for the archive and dated episode.

A failed or skipped destination means the edition is incomplete. GitHub Actions notifications and the failed run are the initial alert channel.

For an authorized manual run, open **Daily briefing publication → Run workflow**, enter `RUN`, and select the voice. Do not launch multiple manual runs for the same edition; workflow concurrency serializes accidental overlap.

## Resume and recovery

Rerun the failed workflow for the same UTC date. If `episode-YYYY-MM-DD` already exists, the workflow downloads its seven release assets, validates the manifest checksums, and resumes from that checkpoint. It then reconciles the release, searches YouTube for the exact edition marker, restores the playlist relationship, rebuilds the site, and deploys Pages. It does not blindly create a second release or video.

If checksum validation fails, stop. Preserve the failed run and compare the release assets with `manifest.json`; do not delete or replace remote assets until the discrepancy is understood.

If YouTube OAuth is revoked or expired:

1. Set `PILOT_ENABLED=false`.
2. Run `python -m pipeline.auth.youtube_oauth_setup` locally with the operator-owned OAuth client.
3. Replace `YOUTUBE_REFRESH_TOKEN` in repository Actions secrets.
4. Run **YouTube OAuth preflight**.
5. Resume the daily workflow manually with `RUN`.

If Groq rejects structured output, the generator retries schema-invalid responses at most twice. Authentication, quota exhaustion, safety rejection, or repeated invalid output remains a hard failure.

## Corrections

Pause the schedule before correcting published facts. Record the affected edition and evidence. Correct the source-backed episode and regenerate all dependent transcript/media files; publish a clearly identified replacement release rather than silently changing checksummed assets. Update or replace the YouTube video and Pages edition, verify every destination, and record the correction in the acceptance log. Never remove the original evidence trail without an explicit retention decision.

## Retention

- Pages preserves the newest 30 editions by importing only dated pages and their bounded media from the same HTTPS site before each deployment.
- Workflow publication records are retained for 30 days.
- GitHub Releases are durable checkpoints and are not automatically deleted.
- YouTube videos remain private unless the operator explicitly changes the publication policy.

Review storage before changing the Pages retention range. The CLI accepts 1–90 retained editions.

## Pilot and go-live

Use `PILOT_LOG.csv` for seven consecutive scheduled editions. For each day, record run URL, release URL, video ID, page URL, start/end time, coverage, content review, media review, cost, and defects. A failed day must be corrected and its affected scenario rerun. After seven days, complete `ACCEPTANCE.md`; the 95% reliability objective is measured separately over the following 30 days.

## Local validation

Install Python 3.12 and the pinned requirements. Run:

```powershell
python -m unittest discover -v
python -m pipeline.run --dry-run --fixture tests/fixtures/news.json --window-end 2026-09-12T08:00:00Z
```

Local `.tools`, `preview`, and `runs` directories are development artifacts and must remain untracked.
