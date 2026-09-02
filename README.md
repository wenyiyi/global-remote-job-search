# global-remote-job-search

每天从公开招聘 API/ATS 搜索适合 base 在中国的资深 Go/后端岗位，生成 Markdown 报告，并可选推送飞书卡片。不会自动投递、发邮件、登录招聘平台或绕过限制。

## 配置

首次使用时运行交互式配置：

```bash
python3 scripts/job_search.py --setup
```

脚本会逐项询问工作地点/时区、后端经验、可选简历路径、技能、目标岗位、匹配阈值、结果数量和岗位时效，然后生成权限为 600 的 `config/private.json`。该文件已被 `.gitignore` 排除。简历仅在本地检查路径是否存在，不读取、上传或输出正文。Webhook 不会被询问或写入配置。

`preferences.max_age_days` 控制岗位新鲜度，默认 7 天；启用后发布日期缺失或早于门槛的岗位不会推送。结果按发布日期倒序、匹配度次序排列。需要更严格的日报可设为 3。

在 `config/sources.json` 启用来源。Greenhouse `board_token`、Lever `site`、Ashby `board` 是公开招聘页标识，不是密钥。新增前阅读 `references/source-policy.md`。

## 公司信息与中文岗位内容

报告和飞书卡片会显示公司所属国家/地区、员工规模、中文岗位职责与技术栈。招聘接口明确提供公司信息时直接使用；否则对最终入选公司做低频 Wikidata 精确名称核验并附依据链接。可复制 `config/company_profiles.example.json` 为私有的 `config/company_profiles.json`，按小写公司名补充或覆盖经官网核验的 `country`、`size` 和 `source_url`。该文件不会提交到 Git。没有可靠信息时显示“待核实”，不会根据远程工作地点猜测公司总部。可在私有配置的 `company_enrichment.enabled` 关闭公开资料查询。

中文内容是脚本根据英文 JD 中明确出现的职责、经验和技术关键词生成的结构化中文解读，同时保留英文原文摘要供核对；它不是具有法律效力的逐字翻译。岗位关键条款仍以申请页英文原文为准。

## 飞书 Webhook

只从环境变量读取，切勿写进文件：

```bash
export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/...'
```

脚本不打印它。先用 dry-run 检查 `reports/*-payload.json`。

## 手动运行

```bash
cd ~/.codex/skills/global-remote-job-search
python3 scripts/job_search.py --dry-run
python3 scripts/job_search.py --self-test
python3 scripts/job_search.py        # 真推送，需要 FEISHU_WEBHOOK_URL
```

dry-run 不推送、不更新持久化去重状态。正式运行仅在推送成功后写 `state/seen.json`；没有新岗位时只写日志，不发空消息。

## macOS 每天北京时间 10:00

launchd：复制 `references/com.codex.global-remote-job-search.plist.example` 到 `~/Library/LaunchAgents/` 并替换路径。Webhook 用受限权限包装脚本或 `launchctl setenv` 提供，不写入 plist。

cron（机器时区需为 Asia/Shanghai）：

```cron
0 10 * * * cd "$HOME/.codex/skills/global-remote-job-search" && /usr/bin/python3 scripts/job_search.py >> logs/cron.log 2>&1
```

不要在 crontab 明文写 Webhook。

## GitHub Actions / 云服务器

代码可以放入公开仓库，但不得提交 `config/private.json`、简历、报告、日志、去重状态或 `.env`。参考 `references/github-actions.yml.example`；`FEISHU_WEBHOOK_URL` 必须放在 GitHub Actions Secrets 中。私有配置应由运行环境交互生成，或通过 Secret 在运行时写入临时文件。简历文件不是运行必需，结构化技能配置即可评分。

## MVP 与后续

默认启用 Remotive、Arbeitnow、Himalayas、Jobicy、Remote OK 公共 API及 We Work Remotely 官方 RSS；Greenhouse、Lever、Ashby 有通用适配器，填公司标识后启用。两个腾讯表格、LinkedIn 和 Glassdoor Community 标为仅人工查看。

后续可增加 Remote OK/We Work Remotely RSS、更多公司 ATS、公司官方 RSS，以及合规的岗位详情二次核验。每个来源先核对条款、robots、API/RSS 和合理频率。
