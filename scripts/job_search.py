#!/usr/bin/env python3
"""Public remote-job search, conservative China screening, reports and Feishu cards."""
from __future__ import annotations

import argparse, datetime as dt, email.utils, hashlib, html, json, logging, os, re, tempfile, time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parents[1]
UA = "global-remote-job-search/1.0 (public-job-feed; low-frequency)"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def setup_private_config(root=ROOT, input_fn=input):
    target=root/"config/private.json"
    if target.exists():
        raise SystemExit("config/private.json 已存在；为避免覆盖隐私配置，请先自行备份或删除后重试")
    def ask(label, default=""):
        suffix=f" [{default}]" if default else ""
        value=input_fn(f"{label}{suffix}: ").strip()
        return value or default
    def ask_int(label, default, minimum=0, maximum=None):
        while True:
            raw=ask(label,str(default))
            try:
                value=int(raw)
                if value < minimum or (maximum is not None and value > maximum): raise ValueError
                return value
            except ValueError: print(f"请输入 {minimum}" + (f"–{maximum}" if maximum is not None else " 以上") + "的整数")
    def ask_float(label, default, minimum, maximum):
        while True:
            try:
                value=float(ask(label,str(default)))
                if not minimum <= value <= maximum: raise ValueError
                return value
            except ValueError: print(f"请输入 {minimum}–{maximum} 的数字")
    def csv(label, default):
        return [x.strip() for x in ask(label,", ".join(default)).split(",") if x.strip()]
    print("交互式私有配置（不会询问或保存 Webhook；可直接回车采用默认值）")
    resume_paths=[]
    while True:
        value=ask("简历绝对路径（留空结束）")
        if not value: break
        resume_paths.append(str(Path(value).expanduser().resolve()))
    cfg={
        "candidate":{
            "name":ask("称呼（可使用昵称）","Private candidate"),
            "base":ask("工作所在地/时区","China (UTC+8)"),
            "years_backend":ask_int("后端经验年数",5),
            "resume_paths":resume_paths,
            "skills":csv("技能，英文逗号分隔",["Go","Python","Java","microservices","distributed systems","Redis","Kafka","MySQL"]),
        },
        "preferences":{
            "target_titles":csv("目标岗位，英文逗号分隔",["Backend Engineer","Platform Engineer","Distributed Systems Engineer"]),
            "preferred_remote":csv("优先远程范围，英文逗号分隔",["worldwide","global","APAC","Asia","China"]),
            "preferred_engagement":csv("合作形式，英文逗号分隔",["full-time","long-term contractor","EOR"]),
            "minimum_score":ask_float("最低匹配度",4.0,1.0,5.0),
            "max_results":ask_int("每次最多岗位数",50,1,50),
            "max_age_days":ask_int("只保留最近多少天",7,1,365),
        },
        "company_enrichment":{"enabled":True,"request_delay_seconds":0.25},
    }
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    target.chmod(0o600)
    print(f"配置已保存：{target}（权限 600，已被 .gitignore 排除）")
    return target


def strip_html(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def fetch_json(url, method="GET", body=None, attempts=3):
    data = None if body is None else json.dumps(body).encode()
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if data: headers["Content-Type"] = "application/json"
    for attempt in range(attempts):
        try:
            with request.urlopen(request.Request(url, data=data, headers=headers, method=method), timeout=25) as r:
                return json.load(r)
        except error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1: raise
            delay = int(exc.headers.get("Retry-After", 2 ** attempt))
        except (error.URLError, TimeoutError):
            if attempt == attempts - 1: raise
            delay = 2 ** attempt
        time.sleep(min(delay, 30))


def fetch_bytes(url, attempts=3):
    for attempt in range(attempts):
        try:
            with request.urlopen(request.Request(url, headers={"User-Agent": UA}), timeout=25) as r:
                return r.read()
        except error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1: raise
            delay = int(exc.headers.get("Retry-After", 2 ** attempt))
        except (error.URLError, TimeoutError):
            if attempt == attempts - 1: raise
            delay = 2 ** attempt
        time.sleep(min(delay, 30))


def format_compensation(minimum=None, maximum=None, currency="", period=""):
    values=[v for v in (minimum,maximum) if v not in (None,"",0,"0")]
    if not values: return ""
    def amount(v):
        try: return f"{float(v):,.0f}"
        except (TypeError,ValueError): return str(v)
    span=amount(values[0]) if len(values)==1 else f"{amount(values[0])}–{amount(values[1])}"
    suffix=f"/{period}" if period else ""
    return " ".join(x for x in (currency,span+suffix) if x).strip()


def normalized_job(source, sid, company, title, url, published, location, description, compensation="", company_country="", company_size=""):
    if isinstance(published, (int, float)):
        published = dt.datetime.fromtimestamp(published, dt.timezone.utc).date().isoformat()
    return {"source": source, "source_id": str(sid or url), "company": company or "Unknown",
            "title": title or "Untitled", "url": url or "", "published_at": str(published or "Unknown")[:10],
            "remote_scope_raw": strip_html(location) or "Not stated", "description": strip_html(description),
            "compensation_raw": strip_html(str(compensation)) if compensation else "",
            "company_country_raw": strip_html(str(company_country)) if company_country else "",
            "company_size_raw": strip_html(str(company_size)) if company_size else ""}


def fetch_source(src):
    kind, name = src["kind"], src["name"]
    if kind == "remotive":
        url = src["url"] + "?" + parse.urlencode({"category": "software-dev", "search": "backend"})
        rows = fetch_json(url).get("jobs", [])
        return [normalized_job(name, x.get("id"), x.get("company_name"), x.get("title"), x.get("url"),
                x.get("publication_date"), x.get("candidate_required_location"), x.get("description"), x.get("salary")) for x in rows]
    if kind == "arbeitnow":
        rows = [x for x in fetch_json(src["url"]).get("data", []) if x.get("remote")]
        return [normalized_job(name, x.get("slug"), x.get("company_name"), x.get("title"), x.get("url"),
                x.get("created_at"), "Remote" if x.get("remote") else x.get("location"), x.get("description")) for x in rows]
    if kind == "greenhouse":
        rows = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{src['board_token']}/jobs?content=true").get("jobs", [])
        return [normalized_job(name, x.get("id"), name.replace(" example", ""), x.get("title"), x.get("absolute_url"),
                x.get("updated_at"), (x.get("location") or {}).get("name"), x.get("content")) for x in rows]
    if kind == "lever":
        rows = fetch_json(f"https://api.lever.co/v0/postings/{src['site']}?mode=json")
        return [normalized_job(name, x.get("id"), name.replace(" example", ""), x.get("text"), x.get("hostedUrl"),
                "Unknown", (x.get("categories") or {}).get("location"), x.get("descriptionPlain") or x.get("description")) for x in rows]
    if kind == "ashby":
        rows = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{src['board']}").get("jobs", [])
        return [normalized_job(name, x.get("jobUrl"), name.replace(" example", ""), x.get("title"), x.get("jobUrl"),
                x.get("publishedAt"), x.get("location"), x.get("descriptionPlain") or x.get("descriptionHtml")) for x in rows]
    if kind == "himalayas":
        rows=[]
        for query in src.get("queries", ["backend engineer", "golang", "platform engineer", "distributed systems"]):
            for page in range(1, int(src.get("pages", 1))+1):
                url=src["url"]+"?"+parse.urlencode({"q":query,"sort":"recent","page":page})
                try: rows.extend(fetch_json(url).get("jobs", []))
                except Exception as exc: logging.warning("Himalayas query=%r page=%d skipped: %s",query,page,type(exc).__name__)
                time.sleep(float(src.get("query_delay_seconds", 1)))
        jobs=[]
        for x in rows:
            restrictions=x.get("locationRestrictions") or []
            scope="Worldwide" if not restrictions else "Restricted to: " + ", ".join(str(v) for v in restrictions)
            tz=x.get("timezoneRestrictions") or []
            if tz: scope += "; timezone: " + ", ".join(f"UTC{v:+g}" for v in tz)
            jobs.append(normalized_job(name, x.get("guid"), x.get("companyName"), x.get("title"),
                        x.get("applicationLink"), x.get("pubDate"), scope, x.get("description") or x.get("excerpt"),
                        format_compensation(x.get("minSalary"),x.get("maxSalary"),x.get("currency"),x.get("salaryPeriod")),
                        x.get("companyCountry") or x.get("companyLocation"), x.get("companySize")))
        return jobs
    if kind == "remoteok":
        rows=fetch_json(src["url"])
        if rows and "legal" in rows[0]: rows=rows[1:]
        jobs=[]
        for x in rows:
            location=(x.get("location") or "Worldwide").strip()
            low=location.lower()
            if location and not any(w in low for w in ("worldwide","anywhere","global","apac","asia","china","remote")):
                location="Restricted to: "+location
            jobs.append(normalized_job(name,x.get("id"),x.get("company"),x.get("position"),x.get("url") or x.get("apply_url"),
                        x.get("date") or x.get("epoch"),location,x.get("description")+" "+" ".join(x.get("tags") or []),
                        format_compensation(x.get("salary_min"),x.get("salary_max"),"USD","year")))
        return jobs
    if kind == "jobicy":
        url=src["url"]+"?"+parse.urlencode({"count":src.get("count",200),"industry":"engineering"})
        rows=fetch_json(url).get("jobs", [])
        jobs=[]
        for x in rows:
            scope=(x.get("jobGeo") or "Not stated").strip()
            if scope.lower() not in ("any","anywhere","worldwide","global","apac","asia","not stated"):
                scope="Restricted to: "+scope
            jobs.append(normalized_job(name,x.get("id"),x.get("companyName"),x.get("jobTitle"),x.get("url"),
                        x.get("pubDate"),scope,x.get("jobDescription") or x.get("jobExcerpt"),
                        format_compensation(x.get("salaryMin"),x.get("salaryMax"),x.get("salaryCurrency"),x.get("salaryPeriod")),
                        x.get("companyCountry") or x.get("companyLocation"), x.get("companySize")))
        return jobs
    if kind == "wwr_rss":
        rows=[]
        for feed in src.get("feeds", [src["url"]]):
            rows.extend(ET.fromstring(fetch_bytes(feed)).findall(".//item")); time.sleep(float(src.get("query_delay_seconds",1)))
        jobs=[]
        for x in rows:
            val=lambda tag: (x.findtext(tag) or "").strip()
            title=val("title"); company, sep, role=title.partition(":")
            published=val("pubDate")
            try: published=email.utils.parsedate_to_datetime(published).date().isoformat()
            except (TypeError, ValueError): pass
            jobs.append(normalized_job(name,val("guid") or val("link"),company if sep else "Unknown",role if sep else title,
                        val("link"),published,val("region") or val("country"),val("description")+" "+val("skills"),val("salary")))
        return jobs
    return []


TITLE_WORDS = ("backend", "back-end", "back end", "server-side", "server side", "golang", "go engineer", "java engineer", "python engineer", "platform engineer", "distributed systems", "api engineer")
BACKEND_SIGNALS = ("backend", "back-end", "microservice", "distributed system", "api", "server-side", "golang", " go ", "kafka", "redis")
HARD_EXCLUDE = ("us only", "united states only", "must reside in the us", "u.s. only", "eu only", "europe only",
                "uk only", "united kingdom only", "canada only", "north america only", "latin america only", "latam only",
                "must be based in the united states")
DIRECT = ("worldwide", "anywhere", "global remote", "including china", "china", "contractor", "eor")
CONFIRM = ("apac", "asia", "global", "remote")

TITLE_ZH = (("senior", "高级"), ("staff", "资深/Staff"), ("principal", "首席"),
            ("backend", "后端"), ("back-end", "后端"), ("platform", "平台"),
            ("distributed systems", "分布式系统"), ("software", "软件"),
            ("engineer", "工程师"), ("developer", "开发工程师"), ("lead", "负责人"))
TECH_NAMES = ("Go", "Golang", "Python", "Java", "Kotlin", "Rust", "C++", "AWS", "GCP", "Azure",
              "Kubernetes", "Docker", "Kafka", "Redis", "MongoDB", "MySQL", "PostgreSQL", "Terraform")


def chinese_job_summary(job):
    """Create a conservative Chinese rendering from explicit JD signals; keep original excerpt for audit."""
    title = job["title"]
    title_zh = title
    for en, zh in TITLE_ZH:
        title_zh = re.sub(re.escape(en), zh, title_zh, flags=re.I)
    text = job.get("description", "")
    low = text.lower()
    duties=[]
    for keys, label in (
        (("design", "architect"), "设计并演进后端服务/系统架构"),
        (("build", "develop", "implement"), "开发、交付并维护生产级服务"),
        (("scale", "high availability", "performance"), "提升系统扩展性、可用性与性能"),
        (("mentor", "technical leadership", "lead a team"), "承担技术带教或技术领导职责"),
        (("cross-functional", "collaborate", "stakeholder"), "与跨职能和国际团队协作"),
        (("on-call", "incident"), "参与值班、故障响应和稳定性建设")):
        if any(k in low for k in keys): duties.append(label)
    tech=[name for name in TECH_NAMES if re.search(r"(?<!\w)"+re.escape(name)+r"(?!\w)", text, re.I)]
    exp=[]
    years=re.findall(r"(?:at least\s+)?(\d{1,2})\+?\s*(?:years?|yrs?)", low)
    if years: exp.append(f"JD 提到 {max(map(int, years))} 年相关经验")
    if "bachelor" in low or "degree" in low: exp.append("可能要求本科或同等实践经验")
    if "english" in low: exp.append("明确涉及英文沟通")
    return {
        "title_zh": title_zh if title_zh != title else f"{title}（职位名称暂保留英文）",
        "content_zh": "；".join(duties[:4]) or "负责后端工程相关工作；具体职责请核对英文原文",
        "requirements_zh": "；".join(exp[:3]) or "年限、学历与语言要求需在完整 JD 中确认",
        "tech_stack_zh": "、".join(dict.fromkeys(tech)) or "未从岗位正文明确识别",
        "original_excerpt": text[:600] + ("…" if len(text) > 600 else "")
    }


def enrich_company(job, profiles):
    profile=profiles.get(job["company"].strip().lower(), {})
    country=job.get("company_country_raw") or profile.get("country") or "待核实"
    size=job.get("company_size_raw") or profile.get("size") or "待核实"
    source="招聘源" if job.get("company_country_raw") or job.get("company_size_raw") else ("本地公司资料缓存" if profile else "暂无可靠公开字段")
    return {**job, "company_country": country, "company_size": size, "company_profile_source": source,
            "company_profile_url": profile.get("source_url", ""), **chinese_job_summary(job)}


def company_key(name):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(inc|ltd|llc|corp|corporation|company|co)\b", "", name.lower()))


def employee_band(value):
    try: n=int(float(value))
    except (TypeError, ValueError): return ""
    for ceiling, label in ((10,"1–10"),(50,"11–50"),(200,"51–200"),(500,"201–500"),(1000,"501–1,000"),(5000,"1,001–5,000"),(10000,"5,001–10,000")):
        if n <= ceiling: return label+" employees"
    return "10,000+ employees"


def wikidata_company_profiles(companies, delay=.25):
    """Conservative exact-label lookup; uncertain search matches are discarded."""
    found={}
    for company in companies:
        url="https://www.wikidata.org/w/api.php?"+parse.urlencode({"action":"wbsearchentities","search":company,
            "language":"en","format":"json","limit":3,"type":"item","origin":"*"})
        try: candidates=fetch_json(url, attempts=2).get("search", [])
        except Exception as exc:
            logging.warning("company enrichment skipped for %s: %s", company, type(exc).__name__); continue
        match=next((x for x in candidates if company_key(x.get("label", "")) == company_key(company)
                    and any(w in (x.get("description") or "").lower() for w in ("company","business","corporation","enterprise","organization"))), None)
        if not match: continue
        qid=match["id"]
        try:
            entity=fetch_json("https://www.wikidata.org/wiki/Special:EntityData/"+qid+".json", attempts=2)["entities"][qid]
            claims=entity.get("claims", {})
            country_claim=(claims.get("P17") or [{}])[0].get("mainsnak",{}).get("datavalue",{}).get("value",{})
            country_qid=country_claim.get("id") if isinstance(country_claim,dict) else ""
            country=""
            if country_qid:
                country_entity=fetch_json("https://www.wikidata.org/wiki/Special:EntityData/"+country_qid+".json", attempts=2)["entities"][country_qid]
                labels=country_entity.get("labels",{}); country=(labels.get("zh") or labels.get("en") or {}).get("value","")
            employees=(claims.get("P1128") or [{}])[0].get("mainsnak",{}).get("datavalue",{}).get("value",{})
            amount=employees.get("amount") if isinstance(employees,dict) else ""
            found[company.lower()]={"country":country or "待核实", "size":employee_band(amount) or "待核实",
                                    "source_url":"https://www.wikidata.org/wiki/"+qid}
        except Exception as exc: logging.warning("company entity skipped for %s: %s", company, type(exc).__name__)
        time.sleep(delay)
    return found


def assess(job, cfg):
    title = job["title"].lower(); scope = job["remote_scope_raw"].lower(); text = (title + " " + job["description"]).lower()
    title_match=any(w in title for w in TITLE_WORDS)
    generic_engineer=any(w in title for w in ("software engineer","software developer","systems engineer","infrastructure engineer","full stack engineer","full-stack engineer","full stack developer","full-stack developer"))
    if not title_match and not (generic_engineer and sum(w in text[:4000] for w in BACKEND_SIGNALS)>=2): return None
    if any(w in title for w in ("qa ", "quality assurance", "testing", "frontend", "front-end", "react", "mobile", "ios", "android")): return None
    if scope.startswith("restricted to:") and "china" not in scope:
        feasibility, score = "不建议投", 1.0
    elif "," in scope and "china" not in scope and not any(w in scope for w in ("worldwide","anywhere","global","apac","asia","remote")):
        feasibility, score = "不建议投", 1.0
    elif scope.strip(" .,-").lower() in ("us", "usa", "united states", "uk", "united kingdom", "eu", "europe", "canada"):
        feasibility, score = "不建议投", 1.0
    elif any(w in scope or w in text[:1500] for w in HARD_EXCLUDE):
        feasibility, score = "不建议投", 1.0
    elif any(w in scope for w in DIRECT) or scope in ("any", "anywhere in the world", "anywhere"):
        feasibility, score = "可直接投", 3.0
    elif any(w in scope for w in CONFIRM):
        feasibility, score = "值得确认", 2.5
    else:
        feasibility, score = "值得确认", 2.0
    title_bonus = 1.5 if title_match else (1.0 if generic_engineer else .5)
    skills = cfg["candidate"]["skills"]
    matched = [s for s in skills if s.lower() in text]
    skill_bonus = min(1.0, len(matched) / 4)
    score = min(5.0, round(score + title_bonus + skill_bonus, 1)) if feasibility != "不建议投" else score
    gaps = []
    for keyword in ("kubernetes", "aws", "rust", "typescript", "leadership"):
        if keyword in text and not any(keyword in s.lower() for s in skills): gaps.append(keyword)
    reason = f"职位方向匹配；命中技能：{', '.join(matched[:6]) or '未从摘要确认'}；远程范围判定为{feasibility}。"
    threshold=float(cfg["preferences"].get("minimum_score", 3.5))
    return {**job, "china_feasibility": feasibility, "score": score, "match_reason": reason,
            "main_gaps": ", ".join(gaps[:4]) or "需在完整 JD/面试中确认雇佣实体、时区与英文沟通要求",
            "recommendation": "建议投递" if score >= threshold and feasibility == "可直接投" else ("建议先确认中国雇佣/EOR/contractor" if score >= threshold else "暂不投递")}


def uid(job):
    raw = f"{job['source']}|{job['source_id']}|{job['url']}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def published_date(job):
    try: return dt.date.fromisoformat(job.get("published_at", "")[:10])
    except (TypeError, ValueError): return None


def build_report(jobs, errors, now):
    lines = [f"# 全球远程后端岗位日报 - {now:%Y-%m-%d}", "", f"新增高匹配岗位：{len(jobs)} 个", ""]
    if not jobs: lines += ["没有符合条件的新岗位。", ""]
    for i, j in enumerate(jobs, 1):
        source = f"[{j['source']}]({j['source_url']})" if j.get("source_url") else j["source"]
        lines += [f"## {i}. {j['company']} - {j['title']}", "", f"- 申请链接：[{j['url']}]({j['url']})",
                  f"- 发布日期：{j['published_at']}", f"- 来源：{source}", f"- Remote 原文：{j['remote_scope_raw']}",
                  *([f"- 薪资范围：{j['compensation_raw']}"] if j.get("compensation_raw") else []),
                  f"- 公司所属国家/地区：{j['company_country']}", f"- 公司规模：{j['company_size']}",
                  f"- 公司信息依据：" + (f"[{j['company_profile_source']}]({j['company_profile_url']})" if j.get("company_profile_url") else j['company_profile_source']),
                  f"- 中国 base 可行性：{j['china_feasibility']}", f"- 匹配度：{j['score']:.1f}/5",
                  f"- 中文职位名：{j['title_zh']}", f"- 岗位内容（中文）：{j['content_zh']}",
                  f"- 任职要求（中文）：{j['requirements_zh']}", f"- 技术栈：{j['tech_stack_zh']}",
                  f"- 英文原文摘要：{j['original_excerpt']}", f"- 匹配原因：{j['match_reason']}",
                  f"- 主要缺口：{j['main_gaps']}", f"- 建议：{j['recommendation']}", ""]
    if errors: lines += ["## 来源错误", ""] + [f"- {e}" for e in errors] + [""]
    return "\n".join(lines)


def build_payload(jobs, now):
    blocks = [{"tag":"div","text":{"tag":"lark_md","content":f"**新增高匹配岗位：{len(jobs)} 个**"}}]
    for j in jobs:
        source = f"[{j['source']}]({j['source_url']})" if j.get("source_url") else j["source"]
        salary = f"\n薪资：{j['compensation_raw']}" if j.get("compensation_raw") else ""
        content = (f"**{j['company']}｜{j['title']}**  {j['score']:.1f}/5\n"
                   f"{j['china_feasibility']}｜{j['published_at']}｜来源：{source}{salary}\n"
                   f"公司：{j['company_country']}｜规模：{j['company_size']}\n"
                   f"中文解读：{j['content_zh']}\n技术栈：{j['tech_stack_zh']}\n"
                   f"[{j['recommendation']} · 打开申请页]({j['url']})")
        blocks.append({"tag":"div","text":{"tag":"lark_md","content":content}})
    return {"msg_type":"interactive","card":{"header":{"template":"purple","title":{"tag":"plain_text","content":f"全球远程后端岗位日报 {now:%Y-%m-%d}"}},"elements":blocks}}


def post_feishu(payload):
    webhook = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook: raise RuntimeError("FEISHU_WEBHOOK_URL 未设置")
    result = fetch_json(webhook, method="POST", body=payload)
    if result.get("code", result.get("StatusCode", 0)) not in (0, None): raise RuntimeError("飞书返回失败状态")


def execute(args, root=ROOT, state_override=None):
    cfg = load_json(root / "config/private.json")
    missing = [p for p in cfg["candidate"]["resume_paths"] if not Path(p).is_file()]
    if missing: raise SystemExit(f"配置错误：{len(missing)} 个简历路径不存在")
    errors=[]
    if args.fixture:
        raw = load_json(Path(args.fixture))
    else:
        raw=[]; source_counts=[]
        for src in load_json(root / "config/sources.json")["sources"]:
            if not src.get("enabled") or src["kind"] == "manual": continue
            try:
                rows=fetch_source(src)
                source_url=src.get("docs") or src.get("url") or ""
                for job in rows: job["source_url"]=source_url
                raw.extend(rows); source_counts.append((src["name"],len(rows)))
            except Exception as exc: errors.append(f"{src['name']}: {type(exc).__name__}")
            time.sleep(float(src.get("rate_seconds", 0)))
        logging.info("source_counts=%s", ", ".join(f"{n}:{c}" for n,c in source_counts))
    state_path = Path(state_override) if state_override else root / "state/seen.json"
    seen = set(load_json(state_path).get("seen", [])) if state_path.exists() else set()
    unique_raw={uid(j):j for j in raw}.values()
    scored = [x for j in unique_raw if (x := assess(j, cfg)) is not None]
    threshold=float(cfg["preferences"].get("minimum_score", 4)); cap=min(50, int(cfg["preferences"].get("max_results", 50)))
    max_age=0 if args.fixture else max(0, int(cfg["preferences"].get("max_age_days", 7)))
    cutoff=dt.date.today()-dt.timedelta(days=max_age)
    eligible=[j for j in scored if j["score"] >= threshold and j["china_feasibility"] != "不建议投" and uid(j) not in seen]
    if max_age: eligible=[j for j in eligible if published_date(j) and published_date(j) >= cutoff]
    selected = sorted(eligible, key=lambda x:(published_date(x) or dt.date.min, x["score"]), reverse=True)[:cap]
    profiles_path=root/"config/company_profiles.json"
    profiles=load_json(profiles_path) if profiles_path.exists() else {}
    if not args.fixture and cfg.get("company_enrichment",{}).get("enabled", True):
        missing=sorted({j["company"] for j in selected if j["company"].lower() not in profiles})
        profiles.update(wikidata_company_profiles(missing, float(cfg.get("company_enrichment",{}).get("request_delay_seconds", .25))))
    selected=[enrich_company(j, profiles) for j in selected]
    now=dt.datetime.now(); report_dir=root/"reports"; log_dir=root/"logs"; report_dir.mkdir(exist_ok=True); log_dir.mkdir(exist_ok=True)
    stamp=now.strftime("%Y%m%d-%H%M%S-%f"); report=report_dir/f"remote-jobs-{stamp}.md"; preview=report_dir/f"remote-jobs-{stamp}-payload.json"
    report.write_text(build_report(selected, errors, now), encoding="utf-8")
    payload=build_payload(selected, now); preview.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("report=%s new=%d source_errors=%d", report, len(selected), len(errors))
    if args.dry_run: logging.info("dry-run: Feishu skipped; durable state unchanged")
    elif not selected: logging.info("没有新岗位；不发送飞书")
    else:
        post_feishu(payload)
        state_path.parent.mkdir(exist_ok=True); state_path.write_text(json.dumps({"seen":sorted(seen|{uid(j) for j in selected})}, indent=2), encoding="utf-8")
        logging.info("飞书推送成功；已更新去重状态")
    return selected, report, preview


def self_test():
    class A: dry_run=False; fixture=str(ROOT/"fixtures/jobs.json")
    original=os.environ.pop("FEISHU_WEBHOOK_URL", None)
    try:
        with tempfile.TemporaryDirectory() as td:
            setup_root=Path(td)/"setup"; answers=iter(["","","","","","","","","","",""])
            setup_path=setup_private_config(setup_root, lambda _prompt: next(answers))
            assert setup_path.stat().st_mode & 0o777 == 0o600 and load_json(setup_path)["preferences"]["max_age_days"]==7
            # Test production-state semantics without network by validating selection then writing the same IDs.
            A.dry_run=True; first, report, preview=execute(A, root=setup_root, state_override=Path(td)/"seen.json")
            assert len(first)==2 and all(j["score"]>=4 for j in first)
            payload=load_json(preview); assert payload["msg_type"]=="interactive"
            assert all("https://" in e["text"]["content"] for e in payload["card"]["elements"][1:])
            assert "薪资：USD 120,000–160,000/year" in json.dumps(payload,ensure_ascii=False)
            report_text=report.read_text(encoding="utf-8")
            assert "薪资范围：USD 120,000–160,000/year" in report_text
            assert "公司所属国家/地区：待核实" in report_text and "岗位内容（中文）" in report_text
            state=Path(td)/"seen.json"; state.write_text(json.dumps({"seen":[uid(j) for j in first]}), encoding="utf-8")
            second, _, _=execute(A, root=setup_root, state_override=state); assert len(second)==0
            print(f"SELF-TEST OK: config, scoring, dedup, report, payload; report={report}")
    finally:
        if original is not None: os.environ["FEISHU_WEBHOOK_URL"]=original


def main():
    p=argparse.ArgumentParser(); p.add_argument("--setup", action="store_true", help="通过终端问答创建私有配置")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--fixture"); p.add_argument("--self-test", action="store_true")
    args=p.parse_args(); logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.setup: setup_private_config()
    elif args.self_test: self_test()
    else: execute(args)


if __name__ == "__main__": main()
