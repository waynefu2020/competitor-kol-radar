# 海外平台：TikHub 接口与字段

所有请求：`GET https://api.tikhub.io<path>`，Header `Authorization: Bearer <key>`，需带 User-Agent。实测单价约 $0.001/次。

## TikTok

- 搜索：`/api/v1/tiktok/app/v3/fetch_video_search_result`，参数 `keyword, offset(0,20,40…), count=20, sort_type(0 相关 / 1 点赞)`。不要传 `publish_time`。
- 结果：`data.search_item_list[].aweme_info`
  - `aweme_id, desc, create_time, region`
  - `statistics.{play_count, digg_count, comment_count, share_count, collect_count}`
  - `author.{unique_id, follower_count}` —— 自带粉丝数，不用再查主页
  - `text_extra[].hashtag_name`
  - `commerce_info.branded_content_type`（含义见 pitfalls）、`is_ads`、`anchors[].type`（35 ≈ TikTok Shop 商品）

## Instagram

- 话题帖子：`/api/v1/instagram/v2/fetch_hashtag_posts`，参数 `keyword, feed_type(top|recent), pagination_token`
- 结果：`data.data.items[]`：`code, taken_at, caption.text, like_count, play_count/ig_play_count, comment_count, user.username, is_paid_partnership, sponsor_tags, product_type`；翻页 token 在 `data.pagination_token`
- 博主主页：`/api/v1/instagram/v1/fetch_user_info_by_username?username=`，粉丝数 `data.data.user.edge_followed_by.count`

## YouTube

- 搜索：`/api/v1/youtube/web/search_video`，参数 `search_query, order_by(this_year|this_month…), continuation_token`；结果 `data.videos[]`：`video_id, title, author, number_of_views, published_time("3 weeks ago"), channel_id`
- 详情：`/api/v1/youtube/web_v2/get_video_info?video_id=`：`title, description, channel_handle, subscriber_count_text, view_count, like_count, publish_date, length_seconds`

## 账户

- 余额：`/api/v1/tikhub/user/get_user_info` → `user_data.balance`

## 备用数据源

- **Monid**（若已安装）：`anyapi /tiktok.search_keyword`、`/instagram.search_hashtag`、`/similarweb.overview` 等。Similarweb 只有这里有。
- **TikHub MCP**：已在 Claude Code 配置时，可直接调用 MCP 工具代替脚本做零散查询；批量采集仍用脚本更快、可复现。
