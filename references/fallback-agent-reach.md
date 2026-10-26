# 免费兜底：没有 TikHub 时用 Agent Reach 工具链

[Agent Reach](https://github.com/Panniantong/Agent-Reach) 是一组免费的命令行和 MCP 工具（yt-dlp、xhs-cli、Exa 搜索、Jina 网页阅读等）。没有 TikHub Key 时用它兜底，能出报告，但**数据完整度明显更低**，报告里必须写清楚。

## 能力对照（2026-10 实测）

| 平台 | 用什么 | 能拿到 | 拿不到 / 限制 | 结论可信度 |
|---|---|---|---|---|
| YouTube | `yt-dlp` 搜索 | 标题、频道、播放量、简介摘要 | 发布日期、订阅数、完整简介（需 `--cookies-from-browser`） | 中：无 Cookie 时不能严格按时间窗过滤 |
| TikTok | 网页搜索找链接 → `yt-dlp -j` 单条解析 | 播放、点赞、评论、发布时间、文案 | 粉丝数；yt-dlp 的话题页已失效，只能靠搜索引擎发现链接，覆盖面窄 | 低到中：只适合看"头部内容长什么样" |
| Instagram | 网页搜索 + `r.jina.ai` 读公开帖 | 少量帖子的文案 | 互动数据、粉丝数；yt-dlp 的话题页已失效 | 仅定性，不进统计 |
| 小红书 | `xhs search`（xhs-cli） | 标题、作者、赞藏评转、发布时间 | 完整正文（需逐条 `xhs read`）、粉丝数 | 中：适合国内调研 |
| 渠道 / 规模 | 网页搜索（Exa 或 Agent 自带搜索） | 新闻、零售入驻、营收报道 | Similarweb 流量来源 | 与 TikHub 方案相同 |

## 准备

```bash
pipx install yt-dlp            # 或 brew install yt-dlp
pipx install xiaohongshu-cli && xhs login     # 小红书需要，会从浏览器提取 Cookie
```

`agent-reach doctor` 可检查哪些渠道可用。不要替用户运行 `xhs login` 或读取浏览器 Cookie，先说明会用到他的登录态，由他确认。

## 流程

brief 照常写（`tiktok_keywords` 等字段可以留着，不会用到）。然后：

```bash
S=~/.claude/skills/competitor-kol-radar/scripts

# YouTube：按上传时间排序搜索
python3 -I $S/agent_reach_import.py --brief brief.json youtube "flower knows" "flower knows review" --pages 2
#   用户同意用浏览器登录态后，可补齐日期和订阅数：
#   ... youtube "flower knows" --cookies-from-browser chrome

# TikTok：先用网页搜索收集视频链接（site:tiktok.com "品牌名" review / unboxing / haul），
# 每行一个写进 tiktok_urls.txt，再解析
python3 -I $S/agent_reach_import.py --brief brief.json tiktok --urls tiktok_urls.txt

# 小红书（国内）
python3 -I $S/agent_reach_import.py --brief brief.json xhs "花知晓" "花知晓 测评" --pages 2

python3 -I $S/normalize.py --brief brief.json
python3 -I $S/analyze.py --brief brief.json
```

导入结果写进 `raw/posts_extra.jsonl`，`normalize.py` 会自动合并，并打印"数据来源"和"无日期条数"。

TikTok 找链接的搜索词建议：`site:tiktok.com "<品牌>"`、`site:tiktok.com "<品牌>" review`、`"<品牌>" tiktok unboxing`、`site:tiktok.com "<品牌>" #ad`。合作话题（如 #品牌partner）单独搜一次。

## 写报告时必须做的

- 方法部分写明哪些平台走了兜底、各有多少条、缺什么（build_report 会自动加一条，narrative 里再补具体影响）。
- **不要在兜底数据上给"买量型 / 自来水型"的强结论**，除非 TikTok 或 YouTube 有足够带播放量的样本（每平台 ≥ 30 条）。样本不够就写"倾向于…，待 TikHub 数据验证"。
- 量级分布里"未知"占比高时，不写"主力博主是 X 万粉"。
- Instagram 只做定性描述（"能看到的帖子多是开箱和快闪打卡"），不出比例。
