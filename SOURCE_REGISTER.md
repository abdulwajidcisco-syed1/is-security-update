# Source register

No production feed has been validated yet. Do not represent synthetic source data
as news or enable network collection based solely on this register.

| Source | State | Required work |
|---|---|---|
| CipherTrust Manager official release notes/advisories | Candidate | Verify exact public endpoint, publication/update timestamps, permitted access and sample item. |
| Imperva DAM official release notes/advisories | Candidate | Verify exact public endpoint and distinguish DAM from unrelated Imperva products. |
| Adjacent Thales data protection | Candidate | Verify relevant public sources and lighter topic weight. |
| Database-security news / CVE sources | Candidate | Verify official feeds/API constraints and product relevance mapping. |
| Community feeds | Optional candidate | Confirm access/rights, then treat as secondary signal. |
| `fixture-vendor`, `fixture-news` | Synthetic offline only | `example.org` placeholders; no network requests, no publishing. |

Each production entry must record source ID, verified endpoint, adapter,
topic IDs, access/policy review date, timestamp basis, sample payload and health.
Live collectors also need hostname/IP resolution and redirect controls; the
current URL syntax check is not a complete SSRF defense.
