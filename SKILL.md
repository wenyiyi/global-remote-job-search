---
name: global-remote-job-search
description: Search public global remote-job APIs and company ATS boards for backend roles at employers outside China that support working remotely from China, score and deduplicate results, produce a Markdown report, and optionally push a Feishu webhook card. Use for recurring global remote backend job discovery; never apply, email, sign in, or bypass access controls.
---

# Global Remote Job Search

Run `scripts/job_search.py`. Read `README.md` for setup/scheduling and `references/source-policy.md` before changing sources.

When `config/private.json` is absent, run `python3 scripts/job_search.py --setup` and let the user answer the terminal prompts. Do not recreate or publish a filled example config.

## Rules

- Treat `config/private.json` and resumes as private. Never print resume contents, contact details, or `FEISHU_WEBHOOK_URL`.
- Use only official/public ATS endpoints, APIs, RSS, or permitted public pages. Never log in, evade rate limits, solve challenges, or scrape LinkedIn.
- Send Feishu only in non-dry-run mode when `FEISHU_WEBHOOK_URL` exists. Never persist or log it.
- Never apply, email, or operate recruiting accounts.
- Preserve location/remote wording verbatim in `remote_scope_raw`.
- Make both the job application URL and the source name clickable in Markdown reports and Feishu cards.
- When a source provides compensation, show its original range, currency, and period in both outputs; omit the field when unavailable and do not convert currencies.
- Show company country/region, industry, and employee-size band when supplied by the job source, a cited local company profile, or a conservative exact-label Wikidata lookup. Link the evidence, label missing values `待核实`, and never infer company country from the remote-work location.
- Include a concise Chinese company analysis in both Markdown reports and Feishu pushes. Base it only on cited company fields; do not speculate about reputation, funding, growth, profitability, or the legal employing entity.
- Include a conservative Chinese job analysis in both outputs, covering responsibilities, requirements, detected stack, match score, China-remote feasibility, and application advice, plus an English source excerpt. Do not present rule-based interpretation as a certified full translation.
- The default employer scope is any country/region outside China, while the candidate remains based in China. Exclude a China-based employer only when its company-country label is verified; retain unknown company countries as `待核实`.
- Hard-exclude roles whose work-location rules are limited to countries outside China. Classify conservatively as `可直接投`, `值得确认`, or `不建议投`.
- Accept backend development roles across Go, Python, Java and other server-side stacks; do not require Go in the title. Exclude QA/testing, frontend-only and mobile-only roles.
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
