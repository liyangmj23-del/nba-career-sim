"""
场外事件：9个。
以月为单位触发，频率较低。
"""
from events.event_registry import EventDefinition, Condition, AttrEffect, register

register(EventDefinition(
    key="offcourt.media_buzz",
    category="off_court",
    title="媒体热度飙升",
    severity="normal",
    base_prob=0.08,
    conditions=[
        Condition("media_handling", ">=", 45),
    ],
    attr_effects=[
        AttrEffect("morale", (3, 8)),
        AttrEffect("media_handling", 1),
    ],
    cooldown_weeks=6,
    narratives=[
        """最近几场的数据让你上了很多平台的推荐位。

采访邀请变多了，训练馆外的人也多了一点。
你没有刻意去看那些评论，但你知道它们在那里。

你打电话给经纪人，他说：把握节奏，不要说太多。
你说：我知道。
你确实知道。""",

        """有一个视频在社交媒体上传播，里面是你这周的一个进球。

播放量让你经纪人很高兴。
你点进去看了一眼，关掉了。
你更在意的是那个进球是在对的防守时机产生的，
不是在某个流量数字。""",
    ],
))

register(EventDefinition(
    key="offcourt.media_controversy",
    category="off_court",
    title="媒体风波",
    severity="normal",
    base_prob=0.04,
    conditions=[
        Condition("media_handling", "<=", 60),
    ],
    attr_effects=[
        AttrEffect("morale", (-10, -5)),
        AttrEffect("media_handling", (-5, -2)),
    ],
    cooldown_weeks=10,
    narratives=[
        """那句话被断章取义了，或者说，你当时确实没有想清楚再说。

赛后采访结束，片段发出来，评论区炸了。
经纪人打来电话的时候，你已经知道发生了什么。

他说：什么都不要说，让我来处理。
你把手机放下，看着窗外，
试着想清楚这件事从哪里开始出错的。""",

        """记者问了一个刁钻的问题，你没有绕开，你直接回答了。

你没想到会有这么大的反应。
内容变成了话题，话题变成了争议，争议持续了整整一周。
你不得不在下次新闻发布会上做了一点解释，
虽然你认为那句话本来就是对的。

有时候说真话比说错话更麻烦。""",
    ],
))

register(EventDefinition(
    key="offcourt.trade_rumor",
    category="off_court",
    title="交易传言",
    severity="normal",
    base_prob=0.06,
    monthly_only=True,
    conditions=[
        Condition("morale", "<=", 65),
    ],
    attr_effects=[
        AttrEffect("morale", (-8, -3)),
        AttrEffect("fatigue", (3, 7)),
    ],
    cooldown_weeks=8,
    narratives=[
        """你在网上看到了自己名字出现在了一篇报道里。

是交易报道，还带着"消息人士称"这种开头。
你不知道这是真的还是有人在放风，但你知道一旦名字出来，
就会有影响——无论最终发生了什么。

训练时你感觉有人看你的眼神和平时不太一样。
你什么也没有说，只是认真打完了训练。""",

        """经纪人告诉你，有球队在问你的情况。

你没有立刻有反应，只是问：哪支球队？
然后他说了名字，你想了一下那座城市。

你挂掉电话，回到训练馆，换上鞋，专注于眼前的练习。
那些事情轮不到你决定，所以你不去花精力想它。""",
    ],
))

register(EventDefinition(
    key="offcourt.social_media_incident",
    category="off_court",
    title="社交媒体翻车",
    severity="major",
    base_prob=0.025,
    conditions=[
        Condition("media_handling", "<=", 55),
    ],
    attr_effects=[
        AttrEffect("morale", (-15, -8)),
        AttrEffect("media_handling", (-8, -4)),
    ],
    cooldown_weeks=15,
    narratives=[
        """你发了一条你以为只有朋友看的内容。

它扩散了。

经纪人在凌晨两点打来电话，你在半睡半醒中接的，
然后彻底清醒了。

接下来几天，你删了那条内容，不接采访，
关掉了一半的通知，闭关了一段时间。
你不得不认真考虑一件事：你的公众形象，和你自己，并不是同一件事。""",

        """那条内容发出去之后你立刻意识到出错了。

但已经有人截图了。
你试着删除，但网络上的东西一旦传播开就没有"删除"。

你和经纪人、公关一起写了一份声明，
说了你真实的意思，解释了那句话的背景。
有人接受了，有人不接受。这件事花了你很多精力，
让你明白有些话要等你准备好了再说。""",
    ],
))

register(EventDefinition(
    key="offcourt.podcast_interview",
    category="off_court",
    title="播客专访",
    severity="minor",
    base_prob=0.06,
    monthly_only=True,
    conditions=[
        Condition("media_handling", ">=", 50),
        Condition("career_year", ">=", 3),
    ],
    attr_effects=[
        AttrEffect("morale", (4, 8)),
        AttrEffect("media_handling", 2),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=10,
    narratives=[
        """你接受了一档球员播客的邀请，录了两个小时。

对方问了很多你平时不会在正式采访里被问到的问题——
关于你小时候怎么开始打球的，关于你最喜欢的球员，
关于你场外是什么样的人。

你比你预期的说了更多，聊得有点放开了。
出来的时候感觉有点奇怪，但不是坏的那种奇怪。""",

        """录完之后主持人说：这期反响一定很好。

你笑了笑，没太当回事。
但节目出来之后，你意外地收到了很多陌生人的消息，
说他们更了解你了，说他们开始关注你了。

你把其中一条发给了你妈，她说：你在里面讲了我。
你说：你不是第一次出现在别人的播客里了。""",
    ],
))

register(EventDefinition(
    key="offcourt.documentary",
    category="off_court",
    title="纪录片拍摄",
    severity="normal",
    base_prob=0.03,
    monthly_only=True,
    conditions=[
        Condition("career_year", ">=", 5),
        Condition("overall_rating", ">=", 72),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (5, 10)),
        AttrEffect("media_handling", 3),
        AttrEffect("fatigue", (3, 8)),
    ],
    cooldown_weeks=99,
    narratives=[
        """摄制组跟拍了好几个月，你已经快忘了他们的存在了。

他们拍了训练、拍了比赛、拍了你在飞机上睡觉。
有时候你对着镜头讲一些东西，有时候你让他们离远一点。

看样片的时候，你看着屏幕上的自己，
感觉有点陌生，又有点熟悉——
这是别人眼里的你，不是你自己知道的那个你。""",

        """纪录片发布之后，你没有第一时间看完整版。

你知道里面有什么，因为你经历过那些事情。
但通过别人的镜头看这些，需要一段时间做好准备。

发布两周后，你找了一个安静的下午，一个人看完了。
看完之后，你在那里坐了一会儿，没有立刻做任何事。""",
    ],
))

register(EventDefinition(
    key="offcourt.allstar_weekend",
    category="off_court",
    title="全明星周末",
    severity="normal",
    base_prob=0.0,   # 通过全明星资格判断触发
    conditions=[
        Condition("career_year", ">=", 2),
        Condition("overall_rating", ">=", 78),
    ],
    attr_effects=[
        AttrEffect("morale", (10, 18)),
        AttrEffect("media_handling", 2),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=52,
    narratives=[
        """全明星周末是一种奇特的存在。

所有最好的球员都在同一个地方，没有真正的竞争，只有展示。
你在技巧大赛看台上坐着，旁边是你小时候海报贴满卧室的那些人，
现在他们和你说话，就像同事一样。

你心里有点感慨，但你没有表现出来。
你只是笑着回应，然后把这一刻悄悄存进了某个地方。""",

        """全明星之夜，你打了一段时间，然后下场。

没有人在全明星赛打认真的防守，所以你也没有。
你享受了这种轻松的一面，和对方球员互相说了几句话，
在场上做了几个你平时不会冒险去做的传球。

观众很高兴，你也高兴。
这是这份工作里少数几个没有压力的时刻之一。""",
    ],
))

register(EventDefinition(
    key="offcourt.shoes_release",
    category="off_court",
    title="个人签名球鞋发布",
    severity="major",
    base_prob=0.0,   # 条件门控
    conditions=[
        Condition("overall_rating", ">=", 82),
        Condition("media_handling", ">=", 55),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (12, 20)),
        AttrEffect("media_handling", 3),
    ],
    cooldown_weeks=99,
    narratives=[
        """设计过程比你想象的要长。

你参与了好几轮讨论，提了一些你觉得重要的细节——
一些只有你自己知道意义的东西：一个数字，一个颜色，
一个你和家人之间才知道的小东西。

发布那天，你在店里看见有人在买，
那个人不知道你站在旁边。你决定不出声，只是看了一会儿，然后走了。""",

        """第一双正式生产的样品快递到你手上的时候，
你拆开纸箱，从里面取出来，举在光线下看了一圈。

它不完美，有一个小细节和你想象的有一点出入。
但它存在了，它是真实的，上面有你的名字。

你在更衣室里穿上了它，踩了踩，点了点头。""",
    ],
))

register(EventDefinition(
    key="offcourt.food_investment",
    category="off_court",
    title="场外投资",
    severity="minor",
    base_prob=0.04,
    monthly_only=True,
    conditions=[
        Condition("career_year", ">=", 4),
    ],
    attr_effects=[
        AttrEffect("morale", (3, 7)),
        AttrEffect("media_handling", 1),
    ],
    cooldown_weeks=20,
    narratives=[
        """你投资了一个餐厅，老板是你认识了很多年的朋友。

你没有参与经营，只是出了一部分钱，然后偶尔过去吃饭。
有时候坐在那里，看着客人进进出出，
你会想：这件事和篮球是完全不同的事情，
但你在里面找到了一种别的满足感。""",

        """经纪人帮你梳理了一些投资方向，你选了其中一个。

不是最高收益的那个，是你最感兴趣的那个。
你知道有一天打球会结束，在那之前你需要想清楚之后的事情。
这是第一步——很小的一步，但是你自己主动走出来的。""",
    ],
))
