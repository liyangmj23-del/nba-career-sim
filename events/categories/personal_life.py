"""
个人生活类事件：9个。
以月为单位触发（monthly_only=True），频率较低。
"""
from events.event_registry import EventDefinition, Condition, AttrEffect, register

register(EventDefinition(
    key="personal.family_crisis",
    category="personal_life",
    title="家庭变故",
    severity="major",
    base_prob=0.06,
    monthly_only=True,
    conditions=[],
    attr_effects=[
        AttrEffect("morale", (-20, -10)),
        AttrEffect("basketball_iq", -2, duration_weeks=3),
        AttrEffect("fatigue", (5, 12)),
    ],
    cooldown_weeks=20,
    narratives=[
        """你在机场的时候接到了电话。

你把行李拖到角落里，站在人群旁边，听着电话里的声音。
你告诉自己保持镇定，但腿有点软。

联盟的规定允许你回家处理家庭紧急情况。
教练说：去吧，球队的事不用想。
你坐上了下一班飞机。

接下来几周，你在两个世界之间穿行——球场和家，
你很难说哪一个你更在乎，也很难说哪一个现在更能让你感到安全。""",

        """有些事情发生了，你不想对外说太多。

你请了几天假，教练批了，没有多问。
队友们也看出来了什么，但没有人追问，只是给你留了空间。

你回到球场的时候，有人拍了拍你的肩。没有话，但你知道什么意思。
你点了点头，说：好了，打球吧。""",
    ],
))

register(EventDefinition(
    key="personal.baby_born",
    category="personal_life",
    title="孩子出生了",
    severity="major",
    base_prob=0.04,
    monthly_only=True,
    conditions=[
        Condition("career_year", ">=", 3),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (15, 25)),
        AttrEffect("leadership", 2),
        AttrEffect("work_ethic", 2),
        AttrEffect("fatigue", (5, 10)),
    ],
    cooldown_weeks=99,
    narratives=[
        """凌晨三点，你在产房外面的走廊上来回走着。

门开了，护士把他/她递给你的时候，你整个人停住了。

你在脑子里演练过这个场景很多次，但你没有预料到那种重量——
不是孩子身体的重量，是你突然意识到，从现在起你的人生里有了另一个中心。

三天后你回到球队，打了这个赛季最好的两场比赛之一。
你也说不清楚为什么。""",

        """队友们在更衣室里把你围起来，轮流和你击掌。

你哭了，你没有试图隐藏它。
教练从办公室探出头，说：你他妈去好好打球，给孩子当个榜样。

你把他的名字写在球鞋内侧，那个地方只有你自己看得到。
每次换鞋的时候，你都会看一眼。""",
    ],
))

register(EventDefinition(
    key="personal.relationship_trouble",
    category="personal_life",
    title="感情出现裂痕",
    severity="normal",
    base_prob=0.05,
    monthly_only=True,
    conditions=[
        Condition("career_year", ">=", 2),
    ],
    attr_effects=[
        AttrEffect("morale", (-12, -6)),
        AttrEffect("fatigue", (3, 8)),
        AttrEffect("media_handling", (-3, -1)),
    ],
    cooldown_weeks=12,
    chains_to=["personal.relationship_resolved"],
    chain_delay=3,
    narratives=[
        """你们在电话里吵架了，然后挂断了。

你坐在宾馆的床上，看着窗外陌生城市的灯光，
想着她说的那些话——关于你总是不在、关于你把一切都给了球场。

你知道她说的不全是错的。你也知道你无法改变那些事情。
这种无解的感觉比争吵本身更重。""",

        """已经好几天没有好好通话了。

你们都在忙，但"忙"不是全部的原因。
你感觉到了两个人之间那条细细的裂缝，但你不知道从哪里开始修复。

训练的时候，你把注意力全部放在球上。
球场是唯一一个你知道规则的地方。""",
    ],
))

register(EventDefinition(
    key="personal.relationship_resolved",
    category="personal_life",
    title="重归于好",
    severity="normal",
    base_prob=1.0,   # 连锁触发
    conditions=[],
    attr_effects=[
        AttrEffect("morale", (8, 15)),
        AttrEffect("media_handling", (2, 4)),
    ],
    cooldown_weeks=99,
    narratives=[
        """你们终于坐下来，好好说话了。

没有吵架，只是说话。
说了很多平时忙起来顾不上说的事情，说到很晚。

挂断电话的时候你觉得轻了一点。
不是所有问题都解决了，但你们又在同一边了。
那已经足够了。""",

        """她飞过来陪了你三天。

你请了两天假，带她去了这座城市你最喜欢的一个地方。
那三天，你没有打开手机看新闻，没有想战术，什么都没想。

她走的时候，你送她到机场，你们都没有多说什么。
但你回到球馆的那天，打得特别好。""",
    ],
))

register(EventDefinition(
    key="personal.hometown_return",
    category="personal_life",
    title="回到家乡城市",
    severity="normal",
    base_prob=0.08,
    monthly_only=True,
    conditions=[],
    attr_effects=[
        AttrEffect("morale", (8, 15)),
        AttrEffect("clutch_factor", 2),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=10,
    narratives=[
        """你小时候站在这个球馆外面，买不到票，只能趴在栅栏上听里面的声音。

今晚你走进去，是作为客队的一员。
更衣室里，你在心里笑了一下。

在这座城市，你认识的人从来没有停止关注你。
今晚你看见了很多熟悉的脸，也看见了很多从小看着你长大的眼神。
你打了一场很认真的比赛。""",

        """客队更衣室门口，有几个孩子在等你要签名。

其中一个戴着你早年号码的球衣——那件球衣现在已经停产了。
你把他们叫过来，一个一个签，然后和他们合了照。

这座城市塑造了你的很多部分。
每次回来，你都会想起那个还不知道自己能走多远的孩子。""",
    ],
))

register(EventDefinition(
    key="personal.endorsement_deal",
    category="personal_life",
    title="签下赞助合同",
    severity="normal",
    base_prob=0.05,
    monthly_only=True,
    conditions=[
        Condition("overall_rating", ">=", 65),
        Condition("media_handling", ">=", 50),
    ],
    attr_effects=[
        AttrEffect("morale", (6, 12)),
        AttrEffect("media_handling", 2),
    ],
    cooldown_weeks=15,
    narratives=[
        """经纪人发来合同，你签字之前认真看了一遍。

数字让你沉默了片刻。不是因为多，是因为你意识到，
这些数字说明有人认为你值这些——不只是在场上，也在场外。

你记得你爸妈知道你要打职业球的时候说的话：
先把书读好，打球的事再说。
你拨了他们的电话。""",

        """拍宣传片那天，你站在镜头前面，感觉有点奇怪。

你习惯的是球场上的灯光，不是摄影棚的。
但导演说你很自然，你也不确定他说的是真的还是客套话。

鞋子发布那天，评论区里有很多你认识的名字。
你截图，发给了妈妈。""",
    ],
))

register(EventDefinition(
    key="personal.charity_event",
    category="personal_life",
    title="社区公益活动",
    severity="minor",
    base_prob=0.07,
    monthly_only=True,
    conditions=[],
    attr_effects=[
        AttrEffect("morale", (4, 8)),
        AttrEffect("media_handling", 1),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=8,
    narratives=[
        """你去了一所学校，在体育馆里给孩子们讲球。

准备了很多干货，到最后变成了答疑——
孩子们问的问题大多数是关于你的日常生活，
最多的一个问题是：联盟的球馆真的那么大吗？

你说：比你们想象的还要大。然后带着他们做了半小时训练。""",

        """今天的活动结束之后，你在路上堵了一个小时。

但你没觉得浪费了时间。
有个小孩在活动结束后追上来，塞给你一张纸条，
上面写着：我以后也要打NBA。

你把那张纸条放进了口袋里，带回了酒店。""",
    ],
))

register(EventDefinition(
    key="personal.mental_fatigue",
    category="personal_life",
    title="心理疲惫",
    severity="normal",
    base_prob=0.05,
    monthly_only=True,
    conditions=[
        Condition("morale", "<=", 55),
        Condition("career_year", ">=", 3),
    ],
    attr_effects=[
        AttrEffect("morale", (-10, -5)),
        AttrEffect("fatigue", (8, 15)),
        AttrEffect("media_handling", (-4, -2)),
    ],
    cooldown_weeks=10,
    narratives=[
        """不是受伤，不是输球，只是一种疲倦。

不是身体的疲倦——那个你已经学会了管理——
是你说不清楚的那种：起床、训练、比赛、飞机、宾馆、重复。

你有一周没有好好睡觉，有时候坐在更衣室里什么也不想做。
你没有告诉任何人，你告诉自己这只是一个阶段。
但你也开始怀疑，是不是应该和球队心理辅导谈谈。""",

        """赛季到了这个节点，你开始感觉到一种压力的积累。

不来自任何一件具体的事，是所有事的总和——
成绩的期待，身体的管理，场外的事，还有你自己对自己的要求。

你找了球队的心理辅导谈了一次。
他听你说了四十分钟，说了一句话：
你已经在试着做很多事情了，有时候允许自己先停下来。
你出来之后，在停车场里坐了一会儿。""",
    ],
))

register(EventDefinition(
    key="personal.veteran_mentor",
    category="personal_life",
    title="前辈的教导",
    severity="normal",
    base_prob=0.06,
    monthly_only=True,
    conditions=[
        Condition("career_year", "<=", 4),
    ],
    attr_effects=[
        AttrEffect("basketball_iq", (2, 4)),
        AttrEffect("morale", (5, 10)),
        AttrEffect("work_ethic", 1),
    ],
    cooldown_weeks=8,
    narratives=[
        """你在训练结束后留下来练投篮，他走过来站在你旁边。

他没有立刻说话，看了你出手几次，然后说：
你投球的时候重心靠后了，你知道吗？

你不知道。你以为你知道自己的出手，
但他站在那里给你示范了一遍，你立刻明白了那个区别。

你们在球场上又多待了一个小时。
那一个小时，你学到的东西比你一个人练一个月学到的更多。""",

        """他请你去吃饭，点了一家安静的餐厅。

你们聊了很多，不全是关于篮球。
他说了一些关于联盟的事，关于如何在这里长期待下去，
关于什么值得，什么不值得。

你认真听着。你知道这种话不是每个人都会对你说的。""",
    ],
))
