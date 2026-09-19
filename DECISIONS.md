# Decisions and launch blockers

Updated 2026-09-20. User instructions override conflicting draft BRD assumptions.

| Decision | State | Value / next action |
|---|---|---|
| Repository visibility | Confirmed by user | Public, explicitly authorized to enable GitHub Pages. |
| Operator identity / GitHub account D01 | Verified | GitHub CLI OAuth is stored in the Windows keyring and supports Project/workflow operations. No token is stored in repository files. |
| Repository | Created and verified public | [abdulwajidcisco-syed1/is-security-update](https://github.com/abdulwajidcisco-syed1/is-security-update). |
| CI activation | Enabled and verified | `.github/workflows/ci.yml` is active; [first CI run passed](https://github.com/abdulwajidcisco-syed1/is-security-update/actions/runs/34706412678). |
| GitHub Project | Created and verified private | [IS Security Update](https://github.com/users/abdulwajidcisco-syed1/projects/1); repository linked, all 15 plan issues added with current statuses. |
| Independent ownership | Retained | No credentials, runtime or quota dependence on the original author's deployment. |
| Reference code D09 | Pending | No `shahbaz-daily-updates` code was supplied or available in workspace. Initial foundation is new code; reuse review remains open. |
| Source validation D04 | Pending | Sample endpoints are synthetic and cannot establish real vendor coverage. |
| Schedule D03 | Confirmed V1 baseline | Daily 03:00 UTC (08:30 Asia/Calcutta) with a 90-minute workflow budget. GitHub Actions and the 09:00 Asia/Calcutta Codex monitor provide failure follow-up. |
| Sharing / hosting D06 | Confirmed V1 baseline | Repository, Releases, and Pages are public by explicit authorization. YouTube videos and playlist remain private during pilot; changing video visibility requires an explicit later decision. |
| Persona D02 | Confirmed V1 baseline | English briefing for database-security and data-protection practitioners, emphasizing CipherTrust Manager, Imperva DAM, and general database security; Thales-adjacent news is lower priority. |
| Retention D05 | Confirmed V1 baseline | Pages retains 30 editions; workflow records retain 30 days; Releases and private YouTube videos have no automatic deletion. |
| OAuth D07 / quotas D10 | Partially verified | Operator-owned Groq and YouTube credentials passed live integration. Pilot must record actual usage and exercise OAuth recovery. |
| No-news D08 | Confirmed V1 baseline | A successful collection with no qualifying items publishes a short no-news edition. It never pads with unrelated or invented material. All-source failure remains a failed run. |
| Pages mechanism D11 | Confirmed and implemented | Explicit Actions artifact deployment is live with HTTPS and post-deploy checks. |

## Private repository hosting implications

GitHub Pages from a private repository requires an eligible plan. A private source
repository also does not by itself make a Pages site private. See
[GitHub Pages creation documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).
Private repository Release assets are not anonymous public media hosting. Do not
put a token in an audio/video link to work around authentication.

Before P09ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“P12 publication, choose an authorized delivery architecture compatible
with private source code, intended audience, and the $0 target. No paid upgrade or
public hosting resource is assumed authorized by the private-repository request.

GitHub documents the personal-Project limitation in [fine-grained token limitations](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens-limitations).

Project/workflow setup uses the authorized GitHub CLI OAuth login. The earlier fine-grained token limitation is resolved for this setup through OAuth, not by expanding that token.
