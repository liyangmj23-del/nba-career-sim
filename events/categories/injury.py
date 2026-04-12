"""
伤病类事件：10个。
伤病有连锁机制：重伤触发 -> 手术/康复 -> 复出。
"""
from events.event_registry import EventDefinition, Condition, AttrEffect, register

register(EventDefinition(
    key="injury.ankle.mild",
    category="injury",
    title="脚踝轻度扭伤",
    severity="minor",
    base_prob=0.06,
    conditions=[
        Condition("health", ">=", 60),
    ],
    attr_effects=[
        AttrEffect("health", (-15, -8)),
        AttrEffect("speed", (-5, -2), duration_weeks=2),
        AttrEffect("fatigue", (8, 15)),
    ],
    cooldown_weeks=4,
    narratives=[
        """第三节，你完成一次快下后落地，脚踝传来一阵钝痛。

你站起来，走了几步，点了点头，示意自己没事。
但训练师已经在赶来的路上了。

接下来两周你在理疗室和泡沫轴之间度过，
看着队友出发的背影，心里说不清是什么滋味。""",

        """那一步踩空了。

不严重——你去影像室看了片子，医生说两周休息，没有大问题。
"两周"这两个字听起来很短，但赛季里的两周可以发生很多事情。

你在场边坐着看队友练球，试着把这段时间当作调整。
你不确定自己信不信这个说法。""",
    ],
))

register(EventDefinition(
    key="injury.ankle.severe",
    category="injury",
    title="脚踝严重扭伤",
    severity="major",
    base_prob=0.025,
    conditions=[
        Condition("health", ">=", 50),
        Condition("fatigue", ">=", 40),
    ],
    attr_effects=[
        AttrEffect("health", (-30, -20)),
        AttrEffect("speed", (-10, -5), duration_weeks=5),
        AttrEffect("morale", (-15, -8)),
    ],
    cooldown_weeks=8,
    chains_to=["injury.recovery.ankle"],
    chain_delay=4,
    narratives=[
        """落地的那一刻，你听到了声音。

不是骨折，但韧带撕裂了。医生告诉你四到六周。
队友拍了拍你的肩，你点了点头，说：没事的。

回到更衣室，你一个人坐了很久。
不是因为疼，是因为你开始在脑子里算：四到六周，正好是季后赛争夺阶段。""",

        """你被架出场的时候，全场安静了片刻。

检查结果出来，韧带损伤，需要休养。
你躺在检查台上，盯着天花板，试图保持镇定。

手机上有几十条消息，你只回了妈妈那一条。""",
    ],
))

register(EventDefinition(
    key="injury.recovery.ankle",
    category="injury",
    title="脚踝康复进展",
    severity="normal",
    base_prob=1.0,   # 由连锁触发，概率无关
    conditions=[],
    attr_effects=[
        AttrEffect("health", (8, 15)),
        AttrEffect("speed", (3, 6)),
        AttrEffect("morale", (3, 8)),
    ],
    cooldown_weeks=99,
    one_time=False,
    narratives=[
        """理疗室的日子有一种奇怪的节律。

早上冰敷，中午电疗，下午在跑步机上做小步跑。
你开始能感觉到脚踝的力量在一点一点回来。

训练师说你恢复得比预期快。
你没有表现出来，但这几个字让你放松了很多。""",

        """今天你第一次在场上做了无球跑动。

没有剧烈接触，只是跑了几趟，
但那种踩在地板上的实感让你意识到——你要回来了。

你站在场边，看着场内的灯光，深呼了一口气。""",
    ],
))

register(EventDefinition(
    key="injury.hamstring",
    category="injury",
    title="腘绳肌拉伤",
    severity="normal",
    base_prob=0.04,
    conditions=[
        Condition("fatigue", ">=", 50),
    ],
    attr_effects=[
        AttrEffect("health", (-20, -12)),
        AttrEffect("speed", (-8, -3), duration_weeks=3),
        AttrEffect("endurance", (-5, -2), duration_weeks=3),
    ],
    cooldown_weeks=6,
    narratives=[
        """你在一次全力冲刺后感觉到了大腿后侧的拉扯感。

你立刻停下来，医疗人员检查了一下：腘绳肌拉伤，不严重，但需要休息三周。

三周。这是你听过很多次的数字，但每一次都一样难以接受。
身体总是在最不该出问题的时候出问题。""",

        """热身结束后你就感觉到了一点不对，但你没说。

第二节跑动中，那里突然一紧，你不得不示意换人。

医生说三周，说要注意，腘绳肌这个伤复发率不低。
你听着他说完，然后问：最快多久能上场？""",
    ],
))

register(EventDefinition(
    key="injury.acl_tear",
    category="injury",
    title="前交叉韧带撕裂",
    severity="legendary",
    base_prob=0.008,
    conditions=[
        Condition("health", ">=", 30),
    ],
    attr_effects=[
        AttrEffect("health", (-70, -50)),
        AttrEffect("speed", (-20, -10)),
        AttrEffect("vertical", (-15, -8)),
        AttrEffect("morale", (-30, -20)),
    ],
    cooldown_weeks=99,
    chains_to=["injury.acl_surgery", "injury.acl_rehab", "injury.acl_comeback"],
    chain_delay=2,
    one_time=True,
    narratives=[
        """你知道的那一秒，是膝盖扭转的时候。

你甚至还没有倒下，就已经知道了。
那种声音，那种感觉——你在某个地方读到过对它的描述，
但你从来没想过有一天会发生在自己身上。

你躺在地板上，训练师们跑过来，场边的观众安静下来。
你用手捂着眼睛，不是因为眼泪，是因为你不想让人看到你的表情。

赛季结束了。""",

        """医生说"完全撕裂"的时候，你没有立刻有反应。

你坐在检查室的椅子上，听他解释手术流程和康复时间，
点头，说谢谢，然后走出去。

在车里坐下来，你才真正感觉到了它的重量——
不只是今年，是接下来很长一段时间的未知。

你打给经纪人，告诉了他。挂掉电话之后，你一个人坐了很久。""",
    ],
))

register(EventDefinition(
    key="injury.acl_surgery",
    category="injury",
    title="手术结束",
    severity="major",
    base_prob=1.0,
    conditions=[],
    attr_effects=[
        AttrEffect("health", (5, 10)),
        AttrEffect("morale", (5, 10)),
    ],
    cooldown_weeks=99,
    narratives=[
        """手术室的灯很亮，然后就什么都没有了。

你醒来的时候，腿上有一种沉重的麻木。护士告诉你一切顺利。
你点点头，看着天花板，心里想的是：漫长的路刚刚开始。""",

        """手术完成了。

接下来是九个月的康复。你知道这条路怎么走——
一步一步，没有快捷方式，只有日复一日。

你拿起手机，看了看球队的近期赛程，然后把手机放下来。
有些事情现在想没有意义。""",
    ],
))

register(EventDefinition(
    key="injury.acl_rehab",
    category="injury",
    title="漫长的康复",
    severity="major",
    base_prob=1.0,
    conditions=[],
    attr_effects=[
        AttrEffect("health", (15, 25)),
        AttrEffect("speed", (5, 10)),
        AttrEffect("vertical", (3, 7)),
        AttrEffect("work_ethic", 3),
        AttrEffect("basketball_iq", 2),
    ],
    cooldown_weeks=99,
    narratives=[
        """康复的第一个月，你学会了一件事：忍耐。

不是对疼痛的忍耐——那个你已经习惯了——
是对进展缓慢的忍耐。理疗师每次都说"很好"，
但你看着镜子里自己迟缓的动作，知道"很好"和"可以打球"之间还有多远。

你把这段时间用来看比赛录像，看了几百场，
研究那些不需要膝盖告诉你的东西。""",

        """五个月了，你终于开始跑步了。

第一次全速冲刺，你在完成之后站在原地，不知道该高兴还是害怕。
膝盖没有任何异样的感觉，训练师在旁边默默记录着数据。

你转身，再跑一次。
然后又跑一次。""",
    ],
))

register(EventDefinition(
    key="injury.acl_comeback",
    category="injury",
    title="复出之夜",
    severity="legendary",
    base_prob=1.0,
    conditions=[],
    attr_effects=[
        AttrEffect("health", 20),
        AttrEffect("morale", (25, 35)),
        AttrEffect("leadership", 3),
        AttrEffect("clutch_factor", 3),
    ],
    cooldown_weeks=99,
    one_time=True,
    narratives=[
        """复出前一晚，你几乎没有睡着。

不是紧张——你已经把每一个动作在脑子里演练了无数遍。
是那种奇怪的感觉：你曾经理所当然地做着的事，现在重新变得珍贵了。

上场的时候，全场响起了你很久没有听到的那种欢呼。
你站在罚球线上，做了个深呼吸。

然后比赛开始了，你跑了起来——你的膝盖没有说话。
你跑了起来，就像什么都没发生过一样。

只有你知道，其实发生了很多事。""",

        """教练最后一次问你：确定了？

你说：确定了。

上场之后你打得很保守，你知道这一天不是证明什么的时候，
是重新找到节奏的时候。你完成了两次进攻，抢了一个篮板，没有出现任何问题。

下场的时候，场边给你一块毛巾。你擦了擦脸，
坐下来，看着场内的灯光，你知道这一章算是翻过去了。""",
    ],
))

register(EventDefinition(
    key="injury.back_spasms",
    category="injury",
    title="腰部痉挛",
    severity="minor",
    base_prob=0.05,
    conditions=[
        Condition("career_year", ">=", 5),
        Condition("fatigue", ">=", 35),
    ],
    attr_effects=[
        AttrEffect("health", (-12, -6)),
        AttrEffect("endurance", (-4, -2), duration_weeks=2),
        AttrEffect("fatigue", (10, 18)),
    ],
    cooldown_weeks=3,
    narratives=[
        """早上醒来，你一动就感觉到了。

腰那里痉挛着，医疗人员说要休息，不要硬撑。
你在床上躺着，盯着天花板，听着窗外的车声。

你已经不记得上次休息是什么时候了。""",

        """训练师说你最近训练量太大了。

你知道他说的是对的，但你没办法停下来——
这个阶段每一场比赛都重要。

腰部痉挛让你不得不停了两周。你坐在场边看着，
试着说服自己这是必要的。""",
    ],
))

register(EventDefinition(
    key="injury.fatigue_rest",
    category="injury",
    title="轮休保养",
    severity="minor",
    base_prob=0.08,
    conditions=[
        Condition("fatigue", ">=", 65),
        Condition("career_year", ">=", 8),
    ],
    attr_effects=[
        AttrEffect("fatigue", (-25, -15)),
        AttrEffect("health", (5, 12)),
        AttrEffect("morale", (2, 6)),
    ],
    cooldown_weeks=5,
    narratives=[
        """教练今天叫你去了他的办公室。

他说：你今晚不上了，我们让你休息。
你想反驳，但他已经继续说下去了：我们需要你在季后赛的时候还能跑。

你在场边坐了整场，看着队友打完，赢了。
腿上的那种沉重慢慢淡了，你承认：可能他是对的。""",

        """你的身体最近一直在告诉你同一件事。

训练师说你的疲劳指数超标了，建议休息一到两场。
你答应了，但"答应"不等于心里舒服。

看台上坐着的你盯着场上的比赛，在脑子里不停地做着如果自己在场上会怎么处理的判断。
休息的时候也没有真正地停下来。""",
    ],
))
