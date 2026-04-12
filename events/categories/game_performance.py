"""
比赛表现类事件：12个。
基于本周比赛数据（得分、连胜/连败等）触发。
"""
from events.event_registry import EventDefinition, Condition, AttrEffect, register

register(EventDefinition(
    key="perf.hot_streak",
    category="game_performance",
    title="状态火热",
    severity="normal",
    base_prob=0.12,
    conditions=[
        Condition("week_avg_pts", ">=", 28),
        Condition("week_wins", ">=", 2),
    ],
    attr_effects=[
        AttrEffect("morale", (3, 8)),
        AttrEffect("clutch_factor", 1),
    ],
    cooldown_weeks=3,
    narratives=[
        """连续几场下来，你已经说不清楚这种状态是从哪里来的。

每次接球，脑子里的杂念都少了一点——剩下的只有节奏，和那个你早已练烂的动作。

教练开始多给你球。对手也开始专程派人盯着你。
但这些都不影响什么。

这一周你打得很好，你自己知道。""",

        """训练师在更衣室里问你最近吃什么了。

你没法解释。有时候就是这样——身体会自己找到一种频率，
然后接下来一段时间，你比任何人都清楚球往哪飞。

你把这种感觉默默收好，不和任何人说。""",
    ],
))

register(EventDefinition(
    key="perf.cold_snap",
    category="game_performance",
    title="手感冰凉",
    severity="minor",
    base_prob=0.13,
    conditions=[
        Condition("week_avg_pts", "<=", 12),
        Condition("overall_rating", ">=", 55),
    ],
    attr_effects=[
        AttrEffect("morale", (-8, -3)),
        AttrEffect("fatigue", (3, 7)),
    ],
    cooldown_weeks=2,
    narratives=[
        """出手、铁了。再出手、又铁了。

你站在罚球线延长线上，看着对面的球飞走，脑子里转着那些动作分解——
但这有什么用呢，手感是个不讲道理的东西。

赛后你比任何人都晚离开训练馆，一个人把每个出手位置都重新走了一遍。""",

        """连续几场下来，数据摆在那里，不好看。

你能感觉到更衣室里有些眼神，虽然没人说什么。
社交媒体更直接——你没有打开，但你知道里面有什么。

你告诉自己这只是周期。你也说不准这是真的还是在安慰自己。""",
    ],
))

register(EventDefinition(
    key="perf.buzzer_beater",
    category="game_performance",
    title="压哨绝杀",
    severity="major",
    base_prob=0.04,
    conditions=[
        Condition("week_wins", ">=", 1),
        Condition("clutch_factor", ">=", 45),
    ],
    attr_effects=[
        AttrEffect("morale", (10, 18)),
        AttrEffect("clutch_factor", 2),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=6,
    chains_to=["offcourt.media_buzz"],
    chain_delay=1,
    narratives=[
        """倒计时走到 0.3 秒的时候，球场的噪音突然在你耳中消失了。

你接到传球，转身，起跳。
这一刻你只看见篮筐，其他的都不存在。

球出手的瞬间你已经知道了。

全场在你落地之前就已经爆发。
队友把你扑倒，你被埋在人堆里，什么也看不见，只能感觉到那种重量。""",

        """最后一攻，教练的战术板你只听了一半。

球转过来，你没犹豫。
手指离开球的那一刻时间停住了，然后刷的一声，
所有人都开始叫起来。

你在更衣室里坐了很久，心跳还没有平稳。
这一晚上你会记很长时间。""",
    ],
))

register(EventDefinition(
    key="perf.triple_double",
    category="game_performance",
    title="三双表演",
    severity="normal",
    base_prob=0.07,
    conditions=[
        Condition("week_avg_pts", ">=", 18),
        Condition("passing", ">=", 55),
        Condition("rebounds_context", ">=", 7),
    ],
    attr_effects=[
        AttrEffect("morale", (5, 10)),
        AttrEffect("basketball_iq", 1),
    ],
    cooldown_weeks=4,
    narratives=[
        """今晚你不是在追数字。

但数字在最后就在那里：双位数的分数、双位数的篮板、双位数的助攻。

赛后记者追着你问感受。
你说：赢球才是最重要的。
这是真话，但也不是全部的真话——
你当然知道这场比赛打出了什么。""",

        """场上的几次决策，你自己觉得很对。

当双队包夹来的时候，你放弃了出手，找到了空切的队友。
当界外球发进来，你抢第一时间要球，打了一个快下。

赛后教练在白板前专门分析你这场。
更衣室里有人说：你今晚像个控卫。
你没说话，但心里觉得这话说到点子上了。""",
    ],
))

register(EventDefinition(
    key="perf.explosion_40",
    category="game_performance",
    title="职业生涯级别的爆发",
    severity="major",
    base_prob=0.025,
    conditions=[
        Condition("week_high_pts", ">=", 38),
        Condition("overall_rating", ">=", 65),
    ],
    attr_effects=[
        AttrEffect("morale", (12, 20)),
        AttrEffect("clutch_factor", 2),
        AttrEffect("media_handling", 1),
    ],
    cooldown_weeks=8,
    chains_to=["offcourt.media_buzz"],
    chain_delay=1,
    narratives=[
        """没有人能解释这一晚上发生了什么。

你从第一节就进入了那种状态——不是热身，是直接点燃。
每一次出手你都知道它会进。
对方换了三个防守人，都没有用。

最终你拿下 {pts} 分，场馆里的声音像海浪一样。
赛后更衣室里，老将拍了拍你的肩膀，什么话都没说。
这已经够了。""",

        """第三节还剩四分钟，你已经有三十多分了。

那一刻场上的时间好像变慢了——你能看见防守人的每一个脚步，
能感受到空档在哪里，一切都慢下来，只有你的动作是清晰的。

{pts} 分。赛后有人说这是今年的最佳发挥之一。
你在更衣室里对着镜子，认真地看了自己一眼。""",
    ],
))

register(EventDefinition(
    key="perf.blowout_loss",
    category="game_performance",
    title="惨败夜",
    severity="minor",
    base_prob=0.09,
    conditions=[
        Condition("week_wins", "==", 0),
        Condition("week_losses", ">=", 2),
    ],
    attr_effects=[
        AttrEffect("morale", (-10, -4)),
        AttrEffect("fatigue", (3, 6)),
    ],
    cooldown_weeks=2,
    narratives=[
        """不是你的问题，但也不只是队友的问题。

大比分落后的时候，整支队的运转就开始慢下来了——
传球变迟，出手变硬，站位变散。
你在场上能感觉到这一切，却找不到扭转的方式。

赛后教练开了个简短的会议。没有人说话。
那种沉默比批评更重。""",

        """终场哨响的时候，你站在三分线外面，
看着对面球员在互相击掌。

差距那么大，你说不出任何借口。
回到更衣室，你换衣服、冲澡、离开，一句话也没说。
有时候这一晚上最好的处理方式就是结束它。""",
    ],
))

register(EventDefinition(
    key="perf.defensive_lockdown",
    category="game_performance",
    title="防守统治",
    severity="normal",
    base_prob=0.07,
    conditions=[
        Condition("perimeter_def", ">=", 60),
        Condition("week_wins", ">=", 2),
    ],
    attr_effects=[
        AttrEffect("morale", (4, 8)),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=4,
    narratives=[
        """这一周你盯住了对方最难缠的得分手。

不是压制，是完全封锁——对方每一次持球你都跟上来了，
每一次出手都有你的手在旁边。

数据上你的得分不是最好看的，但教练赛后专门提到了你的防守。
有些事情记录在数字里，有些不在。""",

        """你记得这周每一个对位球员的习惯动作。

左手持球倾向右切的那个，喜欢在高位接球后后撤步的那个——
你在训练视频里记住了他们，今晚你把那些东西都用上了。

对方的进攻在你面前转了好几圈，没有找到缝隙。
这种感觉，比投进一个压哨球更让你满足。""",
    ],
))

register(EventDefinition(
    key="perf.comeback_lead",
    category="game_performance",
    title="带队逆转",
    severity="major",
    base_prob=0.05,
    conditions=[
        Condition("leadership", ">=", 55),
        Condition("week_wins", ">=", 1),
        Condition("clutch_factor", ">=", 50),
    ],
    attr_effects=[
        AttrEffect("morale", (8, 15)),
        AttrEffect("leadership", 2),
        AttrEffect("clutch_factor", 1),
    ],
    cooldown_weeks=5,
    narratives=[
        """第三节结束时，你落后了 19 分。

更衣室里有人低着头，有人在揉膝盖，没人说话。
你站起来，没有发表演讲，只是说了一句话。
你说：还没结束。

你率先打出一波进攻，然后是第二波、第三波。
最终你拿下比赛的时候，比赛里最吵的一刻，也是你最安静的一刻。""",

        """下半场开始，你做了一个决定：不管别人，自己先动起来。

你要到球，强攻了一个，进了。
下一回合，你组织了一次快攻，传球，又进了。
队伍的节奏跟着你动了起来。

最后胜利降临的时候，你知道这不是运气，
是你在那个时刻做出了选择。""",
    ],
))

register(EventDefinition(
    key="perf.overtime_grind",
    category="game_performance",
    title="加时苦战",
    severity="minor",
    base_prob=0.06,
    conditions=[
        Condition("week_wins", ">=", 1),
    ],
    attr_effects=[
        AttrEffect("fatigue", (8, 15)),
        AttrEffect("morale", (2, 6)),
        AttrEffect("endurance", 1),
    ],
    cooldown_weeks=3,
    narratives=[
        """加时赛的 5 分钟比整场常规时间都累。

你的腿早就发沉了，但你没有出场。
最后 2 分钟，你靠着意志力完成了两次关键出手。

赢下来的那一刻，你在场上蹲了下去，深呼了口气。
疲惫和快乐同时在身体里存在，你没法分清哪个多一点。""",

        """正常时间末尾，你认为自己已经尽力了。

然后加时开始了，你不得不再找出一点什么来。
运动员都知道这种感觉：你以为已经空了，
但只要比赛还在，就还能挤出更多。

最终你们赢了。你在更衣室里坐下来，然后就那么坐着，很久没动。""",
    ],
))

register(EventDefinition(
    key="perf.rookie_growing_pains",
    category="game_performance",
    title="新秀的困境",
    severity="minor",
    base_prob=0.15,
    conditions=[
        Condition("career_year", "<=", 2),
        Condition("overall_rating", "<=", 70),
    ],
    attr_effects=[
        AttrEffect("morale", (-6, -2)),
        AttrEffect("basketball_iq", 1),
    ],
    cooldown_weeks=3,
    narratives=[
        """联盟的速度比你预期的快。

你知道自己在大学打得好，但大学里的防守人和这里的不是一回事。
这一周你明显感觉到了差距——不是技术上的，是那种对局势的阅读，
那种老球员才有的预判。

你把这些记在心里。你知道这些东西只能靠时间来填。""",

        """你有时候会觉得比赛太快了。

决策的窗口很窄，稍一犹豫，机会就过去了。
老将们在场上的样子让你明白，那种从容是练出来的，不是天生的。

你今晚打得不够好。但你知道原因在哪里，这已经是一种进步。""",
    ],
))

register(EventDefinition(
    key="perf.veteran_wisdom",
    category="game_performance",
    title="老兵的火焰",
    severity="normal",
    base_prob=0.08,
    conditions=[
        Condition("career_year", ">=", 10),
        Condition("week_avg_pts", ">=", 20),
    ],
    attr_effects=[
        AttrEffect("morale", (5, 12)),
        AttrEffect("leadership", 1),
        AttrEffect("basketball_iq", 1),
    ],
    cooldown_weeks=4,
    narratives=[
        """他们以为你已经老了。

你在场上就一直想着这件事，然后你把它变成了燃料。
这一周你打出了让人想起你年轻时候的比赛——不是靠身体，
是靠那些年积累下来的东西：判断、节奏、和对时机的感知。

赛后有年轻球员过来和你说话，眼神里有一种认真。""",

        """年龄在改变你打球的方式，但没有改变你赢球的方法。

你不再能飞起来扣篮，但你知道什么时候该传球、
什么角度的出手成功率最高、对方在哪个时刻会松懈。

这一周你用这些东西赢了球，赢得很漂亮。""",
    ],
))

register(EventDefinition(
    key="perf.first_career_game",
    category="game_performance",
    title="职业首秀",
    severity="legendary",
    base_prob=1.0,
    conditions=[
        Condition("career_year", "==", 1),
        Condition("week_number", "==", 1),
    ],
    one_time=True,
    attr_effects=[
        AttrEffect("morale", 15),
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
