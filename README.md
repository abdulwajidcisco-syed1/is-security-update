# IS Security Update

Independent daily database-security briefing pipeline for CipherTrust Manager,
Imperva DAM, adjacent Thales products, and general database security.

**Status: live review-preview implementation.** This version collects allowlisted public RSS, NVD, and Hacker News sources, filters and ranks a fixed 24-hour window, generates an evidence-constrained Groq briefing, renders an animated captioned video and static review article, and writes resumable/checksummed run artifacts. YouTube OAuth and configured playlist ownership are verified.

## Requirements and plan

- [Business requirements](BRD.md)
- [Software requirements](SRS.md)
- [Implementation action plan](ACTION_PLAN.md)
- [Decisions and launch blockers](DECISIONS.md)
- [Implementation status](IMPLEMENTATION_STATUS.md)
- [Private implementation Project](https://github.com/users/abdulwajidcisco-syed1/projects/1)
- [GitHub issue backlog](BACKLOG.md)
- [Validation report](TEST_REPORT.md)
- [Source register](SOURCE_REGISTER.md)
- [Operations](OPERATIONS.md)

## Run locally

Python 3.11+ is required (CI uses 3.13).

```sh
python -m pip install -r pipeline/requirements.txt
python -m unittest discover -s tests -v
python -m pipeline.run --dry-run --fixture tests/fixtures/news.json --window-end 2026-09-12T08:00:00Z
python -m pipeline.run --dry-run --fixture tests/fixtures/news.json --window-end 2026-09-12T08:00:00Z --resume
```

Outputs: `runs/is-security-update/2026-09-12/manifest.json`,
`selected_items.json`, and `quarantine.json`. Generated output and local tooling
are ignored by Git. A repeated edition requires `--resume`; changing its inputs
or corrupting artifacts fails rather than silently overwriting the edition.

Offline fixtures and live allowlisted source adapters are available. UTC is an explicit development default; operator timezone and daily ready-time remain undecided.

## Privacy and publishing

The source repository is to remain **private**, per the owner's instruction.
Publication is disabled in configuration and unavailable in code. CI runs from `.github/workflows/ci.yml` using synthetic fixtures with no deployment
permissions or daily publishing schedule.

A private repository changes the original hosting assumptions: private Release
assets require authentication, and GitHub Pages from private repositories requires
an eligible plan. Public or private content delivery must be decided separately;
see [DECISIONS.md](DECISIONS.md). Never embed authentication tokens into media URLs.

No client data, secrets, OAuth files, or raw private material should be added.

## Live review preview

Run the manual **Live briefing preview** GitHub Actions workflow. It collects the trailing 24 hours, filters relevant stories, generates a cited and safety-checked briefing with Groq, renders a static article, and uploads seven-day review artifacts. It has read-only repository permissions and no publication step.

## YouTube destination preflight

Run the manual **YouTube OAuth preflight** workflow to refresh OAuth, identify the authorized channel, and verify that it owns the configured playlist. The workflow is read-only and does not upload or publish media.

## Operations and acceptance

- [Operations guide](OPERATIONS.md)
- [Integrated acceptance record](ACCEPTANCE.md)
- [Seven-day pilot log](PILOT_LOG.csv)
- [Implementation status](IMPLEMENTATION_STATUS.md)
