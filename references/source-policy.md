# Source policy

Before enabling a source, record its name, canonical link, filters, access method, and conservative request interval in `config/sources.json`.

Prefer official ATS/public APIs (Greenhouse, Lever, Ashby), official company APIs/RSS, documented remote-board APIs/feeds, then public pages whose terms and robots policy permit modest automation. Mark a source `manual` and disabled when it needs login, has strong anti-bot controls, forbids automation, has unclear authorization, or is unreliable. Never bypass restrictions.

Use a descriptive User-Agent, sequential requests, the configured delay, and at most three retries for 429/5xx/network failures. Respect Retry-After. Do not retry ordinary 4xx responses. Re-check terms periodically.
