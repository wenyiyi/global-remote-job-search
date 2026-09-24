# Social-post lead verification

Use this workflow only when the user asks to discover jobs from public social posts or supplies post links/screenshots.

1. Read only content that is publicly accessible without bypassing login, CAPTCHA, rate limits, or other access controls. Never collect private author information.
2. Capture the company name, mentioned role or team, visible post date, and post URL. Treat salary, remote scope, hiring status, and application instructions as unverified claims.
3. Resolve the exact employer identity. Ignore anonymous companies, recruiting-course advertisements, paid referrals, reposts without an identifiable employer, and leads that cannot be distinguished from similarly named companies.
4. Find the employer's official careers domain or its linked Greenhouse, Lever, Ashby, Workable, SmartRecruiters, BambooHR, or Workday page. Do not use a job aggregator as final evidence.
5. Confirm that a matching posting is currently live. Preserve its official title, URL, publication date, location wording, employment type, and description. Apply all existing role, freshness, Web3, company-table, and China-remote filters.
6. Use the official posting as `source` and application link. Add the social post only as `discovery_provenance`; never imply that the post proves eligibility or that its author represents the employer.
7. If no live official posting can be found, keep the item in a separate `待官网核实` lead list and do not send it as a recommended job.

Marketplace-specific rules:

- Upwork, Freelancer and Fiverr are lower-priority freelance marketplaces. Treat listings as leads unless the user explicitly requests marketplace contracts; never bid or contact a client automatically.
- Glints, PowerToFly, Fairygodboss, InHerSight, Working Nomads and Workew may expose public listings, but verify the employer and current vacancy on its official site before recommendation.
- SmartDeer, Freelab, Lapins.ai, NextJob, 电鸭社区, RW数字游民、Unix数字游民、云工网、圆领、某Boss、L聘 and Xiaohongshu creator accounts are manual discovery channels. Do not infer that a publisher is the employer.
- WAHJobQueen is a secondary work-from-home blog, not an employer or verified job source. Paybump and Après contain paid/member-oriented career or job-board access. Jobright is an account-based AI job platform with resume, autofill, referral, and automated-application features. Keep all four manual; never subscribe, sign in, upload candidate data, contact people, or auto-apply. A visible company or role is only a lead for official Careers/ATS verification.
- Cryptosquare Jobs is excluded because the candidate has requested removal of Web3/crypto opportunities. Test IO is excluded because it is testing-oriented rather than backend engineering.
