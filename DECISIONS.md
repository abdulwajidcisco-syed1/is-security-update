# Decisions and launch blockers

Updated 2026-09-12. User instructions override conflicting draft BRD assumptions.

| Decision | State | Value / next action |
|---|---|---|
| Repository visibility | Confirmed by user | Private. Never change to public as a workaround for hosting. |
| GitHub account | Verified | Windows Credential Manager credential authenticates as `abdulwajidcisco-syed1`; no token in repository files. |
| Repository | Created and verified private | [abdulwajidcisco-syed1/is-security-update](https://github.com/abdulwajidcisco-syed1/is-security-update). |
| CI activation | Permission blocked | Token lacks Workflows write permission; inactive template committed under `ci/`. |
| GitHub Project | Permission blocked | GitHub rejected `createProjectV2`; Projects write permission or authenticated browser setup is needed. |
| Independent ownership | Retained | No credentials, runtime or quota dependence on the original author's deployment. |
| Reference code D09 | Pending | No `shahbaz-daily-updates` code was supplied or available in workspace. Initial foundation is new code; reuse review remains open. |
| Source validation D04 | Pending | Sample endpoints are synthetic and cannot establish real vendor coverage. |
| Schedule D03 | Pending | UTC only for offline examples; no scheduled workflow enabled. |
| Sharing / hosting D06 | Pending | Keep repo and Project private. Decide audience, Pages eligibility, and media hosting before deployment. |
| Persona D02 | Pending | Confirm operator's role and topic emphasis. |
| Retention D05 | Pending | No automatic deletion; local runs excluded from Git. Durable cloud retention is not yet implemented. |
| OAuth D07 / quotas D10 | Pending | No service keys configured; verify actual account eligibility and free limits before live integration. |
| No-news D08 | Pending | Offline run reports empty selection; it does not create a no-news episode. |
| Pages mechanism D11 | Proposed | Explicit Actions deployment after hosting/audience decision; current workflow is tests only. |

## Private repository hosting implications

GitHub Pages from a private repository requires an eligible plan. A private source
repository also does not by itself make a Pages site private. See
[GitHub Pages creation documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).
Private repository Release assets are not anonymous public media hosting. Do not
put a token in an audio/video link to work around authentication.

Before P09–P12 publication, choose an authorized delivery architecture compatible
with private source code, intended audience, and the $0 target. No paid upgrade or
public hosting resource is assumed authorized by the private-repository request.
