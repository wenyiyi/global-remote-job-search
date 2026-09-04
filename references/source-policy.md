# Source policy

Before enabling a source, record its name, canonical link, filters, access method, and conservative request interval in `config/sources.json`.

Prefer official ATS/public APIs (Greenhouse, Lever, Ashby), official company APIs/RSS, documented remote-board APIs/feeds, then public pages whose terms and robots policy permit modest automation. Mark a source `manual` and disabled when it needs login, has strong anti-bot controls, forbids automation, has unclear authorization, or is unreliable. Never bypass restrictions.

Use a descriptive User-Agent, sequential requests, the configured delay, and at most three retries for 429/5xx/network failures. Respect Retry-After. Do not retry ordinary 4xx responses. Re-check terms periodically.

## Requested discovery sites

- Automated: Remotive, Remote OK, and We Work Remotely use their documented public API or RSS feed.
- Configurable ATS: Greenhouse and Workable use official public published-job endpoints, but each entry needs a company board token or account subdomain. Do not attempt to enumerate customer identifiers.
- Manual only: LinkedIn, Glassdoor, FlexJobs, Wellfound, and Y Combinator restrict or do not authorize general automated extraction. Keep these entries disabled and never browser-automate them from this skill.
- Manual until a documented jobs feed is available: Remote.com and Jobgether. Their public job pages can be opened by the user, but this skill must not depend on undocumented internal endpoints or page scraping.
