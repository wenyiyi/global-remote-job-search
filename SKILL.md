---
name: global-remote-job-search
description: Search public global remote-job APIs and company ATS boards for China-compatible backend roles across Go, Python, Java and related stacks, score and deduplicate results, produce a Markdown report, and optionally push a Feishu webhook card. Use for recurring remote backend job discovery; never apply, email, sign in, or bypass access controls.
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
- Show company country/region and employee-size band when supplied by the job source, a cited local company profile, or a conservative exact-label Wikidata lookup. Link the evidence, label missing values `待核实`, and never infer company country from the remote-work location.
- Render a conservative Chinese job interpretation (title, responsibilities, requirements and detected stack) plus an English source excerpt. Do not present rule-based interpretation as a certified full translation.
- Hard-exclude country-only roles outside China. Classify conservatively as `可直接投`, `值得确认`, or `不建议投`.
- Accept backend development roles across Go, Python, Java and other server-side stacks; do not require Go in the title. Exclude QA/testing, frontend-only and mobile-only roles.
- Push only unseen jobs scoring at least the configured threshold (default 3.5), capped at 50. Include lower-confidence location wording only when it is not an explicit country exclusion.
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
