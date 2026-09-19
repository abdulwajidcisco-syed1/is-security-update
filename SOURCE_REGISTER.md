# Source register

Reviewed 2026-09-20. “Verified live” means the endpoint responded and the pipeline normalized its payload. “Verified manually” means an official public page was inspected but is not eligible for automated 24-hour collection because it lacks a stable structured feed or trustworthy item timestamps.

| Source | Endpoint | Access / adapter | State | Timestamp rule | Role, health, and fallback |
|---|---|---|---|---|---|
| CISA Cybersecurity Advisories | `https://www.cisa.gov/cybersecurity-advisories/all.xml` | Public HTTPS RSS | Verified live 2026-09-19 | Item `pubDate`; timezone required | Official advisory coverage. A source failure is isolated; NVD and other successful sources continue with partial-coverage status. |
| NVD CVE API 2.0 | `https://services.nvd.nist.gov/rest/json/cves/2.0` | Public HTTPS JSON API | Verified live 2026-09-19 | NVD `published`; material updates require separately validated update ordering | Authoritative CVE descriptions and the current fallback for CipherTrust/Imperva product vulnerability mentions. Unauthenticated rate limits apply; 429/5xx/network failures retry at most three times. |
| Hacker News Algolia | `https://hn.algolia.com/api/v1/search_by_date` | Public HTTPS JSON API | Verified live 2026-09-19 | `created_at`; timezone required | Community discovery signal only. It is never authoritative for identifiers, affected versions, or remediation. |
| CipherTrust Manager release notes | `https://thalesdocs.com/ctp/cm/2.19/` and current portal `https://docs-cybersec.thalesgroup.com/` | Official public HTML documentation | Verified manually 2026-09-20 | No stable per-change timestamp/feed established | Official release documentation exists and includes release notes/changelog navigation. The legacy portal says current documentation moved. It is excluded from automated daily collection until a stable, permitted, timestamped endpoint is confirmed. NVD supplies CVE fallback coverage. |
| CipherTrust Manager product page | `https://cpl.thalesgroup.com/en-gb/encryption/ciphertrust-manager` | Official public HTML | Verified manually 2026-09-20 | Page modification time is not a release timestamp | Product context only; never treated as daily news. |
| Imperva Data Activity Monitoring / DSF | `https://www.imperva.com/products/data-security/unified-visibility/` | Official public HTML | Verified manually 2026-09-20 | No item-level release timestamp or structured release feed | Confirms the current DAM capability and documentation/support routes. No public timestamped DAM release/advisory feed was discovered, so the page is excluded from daily ingestion. NVD supplies CVE fallback coverage; operator support-portal material cannot be ingested without a separate authorization and adapter. |
| Fixture sources | `example.org` | Local synthetic fixture | Offline only | Fixed test timestamps | Tests only; never published or treated as news. |

## Coverage decision

The automated baseline uses CISA, NVD, and Hacker News. It can identify vendor-related CVEs through configured aliases, but it does not claim complete product-release coverage for CipherTrust Manager or Imperva DAM. Public vendor pages without dependable item timestamps are not scraped into the trailing 24-hour window. This is an accepted, visible V1 limitation pending a vendor-supported public feed or an explicitly authorized support-portal integration.

## Collection controls

Live collectors allow only configured hostnames, require global-address resolution, reject redirects outside the allowlist, cap responses at 5 MB, use 20-second request timeouts, and isolate individual source failures. Transient network failures and HTTP 429/500/502/503/504 responses use at most three attempts with bounded backoff. All-source failure is an error and is never reported as a quiet news day. Public access does not authorize wholesale republication; generated outputs retain citations and limited evidence excerpts.

## Feasibility and policy notes

- The three enabled endpoints require no paid subscription in the tested mode.
- NVD unauthenticated quota is suitable for one bounded daily query but remains subject to service policy and availability.
- Groq and YouTube account-specific quotas are monitored during the seven-day pilot; no paid fallback is enabled.
- Re-review official vendor access paths when documentation URLs, terms, or authentication requirements change.
