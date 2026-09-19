# Source register

Verified 2026-09-19. “Verified” means the public endpoint responded and its payload was successfully normalized during a live smoke test; it does not imply endorsement or complete product coverage.

| Source | Endpoint | Adapter | State | Role / limitation |
|---|---|---|---|---|
| CISA Cybersecurity Advisories | `https://www.cisa.gov/cybersecurity-advisories/all.xml` | RSS | Verified live | Official advisories; relevance filter restricts database topics. |
| NVD CVE API 2.0 | `https://services.nvd.nist.gov/rest/json/cves/2.0` | JSON API | Verified live | Official CVE descriptions; unauthenticated rate limits apply. |
| Hacker News Algolia | `https://hn.algolia.com/api/v1/search_by_date` | JSON API | Verified live | Community signal only; never authoritative for versions/remediation. |
| CipherTrust Manager announcements | `https://www.thalestct.com/ciphertrust-product-announcements/` | HTML candidate | Public page verified manually | No structured feed integrated; exact timestamps and permitted automated extraction must be validated. |
| Current Thales CipherTrust documentation | `https://docs-cybersec.thalesgroup.com/` | Documentation candidate | Public portal found | Product-specific release-change discovery remains unresolved. |
| Imperva blog / DAM documentation | `https://www.imperva.com/blog/` | Candidate | Public site found | Exact DAM release/advisory feed remains unresolved. |
| Fixture sources | `example.org` | Fixture | Offline only | Synthetic tests; never published or treated as news. |

Live collectors allow only the three configured hostnames, resolve them to global addresses, reject redirects outside the allowlist, cap responses at 5 MB, use timeouts, and isolate source failures. Public access does not authorize wholesale republication; previews retain short excerpts and source links for verification.
