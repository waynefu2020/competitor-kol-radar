---
name: competitor-kol-radar
description: 竞品红人营销打法拆解（营销总监视角）——抓取竞品近 N 个月在 TikTok / Instagram / YouTube（国内小红书为实验功能）上的红人与 UGC 内容，判断它是"买量型""自来水型"还是"联盟铺量型"，统计博主量级、内容量、播放中位数、主打选题与卖点、销售转化渠道，对标库定位，输出带"对我们意味着什么 + 建议动作"的网页报告和明细 CSV。只要用户想研究某个品牌/竞品怎么做红人营销、KOL 投放、海外社媒种草、出海内容打法、博主合作、UGC 声量、"它在 TikTok/IG/YouTube 上投了哪些博主"、"竞品的红人投放怎么样"、"帮我拆一下 XX 的海外营销"，就应使用本技能，即使用户没说"竞品调研"。不用于：日常抖音竞品账号监控（用 competitor-radar）、单条视频解析、给自己找博主建联。
---

# 竞品红人投放雷达

用一套固定口径，把"某品牌在社媒上被谁、以什么方式、讲了什么、导向哪里买"拆清楚，并以营销总监能直接拿去开会的方式交付。

价值不在抓数据，在**口径和判断**：分清付费、寄样、联盟和自来水，剔除噪音，知道哪些数字不能信。这些规则写在 `references/` 里，先读再动手。

## 0. 立项：先定决策问题

动手前用一两句话确认（用户已经说清的就不要再问）：

- **品牌和别名**（含中文名、各国写法、产品线名）
- **市场**：海外（默认）/ 国内（小红书，实验）/ 内外对比
- **时间窗**：默认近 90 天
- **这份调研要支撑什么决策**：对标学习、进入新市场、定预算、找可复制打法、做内容选题……决策问题决定报告的"建议动作"往哪写。用户没说就默认"我们能借鉴什么"。
- **我方是谁**（可选）：用户的品牌/品类。有了它，建议才能落到"对我们意味着什么"。

## 1. 写 brief

复制 `assets/brief.example.json` 到工作目录（默认当前项目下的 `competitor-research/<brand-slug>/brief.json`），填品牌正则、官方号正则、噪音正则、搜索词、话题、产品/系列词典、品类。品类决定选题和卖点词典（`beauty` / `tech` / `app` / `general`）。

关键词设计见 `references/methodology.md` 第 2 节。最常见的坑：品牌名是常见词或人名（如 "Plaud" 撞上新闻人物）→ 必须写 `noise_regex`。

## 2. 成本预估 → 采集

数据源默认 TikHub（Key 读环境变量 `TIKHUB_API_KEY` 或 `~/.config/tikhub/key`，不要把 Key 写进任何文件或回复）。

```bash
S=~/.claude/skills/competitor-kol-radar/scripts
python3 -I $S/collect.py --brief brief.json --stage search --dry-run   # 打印调用次数、预估花费和余额
python3 -I $S/collect.py --brief brief.json --stage search
python3 -I $S/normalize.py --brief brief.json
python3 -I $S/collect.py --brief brief.json --stage details           # YouTube 详情 + IG 博主粉丝数
python3 -I $S/normalize.py --brief brief.json
```

一次海外调研通常 400–700 次调用，约 $0.5–1。预估超过 $3 先问用户。

**没有 TikHub Key？** 改走免费兜底：用 Agent Reach 工具链（yt-dlp、xhs-cli、网页搜索）采集，`scripts/agent_reach_import.py` 把结果导入同一套流程。YouTube 和小红书够用，TikTok 只能靠搜索发现链接，Instagram 只能定性。做之前读 `references/fallback-agent-reach.md`，先告诉用户兜底方案会缺哪些数据，再开始。

## 3. 抽查（不可跳过）

`normalize.py` 会打印各平台分类计数并抽出 20 条样本。逐条看：是不是在说这个品牌？分类对不对？发现系统性误判就改 brief 里的正则后重跑 normalize，而不是在报告里手工修数。常见误判和对策见 `references/pitfalls.md`。

## 4. 渠道与规模研究

内容数据只能看到"导向哪里买"。补齐渠道全貌：

- 用网页搜索查：零售入驻（如 Ulta、Best Buy、Costco、药妆店）、电商平台、TikTok Shop、联盟计划（Impact 等）、营收/融资/估值报道。来源互相矛盾时**两个口径都写**，不要挑一个。
- 官网流量来源（Similarweb）：TikHub 没有。若 Monid 可用且余额够，跑 `anyapi /similarweb.overview`，结果存 `raw/sales/similarweb.json`；否则在报告里注明缺失。
- 渠道信号如何解读见 `references/channel-signals.md`。

## 5. 分析

```bash
python3 -I $S/analyze.py --brief brief.json
```

产出 `analysis.json`（各平台按类型的内容量、博主数、量级、播放中位数、选题、卖点、产品提及、渠道、打法画像、与对标库的对比）和 `<品牌>_内容清单.csv`。

## 6. 写结论（总监视角）

读 `references/report-spec.md`，写 `narrative.json`。核心要求：

- **先结论后证据**：封面一句话判词 = 打法画像 + 最关键的一个数字。
- **每条发现都要有"所以呢"**：对我们意味着什么。
- **建议动作分四类**：照搬 / 改造 / 避开 / 先小测，各带优先级、预算量级和验证指标。
- **事实和推断分开写**，推断要说依据；样本是抽样，规模类结论标"下限"。
- 标题卖结论，不卖工具名。

## 7. 出报告

```bash
python3 -I $S/build_report.py --brief brief.json
```

生成 `<brand-slug>-report.html`。发布前看一次（截图或预览），修明显的排版问题，然后按 Artifact 工具的规则发布，并把 CSV 一起告诉用户。

## 8. 更新对标库

把本次的核心指标追加进 `references/benchmarks.json`（`analyze.py --save-benchmark` 自动完成）。对标库越大，"它处在什么位置"的判断越有说服力。

## 国内市场（实验）

小红书可用 TikHub `/api/v1/xiaohongshu/app_v2/search_notes` 抓取，或用免费的 `agent_reach_import.py xhs`（xhs-cli）导入。口径和信号差异见 `references/platforms-domestic.md`，统计复用 `analyze.py`，报告里标注"国内为实验口径"。

## 参考文件

| 文件 | 什么时候读 |
|---|---|
| `references/methodology.md` | 每次都读：口径定义、KPI、打法画像判定 |
| `references/pitfalls.md` | 抽查和解读数字前读 |
| `references/platforms-overseas.md` | 采集出错、字段含义不明时读 |
| `references/channel-signals.md` | 写渠道章节前读 |
| `references/report-spec.md` | 写 narrative.json 前读 |
| `references/platforms-domestic.md` | 做国内或内外对比时读 |
| `references/fallback-agent-reach.md` | 没有 TikHub Key、或要用小红书 xhs-cli 时读 |
| `references/benchmarks.json` | 对标定位时由 analyze.py 自动读取 |
