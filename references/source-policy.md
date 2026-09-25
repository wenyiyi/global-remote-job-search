# Source policy

Before enabling a source, record its name, canonical link, filters, access method, and conservative request interval in `config/sources.json`.

Prefer official ATS/public APIs (Greenhouse, Lever, Ashby), official company APIs/RSS, documented remote-board APIs/feeds, then public pages whose terms and robots policy permit modest automation. Mark a source `manual` and disabled when it needs login, has strong anti-bot controls, forbids automation, has unclear authorization, or is unreliable. Never bypass restrictions.

Use a descriptive User-Agent, sequential requests, the configured delay, and at most three retries for 429/5xx/network failures. Respect Retry-After. Do not retry ordinary 4xx responses. Re-check terms periodically.

## Curated discovery catalogs

`lukasz-madon/awesome-remote-job` is a maintained directory of remote-job boards, aggregators, remote-first companies, and supporting resources. Keep it in `config/discovery_catalogs.json` as a coverage-expansion source, not as a job source of record.

- Review only its job-board, aggregator, and companies-with-remote-DNA sections for relevant backend/company leads.
- Prefer sources that expose a documented public API/RSS/MCP or official company Careers/ATS pages. Verify documentation, terms, robots rules, and request limits before changing a lead from `manual` to `automated`.
- For company leads, resolve the official company identity and careers domain. Recommend only a currently live official posting whose complete location policy supports working from China.
- For job-board leads, retain the original employer posting as the application URL whenever it is available. An aggregator's `Worldwide` or `Remote` tag is never sufficient when the full JD contains a country or timezone restriction.
- Ignore generic remote-work articles, courses, housing, communities, and productivity tools during job discovery.
- Exclude catalog entries dedicated to crypto, Web3, testing, frontend-only, or geography-specific markets that cannot include China.

## Requested discovery sites

- Automated: Remotive, Remote OK, and We Work Remotely use their documented public API or RSS feed.
- Configurable public API: The Muse Jobs API requires registering an app for production use. Set `THEMUSE_API_KEY` in the runtime environment before enabling its bounded newest-first `Flexible / Remote` pagination. Never scrape The Muse pages; its API terms expressly prohibit web scraping.
- Configurable ATS: Greenhouse and Workable use official public published-job endpoints, but each entry needs a company board token or account subdomain. Do not attempt to enumerate customer identifiers.
- Manual only: LinkedIn, Glassdoor, FlexJobs, Wellfound, and Y Combinator restrict or do not authorize general automated extraction. Keep these entries disabled and never browser-automate them from this skill.
- Manual until a documented jobs feed is available: Remote.com and Jobgether. Their public job pages can be opened by the user, but this skill must not depend on undocumented internal endpoints or page scraping.
- Social lead discovery: Xiaohongshu and similar community posts are manual lead sources only. The public Open Platform does not currently expose a general note-search/read API for this workflow. Record the post as provenance, but use the official employer career page or ATS as the job source of record.
- Curated directory discovery: Awesome Remote Job is a manual catalog. Initial backend-relevant leads are tracked in `config/discovery_catalogs.json`; none may be enabled in `config/sources.json` until its access method is independently verified.

## Remote OK coverage (verified 2026-09-24)

Fetch the overall public API plus category JSON feeds linked by public category pages. Merge by Remote OK job ID. Category feeds expose bounded recent results, not the complete historical inventory. A probe of `api?tag=java&page=2` returned the same job IDs as page 1; do not implement fictitious pagination. Do not call robots-disallowed `action=get_jobs` endpoints. Respect a two-second interval and preserve canonical Remote OK attribution. Missing location is `Not stated`, never inferred Worldwide. Persist per-feed counts and partial failures and show per-source filtering statistics. Public access guidance: https://remoteok.com/llms.txt and https://remoteok.com/robots.txt .
