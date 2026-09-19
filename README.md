# IS Security Update

Independent daily database-security briefing pipeline for CipherTrust Manager,
Imperva DAM, adjacent Thales products, and general database security.

**Status: live review-preview implementation.** This version validates configuration,
filters a fixed 24-hour window, groups duplicate reports, ranks relevant stories,
preserves evidence metadata, and writes resumable/checksummed local run artifacts.
It does not yet collect live sources, write an AI script, generate audio/video,
or publish an episode. Sample data is visibly synthetic, not vendor news.

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

The current source adapter is fixture-only. YAML configuration reserves RSS/Atom
adapter names but does not implement network fetching yet. UTC is an explicit
development default; operator timezone and daily ready-time remain undecided.

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
