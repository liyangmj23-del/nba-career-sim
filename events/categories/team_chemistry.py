"""
球队化学值类事件：9个。
由球队连胜/连败、交易、球员关系触发。
"""
from events.event_registry import EventDefinition, Condition, AttrEffect, register

register(EventDefinition(
    key="team.locker_room_conflict",
    category="team_chemistry",
    title="更衣室风波",
    severity="major",
    base_prob=0.04,
    conditions=[
        Condition("team_loss_streak", ">=", 4),
        Condition("morale", "<=", 60),
    ],
    attr_effects=[
        AttrEffect("morale", (-15, -8)),
        AttrEffect("leadership", -1),
        AttrEffect("media_handling", (-5, -2)),
    ],
    cooldown_weeks=10,
    chains_to=["team.conflict_resolved"],
    chain_delay=3,
    narratives=[
        """事情在一次训练后爆发了。

起因很小，但那只是一个出口——
那些积压的东西找到了一个缝隙，一下子都涌了出来。
大家都说了一些不该说的话。

你事后坐在自己的位置上，听着更衣室里慢慢恢复的安静，
感觉到了一种沉重。不是因为那些话，是因为它反映出来的东西。""",

        """赛后更衣室里，有两个人对视的眼神不对。

你看见了，教练也看见了。
在所有人都离开之后，你留下来，
试着和其中一个人谈了一会儿。

那次谈话没有解决什么，但你知道这件事不能放着不管。
球队的化学值从来不是自动存在的，它需要有人去维护。""",
    ],
))

register(EventDefinition(
    key="team.conflict_resolved",
    category="team_chemistry",
    title="风波平息",
    severity="normal",
    base_prob=1.0,
    conditions=[],
    attr_effects=[
        AttrEffect("morale", (6, 12)),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=99,
    narratives=[
        """那件事最终过去了。

没有戏剧性的和解——只是两个人在训练时击了个掌，
然后一起在场上打了一次不错的配合。

有时候事情就是这样收场的，不是通过一场对话，
是通过一次出手，一次传球，一次共同赢下来的比赛。""",

        """大家开会了，把事情说清楚了。

话说完之后，室内有一段时间的沉默。
然后有人说：那我们明天好好训练吧。
所有人都笑了，不是大笑，是那种松了口气的笑。

第二天训练，气氛比一周前好了很多。""",
    ],
))

register(EventDefinition(
    key="team.winning_streak",
    category="team_chemistry",
    title="球队连胜",
    severity="normal",
    base_prob=0.10,
    conditions=[
        Condition("team_win_streak", ">=", 5),
    ],
    attr_effects=[
        AttrEffect("morale", (8, 15)),
        AttrEffect("clutch_factor", 1),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=6,
    narratives=[
        """连胜进行到一定数量之后，更衣室里有一种特别的东西。

很难描述——不是骄傲，是一种信任。
你传球给队友，知道他会在那里；他出手，你知道他会进。

这种感觉平时很难得，你试着记住它，
告诉自己在困难的时候想起现在。""",

        """你们已经连赢很多场了，媒体开始频繁出现在训练馆门口。

队内的气氛很好，大家开始有点放松——但不是松懈，是那种真正建立在信任上的轻松。
你在某次暂停里看了看队友们的脸，都是一种平静的专注。

这支球队正在找到什么东西。""",
    ],
))

register(EventDefinition(
    key="team.star_injured",
    category="team_chemistry",
    title="核心队友倒下",
    severity="major",
    base_prob=0.05,
    conditions=[
        Condition("career_year", ">=", 2),
    ],
    attr_effects=[
        AttrEffect("morale", (-10, -5)),
        AttrEffect("usage_rate", 5),
        AttrEffect("basketball_iq", 2),
        AttrEffect("leadership", 2),
    ],
    cooldown_weeks=8,
    narratives=[
        """他受伤被架出去的时候，全场都安静了。

你在场上，离他很近，看见了他当时的表情。
你没有说话，只是低下头，等着医疗人员处理。

更衣室里，教练说：球要一样打，只是现在需要更多人站出来。
他说这话的时候，有意无意地看了你一眼。
你知道这意味着什么。""",

        """他受伤的消息发出来之后，球迷们很崩溃，媒体开始写各种预测。

你把手机放下来，专心应对接下来的训练。
有些事情你无法改变，但你能控制的是你自己。

你开始主动要更多球，做更多的组织，
试着填补他留下的空间——哪怕永远无法完全填上。""",
    ],
))

register(EventDefinition(
    key="team.trade_shock",
    category="team_chemistry",
    title="你被交易了",
    severity="legendary",
    base_prob=0.035,
    conditions=[
        Condition("career_year", ">=", 2),
        Condition("morale", "<=", 65),
    ],
    attr_effects=[
        AttrEffect("morale", (-25, -15)),
        AttrEffect("fatigue", (10, 18)),
        AttrEffect("media_handling", (-5, -3)),
    ],
    cooldown_weeks=20,
    chains_to=["team.new_city_adjustment"],
    chain_delay=2,
    narratives=[
        """你在宾馆房间里，下午刚打完一场比赛，准备睡一觉。

经纪人的电话进来了，你以为是例行的事情，
然后他告诉了你。

你说：确定了？
他说：确定了，明天要报到。

你挂掉电话，坐在床上，不知道该做什么。
你不得不重新打包行李，离开这座你住了几年的城市，
去一个你几乎没有去过的地方，重新开始。""",

        """你是从社交媒体上知道这件事的。

先是传言，然后是官方声明——你的名字出现在了交易细节里。
你还没来得及联系经纪人，队友的消息就已经进来了。

有人发来："保重。"
有人发来表情包。
有人什么都没有说，你知道他不知道说什么。

你回复完所有人，然后开始收拾东西。""",
    ],
))

register(EventDefinition(
    key="team.new_city_adjustment",
    category="team_chemistry",
    title="适应新环境",
    severity="normal",
    base_prob=1.0,
    conditions=[],
    attr_effects=[
        AttrEffect("morale", (5, 12)),
        AttrEffect("basketball_iq", 1),
        AttrEffect("leadership", 1),
    ],
    cooldown_weeks=99,
    narratives=[
        """新队友叫你去吃了一顿饭，带你去了他们常去的地方。

你坐在那里，听他们聊，插了几句，慢慢地有点放松了。

每座城市都有它的节奏，每支球队都有它的规则。
你在心里告诉自己：给自己三个月，你会找到这里的节奏的。""",

        """新球馆和你之前待过的地方不太一样。

灯光的角度不同，观众的喧嚣方式不同，更衣室的布局不同。
但篮筐的高度是一样的，球是一样的，你出手的方式是一样的。

你在这里第一次打了一场好球之后，感觉到了一种微弱的熟悉感。
这就够了，可以慢慢来。""",
    ],
))

register(EventDefinition(
    key="team.coach_system_clash",
    category="team_chemistry",
    title="战术体系冲突",
    severity="normal",
    base_prob=0.05,
    conditions=[
        Condition("basketball_iq", "<=", 65),
        Condition("career_year", "<=", 5),
    ],
    attr_effects=[
        AttrEffect("morale", (-8, -4)),
        AttrEffect("basketball_iq", 2),
    ],
    cooldown_weeks=8,
    narratives=[
        """新教练的体系和你熟悉的东西差别很大。

他要求你做一些你之前不做的事——更多的无球跑动，更少的持球进攻。
你在训练中出错，他叫停，解释，你重来。

你知道他是对的，但"知道"和"做到"是两件事。
这一段时间你比任何时候都更认真地在看战术板。""",

        """他在暂停时把你叫到一边，单独说了几句话。

不是批评——或者说，不全是批评。
他说：你的能力没有问题，我要你用另一种方式把它展示出来。

你听懂了，但你没有完全适应。
这个过程需要时间，教练知道，你也知道。""",
    ],
))

register(EventDefinition(
    key="team.players_only_meeting",
    category="team_chemistry",
    title="球员自发会议",
    severity="normal",
    base_prob=0.04,
    conditions=[
        Condition("team_loss_streak", ">=", 3),
        Condition("leadership", ">=", 55),
    ],
    attr_effects=[
        AttrEffect("morale", (5, 12)),
        AttrEffect("leadership", 2),
        AttrEffect("basketball_iq", 1),
    ],
    cooldown_weeks=8,
    narratives=[
        """训练后，你关上了更衣室的门。

不是命令，只是说：大家都坐下来，说说吧。
然后你先开口，说了你看到的问题，说了你觉得可以改变的地方，
说的时候尽量平静，但也尽量真实。

其他人也开始说了。说了很多，有一些很尖锐，但没有人乱喊。
那一个小时可能比最近三周的训练更重要。""",

        """这不是计划好的。

你们赛后坐在更衣室里，谁都没有动，
然后有人说：我们能不能把话说清楚？

于是就说了。
说了很久，说了一些平时不会说的东西。
灯光慢慢变暗，你们还在里面。

出来的时候，你感觉轻了，也沉了——
因为你知道说出来就意味着得去做到。""",
    ],
))

register(EventDefinition(
    key="team.title_window",
    category="team_chemistry",
    title="冠军窗口期",
    severity="major",
    base_prob=0.06,
    monthly_only=True,
    conditions=[
        Condition("team_win_streak", ">=", 3),
        Condition("overall_rating", ">=", 70),
        Condition("career_year", ">=", 4),
    ],
    attr_effects=[
        AttrEffect("morale", (8, 15)),
        AttrEffect("clutch_factor", 3),
        AttrEffect("leadership", 2),
    ],
    cooldown_weeks=15,
    narratives=[
        """整座城市都在谈论这个赛季。

你能感受到一种氛围的改变——从希望变成了期待，从期待变成了一种笃定。
更衣室里的状态是你进联盟以来见过最好的，所有人都知道这个窗口有多短暂。

你比任何时候都认真地对待每一次训练、每一场比赛。
你知道这种状态不会永远持续，所以你用这种紧迫感推着自己向前。""",

        """外部的声音开始增多了，有人说你们能走多远，有人说你们不行。

你选择了不去看那些东西。
你只知道：现在这支球队有机会做成一件大事，
而这样的机会一生里不会太多。

你把所有的注意力都放在了手头的事情上。""",
    ],
))
