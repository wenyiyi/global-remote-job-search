---
name: global-remote-job-search
description: Search public global remote-job APIs and company ATS boards for backend roles at employers outside China that support working remotely from China, score and deduplicate results, produce a Markdown report, and optionally push a Feishu webhook card. Use for recurring global remote backend job discovery; never apply, email, sign in, or bypass access controls.
---

# Global Remote Job Search

Run `scripts/job_search.py`. Read `README.md` for setup/scheduling and `references/source-policy.md` before changing sources. `config/company_watchlist.json` optionally records privately maintained company discovery notes, their official careers page, automation status, and exclusion reason; use it as an audit trail and keep enabled ATS entries in `config/sources.json` synchronized with it. `config/discovery_catalogs.json` records curated directories such as Awesome Remote Job and the promising boards discovered from them; use these only to expand coverage, never as final job evidence.

When `config/private.json` is absent, run `python3 scripts/job_search.py --setup` and let the user answer the terminal prompts. Do not recreate or publish a filled example config.

## Rules

- Treat `config/private.json` and resumes as private. Never print resume contents, contact details, or `FEISHU_WEBHOOK_URL`.
- Use only official/public ATS endpoints, APIs, RSS, or permitted public pages. Never log in, evade rate limits, solve challenges, or scrape LinkedIn.
- Treat curated resource repositories such as `lukasz-madon/awesome-remote-job` as discovery catalogs, not live job feeds. Periodically review their job-board, aggregator, and remote-company sections, record promising leads in `config/discovery_catalogs.json`, then verify each board's access policy or each company's official Careers/ATS page before enabling automation. A catalog entry, README claim, or generic `Remote` label never proves that a vacancy is live or China-eligible.
- Treat public social posts and community/job marketplaces listed in `config/social_lead_sources.json` only as manually reviewed discovery leads. Extract the named company, role keywords, post date, and source URL, then locate the employer's official careers page or official ATS. Never recommend or push a role unless the official posting is live and its location policy passes the normal China-remote checks. Do not automate login, bidding, bulk collection, anti-bot pages, or private content. Read `references/social-lead-policy.md` when using these leads.
- Send Feishu only in non-dry-run mode when `FEISHU_WEBHOOK_URL` exists. Never persist or log it.
- Never apply, email, or operate recruiting accounts.
- Preserve location/remote wording verbatim in `remote_scope_raw`.
- Make both the job application URL and the source name clickable in Markdown reports and Feishu cards.
- When a source provides compensation, show its original range, currency, and period in both outputs; omit the field when unavailable and do not convert currencies.
- Show company country/region, industry, and employee-size band when supplied by the job source, a cited local company profile, or a conservative exact-label Wikidata lookup. Link the evidence, label missing values `待核实`, and never infer company country from the remote-work location.
- Include a concise Chinese company analysis in both Markdown reports and Feishu pushes. Base it only on cited company fields; do not speculate about reputation, funding, growth, profitability, or the legal employing entity.
- Include a conservative Chinese job analysis in both outputs, covering responsibilities, requirements, detected stack, match score, China-remote feasibility, and application advice, plus an English source excerpt. Do not present rule-based interpretation as a certified full translation.
- The default employer scope is any country/region outside China, while the candidate remains based in China. Exclude a China-based employer only when its company-country label is verified; retain unknown company countries as `待核实`.
- Hard-exclude roles whose work-location rules are limited to countries outside China. Classify conservatively as `可直接投`, `值得确认`, or `不建议投`. Treat an explicit location in the official JD, job title, or job URL (for example `Location: EU (Remote)` or `remote-...-paris`) as higher-confidence evidence than an aggregator's generic `Remote` or `Worldwide` label. A remote boolean never proves worldwide eligibility; preserve any accompanying city/country and reject it when China is outside the allowed geography. Do not infer a restriction merely from a company's headquarters address.
- Treat a plain ATS location containing a single country or city (for example `Philippines` or `Paris, France`) as a work-location restriction, not as uncertain remote eligibility. Only China, Asia/APAC, or explicit global/anywhere wording can pass that check for this candidate.
- When `preferences.required_languages` is configured, require an explicit mention of one of those languages and score only those languages. Databases, middleware, cloud platforms, and other languages must not qualify a role or add skill-match points. Exclude QA/testing, frontend-only and mobile-only roles.
- Maximize discovery coverage through multiple independent sources and official company career pages, while keeping application realism ahead of raw count. Treat 50–100 newly discovered leads and 10–20 high-quality recommendations as coverage targets, never quotas and never reasons to weaken eligibility filters.
- Search broad backend combinations: Go/Golang, Java/Kotlin/JVM, platform, infrastructure, distributed systems, microservices, event-driven systems, Kafka, PostgreSQL, Redis, payment, billing, ledger, SaaS, e-commerce and AI infrastructure.
- Reject engineering-management/people-management roles, relocation/office-required roles, explicit US work-authorization restrictions, and roles that require German, French, or Japanese. Reject full-stack roles when strong React/Next.js expertise is a central requirement; retain backend-leaning full-stack roles.
- Hard-exclude blockchain, Web3, cryptocurrency, crypto-exchange, DeFi, NFT, on-chain, smart-contract, Solidity, Ethereum, and Bitcoin roles. Apply this before recommendation scoring and before the company-table audit list. Do not exclude ordinary security or cryptography work unless the job explicitly connects it to cryptocurrency/Web3.
- Push every unseen job scoring at least the configured threshold (default 3.5), with no result-count cap. Split outbound Feishu content into multiple messages when necessary. Include lower-confidence location wording only when it is not an explicit country exclusion.
- Before scoring or pushing, read the configured Feishu Base company-exclusion table with user identity and exclude jobs whose normalized company name already appears in its `公司名称` field. Treat harmless punctuation, corporate suffixes, Markdown links, and common domain suffixes as equivalent, but do not fuzzy-match unrelated names. If the configured table cannot be read, fail closed and send no jobs.
- In both the Markdown report and Feishu push, add a separate audit section for otherwise-qualified jobs removed by the company-exclusion table. Show the job company, title, application link, matched table company, publication date, source, remote wording, and pre-exclusion score. Do not count these entries as recommendations; cap the displayed audit list at 30 while showing the full filtered count.
- Default to jobs published within the last 7 days (`preferences.max_age_days`), exclude unknown dates while that limit is active, and sort newest publication date first with score as the secondary key.
- Log per-source fetch counts so an empty result can be distinguished from insufficient source coverage or over-filtering.
- Dry-run writes a report and payload preview but does not push or mutate durable state.

```bash
python3 scripts/job_search.py --setup
python3 scripts/job_search.py --dry-run
python3 scripts/job_search.py --self-test
python3 scripts/job_search.py
```

Continue past a failed source, log it, and stop after three exponential-backoff attempts. A failed Feishu push must not mark jobs as sent.
