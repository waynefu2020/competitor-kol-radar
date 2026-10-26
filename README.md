# 竞品红人投放雷达 · competitor-kol-radar

> AI Agent Skill —— 站在营销总监的角度，拆解竞品在 TikTok / Instagram / YouTube 上的红人营销打法

**兼容**：Claude Code · Codex · OpenCode 及其他支持 Skill 的 AI Agent

---

## 这是什么

给它一个品牌名，它会抓取这个品牌近 3 个月的海外红人与 UGC 内容，回答营销总监最关心的三个问题：

1. **它是怎么打的？** 买量型、自来水型、联盟铺量型还是混合型，依据是什么
2. **有没有用？** 付费、寄样、联盟、自然内容各占多少，哪类内容播放更高，博主是什么量级，大家在聊什么、夸什么，导向哪里成交
3. **我们该怎么办？** 每条发现都配"对我们意味着什么"，建议动作分"照搬 / 改造 / 避开 / 先小测"，带优先级、预算量级和验证指标

交付物是一个适合手机竖屏浏览的网页报告，外加一份可筛选的内容明细 CSV。

```
立项（决策问题）→ 写 brief → 成本预估 → 采集 → 清洗分类 → 人工抽查
→ 渠道与规模研究 → 统计分析 → 写结论 → 生成报告 → 更新对标库
```

## 为什么不只是"抓数据"

这个 Skill 的价值在于口径和判断，这些在实战里踩过坑才总结出来：

- **五类内容口径**：付费合作 / 寄样（PR）/ 联盟带货 / 品牌合作（未注明）/ 自然内容。文案信号优先，平台标记兜底
- **坑清单**：同名噪音、官方号和仿冒号、竞品赞助的对比视频、YouTube 简介里其他品牌的折扣码、美妆圈的"PR ≠ 付费"、IG 播放数据缺失、Similarweb 直接访问偏高……
- **打法画像判定**：用"品牌主导内容 vs 自然内容播放倍数""自然内容占比""联盟占商业内容比例"自动判定，结论可追溯
- **对标库**：每跑一个品牌自动沉淀核心指标，越用越能回答"它处在什么位置"

内置两个对标样本，正好是两个极端：

| 品牌 | 打法 | 自然内容占比 | 品牌主导 / 自然播放 |
|---|---|---|---|
| Plaud（AI 录音卡） | 买量型 | 61% | 153× |
| 花知晓 Flower Knows（彩妆） | 自来水型 | 73% | 0.8× |

---

## 快速上手

### 1. 安装

```bash
git clone https://github.com/waynefu2020/competitor-kol-radar.git ~/.claude/skills/competitor-kol-radar
```

其他 Agent 放到各自的 skills 目录即可。需要 Python 3.9+，无第三方依赖。

### 2. 配置 TikHub API Key

数据来自 [TikHub](https://tikhub.io)（一次海外调研通常 $0.5–1）。二选一：

```bash
export TIKHUB_API_KEY=你的密钥
```

```bash
mkdir -p ~/.config/tikhub && printf '%s' '你的密钥' > ~/.config/tikhub/key && chmod 600 ~/.config/tikhub/key
```

不要把 Key 写进 Skill 目录或项目文件。

### 3. 对 AI 说一句话

```
帮我拆一下 Flower Knows 最近 3 个月的海外红人营销
```

其他触发说法：

- "竞品 XX 在 TikTok / IG / YouTube 上投了哪些博主？"
- "我们想出海，帮我看看对标品牌是怎么做红人营销的"
- "XX 的海外声量是买来的还是用户自发的？"

---

## 目录结构

```
competitor-kol-radar/
├── SKILL.md                    流程与判断规则（Agent 读这个）
├── scripts/
│   ├── collect.py              采集（--dry-run 预估成本和余额）
│   ├── normalize.py            清洗、去噪、五类分类、抽查样本
│   ├── analyze.py              KPI、打法画像、对标、CSV
│   ├── build_report.py         生成网页报告
│   ├── lexicons.py             美妆 / 科技 / App 的选题与卖点词典
│   ├── tikhub.py · common.py
├── references/
│   ├── methodology.md          口径、KPI、打法画像判定
│   ├── pitfalls.md             坑清单
│   ├── report-spec.md          总监视角的写作规范与 narrative.json 格式
│   ├── channel-signals.md      渠道信号怎么读
│   ├── platforms-overseas.md   TikHub 接口与字段
│   ├── platforms-domestic.md   国内平台（实验）
│   └── benchmarks.json         对标库
├── assets/
│   ├── report_template.html    报告模板（rose / ink 两套配色）
│   └── brief.example.json
└── examples/flowerknows/       样例 brief 与结论
```

## 局限

- 数据是搜索抽样，不是全量；没披露的合作会被算进自然内容，付费规模视为下限
- TikTok 商业标记字段的含义是根据样本推断的
- 国内平台（小红书、抖音）目前只有手动采集说明，自动化在路上
- 公开报道的营收、估值口径常不一致，报告会并列标注

## License

MIT
