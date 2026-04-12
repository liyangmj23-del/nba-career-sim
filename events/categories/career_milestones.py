"""
生涯里程碑事件：11个。
大多数设为 one_time=True，使用条件门控，只触发一次。
"""
from events.event_registry import EventDefinition, Condition, AttrEffect, register

register(EventDefinition(
    key="milestone.nba_debut",
    category="career_milestones",
    title="NBA 生涯首战",
    severity="legendary",
    base_prob=1.0,
    conditions=[
        Condition("career_year", "==", 1),
        Condition("week_number", "==", 1),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", 20),
        AttrEffect("basketball_iq", 2),
    ],
    narratives=[
        """你记得热身的时候双腿是抖的。

不是恐惧——或者说，不只是恐惧。是那种你等了很多年的东西，
在那一刻同时涌上来了。

上场的哨声响起，你跑进场内，脚踩上那块地板，
你知道你在这里有一席之地。

之后发生了什么，你记得很清楚，也记得很模糊。
但你知道你打完了全场，你的名字第一次出现在正式的比赛记录里。
那个夜晚，你睡得很好。""",

        """你从小就把这一幕想象过无数次。

当它真的发生的时候，和你想象的不完全一样——
更嘈杂、更快、更真实。你被两个人夹击，失误了一次。
你有一次没抓住传球，站在那里看着球滚出界外。

但比赛结束了，你走出来，你没有崩掉。
这就是今晚最重要的事情。""",
    ],
))

register(EventDefinition(
    key="milestone.first_allstar",
    category="career_milestones",
    title="首次全明星当选",
    severity="legendary",
    base_prob=0.0,   # 由引擎逻辑检查当选，不走概率
    conditions=[
        Condition("career_year", ">=", 2),
        Condition("overall_rating", ">=", 78),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (25, 35)),
        AttrEffect("leadership", 3),
        AttrEffect("media_handling", 3),
        AttrEffect("clutch_factor", 2),
    ],
    narratives=[
        """名单公布那天，你正在宾馆房间里看手机。

你的名字出现在屏幕上，你读了三遍才确认不是看错了。

你打给妈妈。
她在电话那头哭了起来，你说没什么大不了，
但挂掉电话之后，你在床边坐了很久。

你想起了所有那些早起训练、伤病、低谷和怀疑的时刻。
你想：这些都是值得的。""",

        """经纪人发来消息的时候你正在训练馆的跑步机上。

你停下来，看着那几个字，然后继续跑。
你需要用运动让自己确认这是真实的。

当晚你去了一家安静的餐厅，自己一个人坐着，
点了一份很好的东西，慢慢吃完，慢慢离开。
这是你给自己庆祝的方式。""",
    ],
))

register(EventDefinition(
    key="milestone.all_nba",
    category="career_milestones",
    title="年度最佳阵容",
    severity="legendary",
    base_prob=0.0,
    conditions=[
        Condition("overall_rating", ">=", 83),
        Condition("career_year", ">=", 3),
    ],
    one_time=False,  # 可多次获得
    attr_effects=[
        AttrEffect("morale", (20, 28)),
        AttrEffect("leadership", 2),
        AttrEffect("media_handling", 2),
    ],
    cooldown_weeks=52,
    narratives=[
        """最佳阵容的名单发出来的时候，你在机场。

你把手机放下，上了飞机。
飞机起飞之后，你靠在椅背上，合上眼睛。
有时候最大的荣誉反而会让人沉下来，而不是飘起来。

你知道这个结果说明了什么，也知道它会带来什么——
更高的期待，更多的目光，以及更难的一年。
你准备好了。""",

        """球队里有人替你高兴，赛后在更衣室里喊了一声。

你低着头笑了。
你没有发社交媒体，没有接受现场采访，只是在回去的路上，
打给了当初在你最迷茫的时候帮助过你的人。
他说：我早知道你能到这里。
你说：谢谢你。""",
    ],
))

register(EventDefinition(
    key="milestone.scoring_title",
    category="career_milestones",
    title="得分王",
    severity="legendary",
    base_prob=0.0,
    conditions=[
        Condition("overall_rating", ">=", 85),
        Condition("shooting_2pt", ">=", 70),
    ],
    one_time=False,
    attr_effects=[
        AttrEffect("morale", (20, 30)),
        AttrEffect("clutch_factor", 3),
        AttrEffect("media_handling", 2),
    ],
    cooldown_weeks=52,
    narratives=[
        """这个赛季你几乎每场都要背负对方最严密的防守。

但你在这个过程中学会了更多——更多的出手时机，
更多的出手方式，更多的与对手博弈的手段。

赛季结束，得分榜第一是你的名字。
你记得第一场比赛和最后一场比赛，
中间的一切都变成了一种模糊而厚重的积累。""",

        """你们第一次得到这个消息是在季末新闻发布会上。

记者问你什么感受，你想了想，说：
这说明我今年整个赛季的稳定性是对的。
然后他们继续问你别的问题，你也继续回答。

回到更衣室，你对着镜子，允许自己笑了一下。""",
    ],
))

register(EventDefinition(
    key="milestone.mvp",
    category="career_milestones",
    title="常规赛 MVP",
    severity="legendary",
    base_prob=0.0,
    conditions=[
        Condition("overall_rating", ">=", 88),
        Condition("career_year", ">=", 4),
    ],
    one_time=False,
    attr_effects=[
        AttrEffect("morale", (30, 40)),
        AttrEffect("leadership", 4),
        AttrEffect("clutch_factor", 3),
        AttrEffect("media_handling", 3),
    ],
    cooldown_weeks=52,
    narratives=[
        """颁奖典礼上，他们念到你的名字的时候，
你站起来，听见了整个场馆的声音。

你走上台，拿着那个奖杯，说了几分钟话。
你提到了你的队友，你的教练，你的家人，
还有几个在很早之前相信你的人的名字。

你说：我不知道我能走多远。我只知道还没到头。

回到座位，有人给你拍了张照片。
你把它存了下来，一直放在手机里。""",

        """你没想到是今年。

你以为还需要再打几年，再证明几次，
但投票结果就是这样出来的，别人看到的东西和你自己看到的不一样。

你接受了这个奖，你感谢了所有该感谢的人，然后你继续打球。
奖杯放在家里一个不显眼的地方。它重要，但它不是全部。""",
    ],
))

register(EventDefinition(
    key="milestone.finals_mvp",
    category="career_milestones",
    title="总决赛 MVP 暨总冠军",
    severity="legendary",
    base_prob=0.0,
    conditions=[
        Condition("career_year", ">=", 3),
        Condition("overall_rating", ">=", 80),
    ],
    one_time=False,
    attr_effects=[
        AttrEffect("morale", (40, 50)),
        AttrEffect("leadership", 5),
        AttrEffect("clutch_factor", 4),
        AttrEffect("basketball_iq", 3),
    ],
    cooldown_weeks=52,
    narratives=[
        """最后一节最后两分钟，你的心跳清晰得像是在你耳边。

不是慌乱，是一种高度清醒——你感觉自己能看见场上的每一条路线，
每一个空档，每一个即将发生的事情。

终场哨响的时候，你还站在场上，没有立刻跳起来。
你向前走了几步，看着这座球馆，让这一刻在你脑子里停留了几秒钟。

然后队友把你扑倒了，一切都乱成了一片，你笑了起来，眼泪也来了。
你不知道哪个先来的。""",

        """颁奖台上，他们把那座奖杯举起来递给你。

你接住了它，它比你想象的沉。
你把它举过头顶，看着台下那些人，那些灯光，
看着你的队友在旁边哭、笑、互相抱在一起。

你深呼了一口气，告诉自己：记住这一刻。
无论接下来发生什么，这一刻是真实的。""",
    ],
))

register(EventDefinition(
    key="milestone.contract_max",
    category="career_milestones",
    title="签下顶薪合同",
    severity="major",
    base_prob=0.0,
    conditions=[
        Condition("overall_rating", ">=", 80),
        Condition("career_year", ">=", 4),
    ],
    one_time=False,
    attr_effects=[
        AttrEffect("morale", (15, 25)),
        AttrEffect("work_ethic", 2),
    ],
    cooldown_weeks=52,
    narratives=[
        """谈判拖了几个月，今天终于定下来了。

你的经纪人发来合同文本，你认真看了每一条，
然后签字，发回去。

电话那头，他说：恭喜。
你说：开始干活了。

你知道这份合同不只是认可，也是压力。
你想要用接下来每一年的比赛来证明这份合同是对的。""",

        """签完之后你没有立刻对外说什么。

只是告诉了几个最重要的人——父母，还有两三个朋友。
他们的反应各不相同，但那份真实的高兴是一样的。

你上网买了一双鞋，是你一直想要但觉得太贵的那双。
这是你给自己的唯一一个小庆祝。""",
    ],
))

register(EventDefinition(
    key="milestone.retirement_thought",
    category="career_milestones",
    title="第一次想到退役",
    severity="major",
    base_prob=0.0,
    conditions=[
        Condition("career_year", ">=", 15),
        Condition("health", "<=", 60),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (-5, 5)),
        AttrEffect("basketball_iq", 2),
        AttrEffect("leadership", 2),
    ],
    cooldown_weeks=99,
    narratives=[
        """你在更衣室里换鞋的时候，突然停了一下。

你坐在那里，看着球鞋，看着自己的手，
脑子里那个念头很轻地出现了：也许，不是现在，
但也许某一天，这件事会结束。

你换好鞋，走出去，打了一场比赛。
但那个念头还在那里，没有消失，也没有让你恐慌——
你只是第一次认真地想了想它。""",

        """赛后你在按摩床上躺着，天花板很白。

医疗师在处理你的膝盖，你闭着眼睛，
想着今年还剩多少场，明年还能打多少年。

你没有答案，也不急着找答案。
你只是第一次清晰地意识到：这件事有一天会结束。
那个"一天"，会是你可以选择的吗？""",
    ],
))

register(EventDefinition(
    key="milestone.rookie_of_year",
    category="career_milestones",
    title="年度最佳新秀",
    severity="legendary",
    base_prob=0.0,
    conditions=[
        Condition("career_year", "==", 1),
        Condition("overall_rating", ">=", 72),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (25, 35)),
        AttrEffect("media_handling", 3),
        AttrEffect("leadership", 2),
    ],
    cooldown_weeks=99,
    narratives=[
        """你的第一年比你预期的更好，也更难。

拿到最佳新秀奖的时候，你想到的第一件事不是庆祝，
是所有在这一年里你没有做好的细节。

但你把这个念头收了起来。今晚可以先高兴一会儿，
明天再继续挑那些细节。""",

        """颁奖典礼在季末举行，你穿着西装，坐在台下。

念到你名字的时候，你旁边的人推了你一把——你还没反应过来。
你站起来，走上台，接过奖杯，说了几句话，
然后走下来，回到座位。

感觉没有你想象的那么大，也没有你担心的那么飘。
你知道这只是一个开始。""",
    ],
))

register(EventDefinition(
    key="milestone.decade_veteran",
    category="career_milestones",
    title="联盟十年老兵",
    severity="major",
    base_prob=0.0,
    conditions=[
        Condition("career_year", "==", 10),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (10, 18)),
        AttrEffect("leadership", 3),
        AttrEffect("basketball_iq", 2),
        AttrEffect("media_handling", 2),
    ],
    cooldown_weeks=99,
    narratives=[
        """十年了。

你试着回忆第一年的感觉，发现那些细节已经有一些模糊了。
你记得感受，但有些场景已经说不清楚细节。

十年里，你认识了很多人，离开了很多城市，
赢过很多比赛，也输过很多比赛。
你不是当年那个走进联盟的那个人了。

你比他更好，也比他更知道这件事有多难。""",

        """更衣室里，年轻的队友问你：你第一年打的什么感觉？

你想了一下，说：怕。

他有点惊讶。你继续说：怕做不好，怕跟不上，怕浪费这个机会。
现在不怕了，因为我已经知道自己能做什么了。

那个孩子点了点头，很认真的那种。
你拍了拍他的肩，说：你也会知道的。""",
    ],
))

register(EventDefinition(
    key="milestone.record_broken",
    category="career_milestones",
    title="打破球队历史记录",
    severity="major",
    base_prob=0.0,
    conditions=[
        Condition("career_year", ">=", 8),
        Condition("overall_rating", ">=", 75),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", (15, 22)),
        AttrEffect("leadership", 2),
        AttrEffect("media_handling", 2),
    ],
    cooldown_weeks=99,
    narratives=[
        """裁判叫了暂停，球馆的广播开始播报。

你站在场上，听着那些数字，
听着旁边的解说在讲一些你已经知道的历史，
然后全场开始鼓掌。

你举了举手，不知道该说什么，也不需要说什么。
你转身，示意队友们继续比赛。

这不是终点，只是一个数字翻页了。""",

        """你是在赛后从队友口中知道这件事的。

他们把你围起来，你才反应过来那个进球意味着什么。
你笑了，说：我以为那只是普通的一球。
他们说：那就是最厉害的地方。""",
    ],
))
