# 国内平台（实验口径）

脚本暂未自动化国内平台。按本文档手动采集，产出字段尽量对齐海外（platform, id, handle, followers, views, likes, ts, text, url），存成 `raw/posts_domestic.jsonl` 后可追加进 `posts.jsonl` 复用 analyze.py。

## 小红书

- 搜索：`/api/v1/xiaohongshu/app_v2/search_notes`，参数 `keyword, page, sort_type(general|time_descending|popularity_descending|comment_descending|collect_descending), note_type(不限|视频笔记|普通笔记), time_filter(不限|一天内|一周内|半年内)`
- 结果：`data.items[].note`：`id, title, desc(截断), type(video|normal), timestamp, liked_count, collected_count, comments_count, shared_count, user.nickname, xsec_token`
- 详情（完整正文、封面）：`/api/v1/xiaohongshu/web_v3/fetch_note_detail?note_id=&xsec_token=`
- 没有公开播放量。核心指标是**赞、藏、评**，工具和干货类内容看**收藏率**（藏 ÷ 赞）。
- "最热"排序会返回半年前的旧帖：最热 + 最新都抓，再按时间过滤。

## 国内投放信号（和海外不同）

| 类型 | 信号 |
|---|---|
| 付费合作 | 小红书笔记的"品牌合作"标识（蒲公英报备）；抖音星图标记；文案"赞助""合作""广告" |
| 寄样 | "品牌寄送""收到了""体验装"；没报备的软广很多，单靠文案识别率低 |
| 带货 | 小红书商品卡/店铺；抖音小黄车；"评论区置顶链接" |
| 自然 | 以上都没有，但国内软广不报备更普遍，"自然"占比应视为上限 |

## 国内渠道

天猫、京东、抖音电商、小红书店铺、拼多多、线下（屈臣氏、KKV、集合店）。规模数据看品牌财报、电商平台榜单、行业媒体（青眼、36氪、界面、晚点）。

## 内外对比模式

同一品牌两套口径分开统计，对比时只比**比例和结构**（自然占比、量级结构、选题卖点），不比绝对数，因为平台指标不同（小红书没有播放量）。
