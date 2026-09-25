# global-remote-job-search

Searches suitable senior Go/backend positions at employers outside China that allow candidates to work remotely while based in China. It uses public job APIs/ATS sources, generates Markdown reports, and optionally pushes Feishu cards. It does not automatically apply for jobs, send emails, log into recruitment platforms, or bypass any restrictions.

## Configuration

Run the interactive setup for the first use:

```bash
python3 scripts/job_search.py --setup
```

The script will ask for candidate location/time zone, excluded employer countries (China by default), backend experience, optional resume path, skills, target roles, matching threshold, result count, and job freshness requirements. Unknown employer countries are retained and labeled for verification. It then generates `config/private.json` with permission mode `600`.

This file is excluded by `.gitignore`.

The resume is only checked locally to verify that the path exists. The script does not read, upload, or output resume content.

The webhook URL will never be requested or stored in the configuration file.

`preferences.max_age_days` controls job freshness. The default value is 7 days. When enabled, jobs without publication dates or jobs older than the threshold will not be included in notifications.

Results are sorted by publication date (newest first) and match score. All qualifying unseen jobs are retained without a result-count cap. For stricter daily reports, set the freshness value to 3.

Blockchain, Web3, cryptocurrency, crypto-exchange, DeFi, NFT, on-chain, smart-contract, Solidity, Ethereum, and Bitcoin roles are excluded before scoring. Ordinary cryptography and security-engineering roles remain eligible unless the job explicitly ties them to cryptocurrency or Web3.

Enable job sources in `config/sources.json`. For Greenhouse, Lever, and Ashby, the `board_token`, `site`, and `board` fields are public recruitment page identifiers, not secrets.

To require specific programming languages, add a private preference such as `"required_languages": ["Go", "Java", "Python", "Kotlin"]`. A job must explicitly mention at least one configured language; infrastructure, database, and cloud keywords do not count as a language match.

The Muse is supported through its official Jobs API. Register an app, set `THEMUSE_API_KEY` in the runtime environment, then enable `The Muse API` in `config/sources.json`. The integration reads bounded newest-first `Flexible / Remote` pages and preserves any accompanying country or city for China-remote filtering.

`config/company_watchlist.json` is an optional private company discovery list; copy `config/company_watchlist.example.json` to create it locally. `active` entries have verified official careers/ATS links; `excluded` entries remain visible but are not queried because they are Web3/crypto employers; `manual_review` entries are ambiguous names, recruiters, local-only employers, or companies without a verified public feed. A manual-review entry must not be promoted to an automated source until its official company identity and permitted public endpoint are verified.

`config/discovery_catalogs.json` tracks curated directories used to discover additional job boards and remote-first companies. Awesome Remote Job is integrated in this mode. Catalogs and their README descriptions are leads only: every source still requires an independent access-policy check, and every recommended vacancy must be confirmed on a live official company Careers/ATS posting with a China-compatible location policy.

Before adding new sources, read `references/source-policy.md`.

## Feishu Company Exclusion Table

`config/company_exclusion_table.json` can point to a Feishu Base table containing companies that must not be pushed again. The configured `公司名称` column is read live before every non-fixture run. Matching ignores case, harmless punctuation, corporate suffixes, Markdown-link formatting, and common domain suffixes. If the table is unavailable or authorization has expired, the run stops without sending jobs.

Otherwise-qualified jobs removed by this table are still shown in a separate audit section in the Markdown report and Feishu card. They are not counted as recommendations. The audit displays up to 30 jobs and always shows the full filtered count.

## Company Information and Chinese Job Content

Reports and Feishu cards display company country/region, industry, employee size, a Chinese company analysis, and a Chinese job analysis covering responsibilities, requirements, stack, match, and China-remote feasibility.

When recruitment APIs explicitly provide company information, the data is used directly.

Otherwise, the system performs low-frequency Wikidata lookups with exact company-name matching for selected companies and attaches reference links.

You can copy:

```bash
config/company_profiles.example.json
```

to:

```bash
config/company_profiles.json
```

and privately add or override verified company information such as:

* `country`
* `industry`
* `size`
* `analysis_zh`
* `source_url`

based on official website verification.

This file will not be committed to Git.

If reliable information is unavailable, the system displays:

```
Pending verification
```

It does not infer company headquarters based on remote work locations.

You can disable public company information lookup through:

```json
company_enrichment.enabled
```

in the private configuration.

Chinese job content is generated by the script based on clearly stated responsibilities, experience requirements, technical keywords, scoring, and remote-work wording from English job descriptions. Company analysis uses only verified source/profile fields and explicitly leaves unavailable facts pending verification.

It provides a structured Chinese explanation while keeping the original English summary for verification.

It is not a legally binding translation.

Important job requirements should always be verified from the original English application page.

## Feishu Webhook

The webhook URL is only read from environment variables. Never store it in files.

Example:

```bash
export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/...'
```

The script never prints the webhook URL.

Use dry-run mode first to inspect:

```bash
reports/*-payload.json
```

## Manual Execution

```bash
cd ~/.codex/skills/global-remote-job-search

python3 scripts/job_search.py --dry-run

python3 scripts/job_search.py --self-test

python3 scripts/job_search.py
```

The final command requires `FEISHU_WEBHOOK_URL` and sends the actual notification.

`--dry-run`:

* Does not send notifications
* Does not update persistent deduplication state

During normal execution, `state/seen.json` is updated only after a successful push.

If there are no new jobs:

* Only logs are written
* No empty notification is sent

## macOS Daily Schedule at 10:00 AM Beijing Time

Using launchd:

Copy:

```bash
references/com.codex.global-remote-job-search.plist.example
```

to:

```bash
~/Library/LaunchAgents/
```

and replace the paths.

The webhook should be provided through a restricted-permission wrapper script or:

```bash
launchctl setenv
```

Do not write the webhook URL directly into the plist file.

Using cron:

(Your machine timezone must be `Asia/Shanghai`.)

```cron
0 10 * * * cd "$HOME/.codex/skills/global-remote-job-search" && /usr/bin/python3 scripts/job_search.py >> logs/cron.log 2>&1
```

Do not put the webhook URL in plain text inside crontab.

## GitHub Actions / Cloud Server

The code can be stored in a public repository, but never commit:

* `config/private.json`
* resumes
* reports
* logs
* deduplication state
* `.env` files

Refer to:

```bash
references/github-actions.yml.example
```

The `FEISHU_WEBHOOK_URL` must be stored in GitHub Actions Secrets.

Private configuration should be generated interactively by the runtime environment or injected temporarily through Secrets.

A resume file is not required for execution. A structured skills configuration is sufficient for job matching.

## MVP and Future Improvements

Default enabled sources:

* Remotive
* Arbeitnow
* Himalayas
* Jobicy
* Remote OK public API
* We Work Remotely official RSS

Generic adapters are available for:

* Greenhouse
* Workable
* Lever
* Ashby

These can be enabled by providing company identifiers.

The following sources are marked as manual review only:

* LinkedIn
* Y Combinator
* Glassdoor
* FlexJobs
* Remote.com
* Wellfound
* Jobgether
* Awesome Remote Job discovery catalog
* Real Work From Anywhere
* Remote Backend Jobs
* JobsCollider
* AI Dev Jobs
* Golangprojects
* WAHJobQueen
* Paybump
* Jobright
* Après

Future improvements may include:

* More Remote OK / We Work Remotely RSS sources
* More company ATS integrations
* Company career page RSS feeds
* Compliant secondary verification of job details

Before enabling any new source, verify its terms, robots rules, APIs/RSS availability, and reasonable request frequency.

## Coverage diagnostics and regression checks

Remote OK combines its public API with category JSON feeds and deduplicates by job ID. These bounded recent feeds do not provide complete historical coverage. Reports include per-source fetch counts, filtering reasons, and partial failures.

Indeed and Indeed China remain manual discovery sources; verified employer ATS boards are queried separately. Neither Indeed site is configured for automatic scraping.

Run offline regression checks with `python3 tests/test_regressions.py`. No personal configuration or live notifications are needed. Keep populated company watchlists, exclusion-table credentials, candidate profiles, resumes, and generated reports local; publish only blank examples.
