# 安装说明（写给 AI Agent）

用户把这个仓库地址发给你，让你安装时，按下面做。用户多半不懂技术：每一步用一句大白话告诉他在做什么，不要让他自己敲命令。

## 1. 放到你的 skills 目录

| Agent | 目录 |
|---|---|
| Claude Code | `~/.claude/skills/competitor-kol-radar` |
| Codex | `~/.codex/skills/competitor-kol-radar` |
| 其他支持 Skill 的 Agent | 放到它的 skills 目录；不确定就查它的文档或问用户 |

```bash
DEST=~/.claude/skills/competitor-kol-radar   # 按上表换成你的目录
if [ -d "$DEST/.git" ]; then git -C "$DEST" pull --ff-only; else git clone https://github.com/waynefu2020/competitor-kol-radar.git "$DEST"; fi
```

没有 git 时用压缩包：

```bash
mkdir -p "$DEST" && curl -L https://github.com/waynefu2020/competitor-kol-radar/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1 -C "$DEST"
```

如果你不能写本地文件（比如 Claude 网页版或桌面 App 的普通对话）：让用户从 GitHub 下载 ZIP（Code → Download ZIP），在 设置 → 功能 → Skills 里上传。

## 2. 自检

```bash
python3 "$DEST/scripts/doctor.py"
```

按输出处理：Python 版本太低就告诉用户怎么装；其他项照提示走。

## 3. TikHub Key（可选，但推荐）

先用一两句话告诉用户：

- 数据来自 TikHub，注册地址 https://tikhub.io ，一次海外竞品调研大约花 $0.5–1。
- 没有 Key 也能用免费兜底方案，只是 TikTok 和 Instagram 的数据会少很多。

用户把 Key 发给你后，这样保存（Key 不会出现在命令输出里）：

```bash
printf '%s' '<用户给的 Key>' | python3 "$DEST/scripts/doctor.py" --save-key
python3 "$DEST/scripts/doctor.py"
```

规矩：

- 不要在回复里复述 Key，也不要把 Key 写进 skills 目录、项目文件或记忆。
- 自检显示 Key 无效时，让用户去 TikHub 后台确认，不要反复重试。

## 4. 可选：免费兜底工具

只有用户没有 TikHub、或想做小红书时才需要。安装前先问用户：

- `yt-dlp`（YouTube / TikTok）：`pipx install yt-dlp` 或 `brew install yt-dlp`
- `xhs-cli`（小红书）：`pipx install xiaohongshu-cli`，然后让用户自己运行 `xhs login`（会读取他浏览器里的小红书登录状态，要他本人同意）

## 5. 告诉用户怎么用

装好后对用户说一句：

> 装好了。以后直接说"帮我拆一下 <品牌名> 最近 3 个月的海外红人营销"就行，也可以加上"做成适合发小红书的风格"或"做成给老板汇报的风格"。
