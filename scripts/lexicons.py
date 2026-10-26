"""Theme (how it's filmed) and selling-point (what's praised) dictionaries per category.

Regexes are matched case-insensitively against caption + hashtags (YouTube: title + description).
Add a category by copying one block; keep keys short and in the reader's words.
"""

COMMON_THEMES = {
    '开箱 / 礼盒': r'unbox|haul|pr (package|box)|開封|언박싱|開箱|package',
    '测评 / 值不值': r'review|honest|worth it|is it worth|ranked|ranking|overrated|disappoint|before you buy|测评|レビュー|리뷰|recenz',
    '竞品对比': r'\bvs\.?\b|versus|compar|better than|which .* (buy|best)|比較|对比',
    '教程 / 玩法': r'how to|tutorial|step by step|setup|set up|tips|guide|使い方|教程',
    '礼物 / 节日大促': r'gift|christmas|holiday|black ?friday|prime day|diwali|birthday|sale|セール|礼物|선물',
    '线下 / 快闪打卡': r'pop-?up|popup|in store|ulta|best ?buy|快闪|팝업|seongsu|store locator',
    'ASMR': r'asmr',
}

THEMES = {
    'beauty': {
        **COMMON_THEMES,
        '试色 / 上脸效果': r'swatch|試色|试色|try ?on|first impression|wear test|上脸|발색',
        '妆容教程 / GRWM': r'tutorial|grwm|get ready|makeup look|full face|教程|メイク|메이크업',
        '包装颜值 / 审美向': r'prettiest|pretty|aesthetic|packaging|cute|beautiful|gorgeous|princess|coquette|girly|dreamy|whimsical|可爱|かわいい|예쁜',
        '收藏展示 / 全系列': r'collection|full set|every|all of|全系列|コレクション|컬렉션|vanity|shelf',
        '平替 / 对比': r'\bdupe|vs\.?\b|compar|versus|比較',
    },
    'tech': {
        **COMMON_THEMES,
        '会议 / 职场提效': r'meeting|会議|議事録|reuni|réunion|call|商談|client|work|仕事|productiv',
        '学生 / 学习': r'student|lecture|class|college|学生|授業|勉強|study|school',
        '医疗 / 护理': r'doctor|medical|nurse|clinic|看護|介護|病院|patient|hospital',
        '家庭 / 宝妈': r'mom|mama|ママ|育児|parent|kids|family|家族',
        '个人知识管理': r'second brain|第二の脳|journal|idea|memory|remember|notes',
        '创业 / 销售': r'entrepreneur|business|founder|sales|real estate|経営|startup',
    },
    'app': {
        **COMMON_THEMES,
        '功能演示': r'feature|demo|how it works|walkthrough|試して|功能',
        '前后对比': r'before (and|&) after|transformation|变化',
        '效率 / 生活方式': r'productiv|routine|habit|day in (my|the) life|vlog',
        '模板 / 挑战': r'template|trend|challenge|filter',
    },
    'general': dict(COMMON_THEMES),
}

COMMON_POINTS = {
    '价格 / 折扣': r'price|cheap|afford|\$\d|% ?off|discount|sale|deal|code',
    '颜值 / 设计': r'design|aesthetic|beautiful|pretty|sleek|packag|顔値|デザイン',
    '中国品牌': r'c-?beauty|chinese|china|中国|國貨|国货',
}

POINTS = {
    'beauty': {
        **COMMON_POINTS,
        '包装像艺术品': r'packag|prettiest|too pretty|detail|embossed|carv|sculpt|art|包装|パッケージ|패키지',
        '主题系列 / IP 世界观': r'collection|series|ballet|unicorn|bear|rococo|bunny|angel|mermaid|系列|コレクション|컬렉션',
        '少女 / 公主 / Coquette 审美': r'princess|coquette|girly|girl|dreamy|fairy|whimsical|doll|balletcore|kawaii|cute|少女|公主',
        '腮红': r'blush|チーク|블러셔|腮红',
        '唇釉 / 口红': r'lip|gloss|lipstick|唇|リップ|립',
        '眼影盘': r'palette|eyeshadow|眼影|アイシャドウ|섀도우',
        '高光 / 闪片': r'highlight|glitter|shimmer|sparkl|高光|ラメ|글리터',
        '显色 / 持妆 / 质地': r'pigment|long-?lasting|longevity|texture|blend|formula|quality|显色|質感',
    },
    'tech': {
        **COMMON_POINTS,
        'AI 转写 + 总结': r'transcri|summar|要約|文字起こし|résum|resum|zusammenfass|rangkum|ringkas',
        '轻薄便携': r'thin|slim|credit[- ]card|tiny|small|compact|pocket|薄|小さ|名刺|kecil',
        '可穿戴': r'wearable|\bpin\b|wrist|necklace|clip|身につけ|ウェアラブル',
        '续航': r'hours|battery|バッテリー|horas',
        '收音 / 通话录音': r'phone call|calls?\b|通話|vibration|noise|ノイズ|clear audio|mic',
        '结构化产出（待办 / 导图）': r'mind ?map|マインドマップ|to-?do|action item|next step|template|テンプレ',
        '生态集成（AI / 第三方）': r'mcp|chatgpt|claude|notion|integrat|連携|agent|zapier',
        '隐私 / 安全': r'privacy|consent|同意|datenschutz|secure|gdpr|hipaa',
        '多语言': r'languages|言語|idiomas|langues|sprachen',
    },
    'app': {
        **COMMON_POINTS,
        '免费 / 订阅': r'free|subscription|premium|pro plan|无料|免费',
        'AI 能力': r'\bai\b|gpt|smart|automat',
        '简单易用': r'easy|simple|one tap|in seconds|簡単',
        '隐私': r'privacy|secure|private',
    },
    'general': dict(COMMON_POINTS),
}
