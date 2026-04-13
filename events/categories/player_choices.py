"""
玩家主动选择事件。
设计原则：每 2-4 周必然触发至少一个，覆盖整个职业生涯各阶段。
影响范围：week（几场）/ month（月）/ season（赛季）/ career（生涯）
"""
from events.event_registry import (
    EventDefinition, Condition, AttrEffect, ChoiceOption, register
)

# ══════════════════════════════════════════════════════════════════════════════
# ── 高频触发（无条件/低门槛）每隔几周必出现 ──────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

register(EventDefinition(
    key="choice.training_intensity",
    category="game_performance",
    title="本周训练强度",
    severity="normal",
    base_prob=0.35,
    cooldown_weeks=3,
    conditions=[],
    narratives=[
        """训练师走过来，把今天的计划表递给你。

上面有两套方案：一套是高强度对抗训练，消耗大但进步快；
另一套是技术细节打磨，更轻松，但积累是慢慢来的。

你手里拿着表，看了看这周的赛程，思考了一下。""",

        """赛季进行到这里，你感觉身体有点沉。

教练问你：今天想怎么练？
这个选择权在你，他尊重你的判断。""",
    ],
    choice_prompt="你今天选择怎么训练？",
    choices=[
        ChoiceOption(
            key="hard",
            label="高强度对抗，拼一把",
            description="得分/防守属性 +2~4，但疲劳大幅增加，受伤风险上升",
            impact_scope="week",
            attr_effects=[
                AttrEffect("shooting_2pt", (1, 3)),
                AttrEffect("perimeter_def", (1, 2)),
                AttrEffect("fatigue", (12, 20)),
                AttrEffect("endurance", 1),
            ],
            narrative="""你选了对抗。

整整两小时，你一遍又一遍地完成那些你不喜欢做的动作。
训练结束，你浑身酸痛，但那种充实感是真实的。
你知道这些会留下来。""",
        ),
        ChoiceOption(
            key="technical",
            label="技术打磨，细水长流",
            description="篮球IQ和传球 +1~3，疲劳少，状态更稳定",
            impact_scope="month",
            attr_effects=[
                AttrEffect("basketball_iq", (1, 3)),
                AttrEffect("passing", (1, 2)),
                AttrEffect("fatigue", (3, 8)),
            ],
            narrative="""你选了技术课。

你花了一个小时反复练一个出手角度，教练在旁边不断调整你的手型。
枯燥，但你感觉到了细微的变化——
那种"对了"的感觉，只有反复练过之后才会有。""",
        ),
        ChoiceOption(
            key="rest",
            label="今天适当休息，保持状态",
            description="恢复体力和士气，短期无属性提升，但状态更好",
            impact_scope="week",
            attr_effects=[
                AttrEffect("fatigue", (-18, -10)),
                AttrEffect("health", (3, 8)),
                AttrEffect("morale", (3, 8)),
            ],
            narrative="""你告诉训练师：今天轻练。

他点点头，没有多说什么。
你做了些拉伸，投了一会儿篮，然后早早收工。
回到宿舍，你睡了一个很好的午觉。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.pregame_focus",
    category="game_performance",
    title="赛前状态调整",
    severity="normal",
    base_prob=0.30,
    cooldown_weeks=2,
    conditions=[],
    narratives=[
        """今晚是一场重要的比赛。

热身结束，距离开球还有二十分钟，你坐在更衣室里。
队友们各自准备，有人在听音乐，有人在看手机，有人在和队友说话。

你想着今晚怎么找到最好的状态。""",

        """上午你就感觉今晚这场不一般。

不是最难的对手，但就是有那种说不清楚的感觉——
这场必须打好。

赛前你在想用什么方式进入状态。""",
    ],
    choice_prompt="你用什么方式准备这场比赛？",
    choices=[
        ChoiceOption(
            key="film",
            label="看录像研究对手",
            description="篮球IQ临时提升，更好地阅读比赛",
            impact_scope="week",
            attr_effects=[
                AttrEffect("basketball_iq", (1, 3)),
                AttrEffect("clutch_factor", 1),
            ],
            narrative="""你打开平板，把对方主要球员的剪辑看了一遍。

他们的防守站位，他们惯用的进攻套路，他们在压力下的习惯动作——
你都记下来了。

开球哨响的时候，你感觉比平时多了几分把握。""",
        ),
        ChoiceOption(
            key="warmup",
            label="充分热身，找手感",
            description="得分和命中率临时提升",
            impact_scope="week",
            attr_effects=[
                AttrEffect("shooting_2pt", (1, 3)),
                AttrEffect("shooting_3pt", (1, 2)),
                AttrEffect("fatigue", (3, 6)),
            ],
            narrative="""你提前二十分钟上场，把每个出手位置都走了一遍。

中距离、三分、罚球线——
你一遍一遍地投，直到那种手感完全回来。

进入比赛的时候，你的手是热的。""",
        ),
        ChoiceOption(
            key="mental",
            label="冥想放松，保持冷静",
            description="士气和关键时刻属性提升，全场更稳定",
            impact_scope="week",
            attr_effects=[
                AttrEffect("morale", (5, 10)),
                AttrEffect("clutch_factor", (2, 4)),
            ],
            narrative="""你戴上耳机，闭上眼睛，什么都不想。

让脑子空了十分钟。

开球的时候，你比平时更安静，但那种安静是实的，不是空的。
你知道今晚你能找到自己的节奏。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.media_interview",
    category="off_court",
    title="赛后采访",
    severity="minor",
    base_prob=0.25,
    cooldown_weeks=3,
    conditions=[],
    narratives=[
        """赛后走廊里，几个记者等着你。

你今天打得不错，或者不那么好——不管哪种，他们都想要一个说法。

你看了看手表，想了想该怎么处理这几分钟。""",

        """混合采访区，摄像机已经架好了。

你换好衣服走出来，主持人递过来麦克风，
问了今天比赛的问题。

你脑子里快速想了一下该怎么回答。""",
    ],
    choice_prompt="你怎么应对这次采访？",
    choices=[
        ChoiceOption(
            key="honest",
            label="直接说真实想法",
            description="媒体应对能力成长，但有时会引发话题",
            impact_scope="month",
            attr_effects=[
                AttrEffect("media_handling", (2, 5)),
                AttrEffect("leadership", 1),
                AttrEffect("morale", (2, 5)),
            ],
            narrative="""你没有用套话，直接说了你觉得真实的东西。

记者们在记，有几个人抬起头看了你一眼——
不是每个球员都会这样说话的。

你走出去的时候感觉比平时轻松一点。""",
        ),
        ChoiceOption(
            key="professional",
            label="标准职业回答，不多说",
            description="稳妥，媒体应对缓慢成长",
            impact_scope="week",
            attr_effects=[
                AttrEffect("media_handling", (1, 2)),
            ],
            narrative="""你说了几句场面话，感谢队友，感谢教练，专注下一场。

记者们记完收摊，你也走了。

没什么特别的，但也没出什么问题。""",
        ),
        ChoiceOption(
            key="brief",
            label="简短结束，回去休息",
            description="节省精力，士气小幅回升",
            impact_scope="week",
            attr_effects=[
                AttrEffect("fatigue", (-5, -3)),
                AttrEffect("morale", (2, 4)),
            ],
            narrative="""你礼貌地说了两句就结束了。

记者们也没有追着问，你往更衣室方向走，
脑子里想的已经是明天的训练了。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.teammate_conflict",
    category="team_chemistry",
    title="和队友起了摩擦",
    severity="normal",
    base_prob=0.18,
    cooldown_weeks=5,
    conditions=[],
    narratives=[
        """训练结束后，你和一个队友发生了一点小摩擦。

起因很小——一次传球没到位，然后说了几句话，气氛就变了。
现在你们各自站在更衣室的两侧，没有人先开口。""",

        """比赛里有一次你没有传球，自己强行出手了。

你进了，但对方队友明明空着——他事后没说什么，
但你能感觉到他不高兴。

现在训练结束，你们站在停车场，各自要走。""",
    ],
    choice_prompt="你选择怎么处理？",
    choices=[
        ChoiceOption(
            key="apologize",
            label="主动道歉，化解矛盾",
            description="领导力和团队化学值提升，短期士气小降",
            impact_scope="month",
            attr_effects=[
                AttrEffect("leadership", (2, 4)),
                AttrEffect("morale", (-3, 5)),
                AttrEffect("basketball_iq", 1),
            ],
            narrative="""你走过去，说：刚才那个我处理得不好。

他愣了一下，然后点点头，说：没事了。

你们没有再多说，但那个节点就这样过去了。
更衣室里的气氛明天会好一点。""",
        ),
        ChoiceOption(
            key="ignore",
            label="各走各的，时间会处理",
            description="短期无影响，问题可能积累",
            impact_scope="season",
            attr_effects=[
                AttrEffect("fatigue", (-3, 0)),
            ],
            narrative="""你把包背起来，往外走。

有些事情不需要当场解决，时间会冲淡的。
至少你是这么告诉自己的。""",
        ),
        ChoiceOption(
            key="talk",
            label="坐下来把话说清楚",
            description="关系真正修复，领导力大幅提升，需要消耗精力",
            impact_scope="career",
            attr_effects=[
                AttrEffect("leadership", (3, 6)),
                AttrEffect("morale", (3, 8)),
                AttrEffect("fatigue", (5, 10)),
            ],
            narrative="""你说：能不能找个地方聊一下？

你们在停车场旁边坐了半小时。
说了一些平时不会说的东西，有点别扭，但说完轻松了很多。

出来的时候，你们一起笑了几句，气消了。""",
        ),
    ],
))

# ══════════════════════════════════════════════════════════════════════════════
# ── 中频触发（有一定条件，但门槛不高）────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

register(EventDefinition(
    key="choice.play_through_pain",
    category="injury",
    title="带伤坚持还是退出",
    severity="major",
    base_prob=0.12,
    cooldown_weeks=6,
    conditions=[
        Condition("health", "<=", 88),   # 只要体力不满就可能触发
    ],
    narratives=[
        """训练师把你叫到一边，声音放低：

"你的状态我知道。正常来说，今晚不该上。
但这场比赛你自己也清楚意味着什么。"

他把最终选择权还给了你。""",

        """上场前，你蹲下来系鞋带，感觉到了那个地方还是有一点。

不是很痛，但在那里。
你站起来，队友们已经在热身了。

教练看了你一眼，没有说话。""",
    ],
    choice_prompt="你会怎么做？",
    choices=[
        ChoiceOption(
            key="play",
            label="上场，这场必须打",
            description="士气和关键时刻提升，但体力进一步损耗",
            impact_scope="month",
            attr_effects=[
                AttrEffect("morale",       (5, 12)),
                AttrEffect("clutch_factor", 2),
                AttrEffect("health",       (-15, -5)),
                AttrEffect("fatigue",      (8, 15)),
            ],
            narrative="""你说：我上。

那个地方整场都在，但你没有让它出来。
比赛结束你在场上蹲了下去，深呼了口气。

你不知道这个决定是对是错，但你在那一刻是确定的。""",
        ),
        ChoiceOption(
            key="rest",
            label="听医疗团队的，坐下来",
            description="体力和疲劳大幅恢复，长期更健康",
            impact_scope="week",
            attr_effects=[
                AttrEffect("health",   (10, 20)),
                AttrEffect("fatigue",  (-20, -10)),
                AttrEffect("morale",   (-5, 2)),
            ],
            narrative="""你点点头：好。

你坐上替补席，看着队友打。
你是理智的，你知道这是对的选择。
但看着比赛的每一分钟，你都在想自己在场上会怎么处理那个球。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.coach_talk",
    category="team_chemistry",
    title="教练找你谈话",
    severity="normal",
    base_prob=0.15,
    cooldown_weeks=6,
    conditions=[],
    narratives=[
        """训练结束后，教练让你留下来。

你在他办公室坐下，他关上了门。
他说有些事情想和你聊聊——关于你的角色，关于球队的方向。

你感觉到这次谈话的分量。""",

        """教练发消息让你明天早点到。

"单独谈一下，没有其他人。"

你不知道是好事还是坏事，睡前想了一会儿，
第二天准时推开了他办公室的门。""",
    ],
    choice_prompt="面对教练，你选择怎么表达？",
    choices=[
        ChoiceOption(
            key="open",
            label="坦诚说出你的想法",
            description="领导力和篮球IQ提升，和教练建立更深信任",
            impact_scope="season",
            attr_effects=[
                AttrEffect("leadership",    (2, 5)),
                AttrEffect("basketball_iq", (1, 3)),
                AttrEffect("morale",        (4, 10)),
            ],
            narrative="""你没有只说"好的教练"。

你说了你真实的想法：哪里觉得打得不顺，哪里觉得可以更好。
他认真地听，中间打断了两次，问了很具体的问题。

谈完出来，你感觉这支球队里多了一根线。""",
        ),
        ChoiceOption(
            key="listen",
            label="先听他说，保留意见",
            description="稳妥，篮球IQ小幅提升",
            impact_scope="month",
            attr_effects=[
                AttrEffect("basketball_iq", (1, 2)),
                AttrEffect("morale",        (2, 5)),
            ],
            narrative="""你坐在那里，认真地听他说完。

有些你同意，有些你不完全同意，但你没有打断他。
出来的时候你把这些都记下来，慢慢消化。""",
        ),
        ChoiceOption(
            key="ask",
            label="主动问他对你的评价",
            description="直接了解教练的真实看法，可能好可能坏",
            impact_scope="season",
            attr_effects=[
                AttrEffect("basketball_iq", (2, 4)),
                AttrEffect("morale",        (-5, 12)),
                AttrEffect("leadership",    (1, 3)),
            ],
            narrative="""等他说完，你直接问：你觉得我现在打得怎么样？

他停了一下，然后告诉了你他真实的看法。
那些话有些不好听，但每一句都是真的。

你出来的时候心情复杂，但脑子里多了几件以前没想清楚的事。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.extra_practice",
    category="game_performance",
    title="休息日加练的诱惑",
    severity="normal",
    base_prob=0.20,
    cooldown_weeks=4,
    conditions=[],
    narratives=[
        """今天是休息日，训练馆不强制要求到场。

但你已经在停车场了。
你想了想最近几场的状态，想了想还有哪些东西没练到位。

门是开的，里面有几个队友在自主练习。""",

        """赛季到这个阶段，身体其实需要休息。

但你脑子里一直有个声音——
那个出手的角度，那个防守脚步，还需要再练。

你站在家门口，想了想。""",
    ],
    choice_prompt="你怎么度过这个休息日？",
    choices=[
        ChoiceOption(
            key="practice",
            label="去加练，哪怕一小时",
            description="技术属性提升，但疲劳增加",
            impact_scope="month",
            attr_effects=[
                AttrEffect("shooting_3pt",  (1, 3)),
                AttrEffect("ball_handling", (1, 2)),
                AttrEffect("work_ethic",    1),
                AttrEffect("fatigue",       (6, 12)),
            ],
            narrative="""你推开训练馆的门。

里面确实有几个人，你们互相点点头，各练各的。
一个小时后你离开，腿又沉了，但那种踏实感是真的。""",
        ),
        ChoiceOption(
            key="rest",
            label="好好休息，身体优先",
            description="体力和士气大幅恢复",
            impact_scope="week",
            attr_effects=[
                AttrEffect("health",  (5, 12)),
                AttrEffect("fatigue", (-20, -12)),
                AttrEffect("morale",  (5, 10)),
            ],
            narrative="""你把车开走了。

你回家，睡了一个长觉，下午看了一场别的比赛。
什么都没有练，但第二天你感觉腿轻了很多。
有时候休息就是训练。""",
        ),
        ChoiceOption(
            key="film",
            label="在家看录像，脑子练",
            description="篮球IQ显著提升，身体得到休息",
            impact_scope="season",
            attr_effects=[
                AttrEffect("basketball_iq", (2, 5)),
                AttrEffect("health",        (3, 8)),
                AttrEffect("fatigue",       (-8, -3)),
            ],
            narrative="""你坐在沙发上打开了比赛录像。

不是今天的，是两周前的，你觉得自己处理得不好的那场。
你看了三遍，把每一个决策都想了一遍。

没有流汗，但脑子里多了一些东西。""",
        ),
    ],
))

# ══════════════════════════════════════════════════════════════════════════════
# ── 低频/特殊场景（条件有一定要求）──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

register(EventDefinition(
    key="choice.locker_room_approach",
    category="team_chemistry",
    title="更衣室风波——你的应对",
    severity="major",
    base_prob=0.12,
    cooldown_weeks=10,
    conditions=[
        Condition("team_loss_streak", ">=", 2),  # 降低：连败2就触发
    ],
    narratives=[
        """连续输球之后，更衣室里有了一种不对劲的气氛。

没有人直接说什么，但那种紧绷就在那里。
你感觉到了，其他人也感觉到了。

今天训练结束，大家都没有急着走。""",
    ],
    choice_prompt="你决定怎么处理这场风波？",
    choices=[
        ChoiceOption(
            key="talk",
            label="主动沟通，把话说开",
            description="短期关系受损但长期凝聚力提升，领导力大幅成长",
            impact_scope="season",
            attr_effects=[
                AttrEffect("morale",    (-5, 5)),
                AttrEffect("leadership", 4),
                AttrEffect("basketball_iq", 1),
            ],
            narrative="""你站出来，关上了门。

你说：大家都坐下来，把话说清楚。
刚开始很沉默，然后有人开了口。

两个小时后，所有人走出去。没有完全解决，但都在同一边了。""",
        ),
        ChoiceOption(
            key="silence",
            label="保持沉默，让时间处理",
            description="不激化矛盾，但问题可能下赛季爆发",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale", (-3, 2)),
            ],
            narrative="""你换好衣服，走出去，一句话没说。

裂缝没有消失，只是被压在了下面。""",
        ),
        ChoiceOption(
            key="confront",
            label="强硬表态，要求改变",
            description="立刻见效但风险高，结果不确定",
            impact_scope="month",
            attr_effects=[
                AttrEffect("morale",    (-5, 10)),
                AttrEffect("leadership", (1, 5)),
                AttrEffect("media_handling", (-3, -1)),
            ],
            narrative="""你说了几句话，没有废话，直接说到了问题的核心。

一半人觉得你说得对，另一半觉得你越线了。
接下来会怎样，取决于场上的结果。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.trade_decision",
    category="team_chemistry",
    title="交易——你的选择",
    severity="legendary",
    base_prob=0.06,
    cooldown_weeks=15,
    one_time=False,
    conditions=[
        Condition("career_year", ">=", 2),  # 降低：2年就可能
    ],
    narratives=[
        """电话是深夜打来的。

经纪人的声音很平静，但你听出了里面的分量：
有球队想要你，而你的球队已经同意了交易框架。

你还有一个窗口说话。""",
    ],
    choice_prompt="你会怎么应对这笔交易？",
    choices=[
        ChoiceOption(
            key="accept",
            label="接受，拥抱新的开始",
            description="可能带来冠军机会，但要重新建立一切",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale",    (-10, 5)),
                AttrEffect("basketball_iq", 2),
            ],
            chains_to="team.new_city_adjustment",
            narrative="""你告诉经纪人：告诉他们我愿意。

然后开始想行李怎么打包。""",
        ),
        ChoiceOption(
            key="refuse",
            label="拒绝，留在这里",
            description="管理层可能有看法，但也可能赢得尊重",
            impact_scope="season",
            attr_effects=[
                AttrEffect("morale",    (5, 15)),
                AttrEffect("leadership", 2),
            ],
            narrative="""你说：我想留下来。

第二天训练馆里有些眼神，但你做了你认为对的事。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.contract_direction",
    category="career_milestones",
    title="续约谈判——你的优先级",
    severity="legendary",
    base_prob=0.85,          # 合同年高概率触发（career_year % 4 == 0 时）
    one_time=False,
    cooldown_weeks=48,       # ~4个赛季冷却，防止反复出现
    conditions=[
        Condition("career_year", ">=", 4),   # 至少打过4年才有续约资格
    ],
    monthly_only=True,       # 只在第4/8/12/...周触发（避免赛季初打断节奏）
    narratives=[
        """谈判桌上摆着几个方向。

你和经纪人需要先搞清楚：你最想要什么。
是最多的钱，最好的机会，还是某种稳定？""",
    ],
    choice_prompt="你的续约优先级是什么？",
    choices=[
        ChoiceOption(
            key="money",
            label="拿最大合同，顶薪优先",
            description="财务最优，但球队阵容建设受限",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale",   (5, 10)),
                AttrEffect("work_ethic", -1),
            ],
            narrative="""你告诉经纪人：拿最好的数字。

你值这个钱，但阵容会更薄，你需要扛更多。""",
        ),
        ChoiceOption(
            key="winning",
            label="接受折扣，让球队有资源",
            description="降薪但球队有更多资源，历史地位可能更高",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale",    (-3, 5)),
                AttrEffect("leadership", 3),
                AttrEffect("clutch_factor", 2),
            ],
            narrative="""你说：少给我一点，把那部分钱用在球队上。

有人说你懂球，有人说你被坑了。
你不在乎哪个。""",
        ),
        ChoiceOption(
            key="loyalty",
            label="短约，保留灵活性",
            description="2-3年短约，可以再次选择去向",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale",   (2, 8)),
            ],
            narrative="""你要了一份短合同。

你获得了主动权——在这个联盟里，主动权很稀缺。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.free_agency",
    category="career_milestones",
    title="自由身——去哪里",
    severity="legendary",
    base_prob=0.0,
    one_time=False,
    cooldown_weeks=52,
    conditions=[
        Condition("career_year", ">=", 3),
    ],
    narratives=[
        """你是自由球员了。

三个方向摆在桌上：老东家、冠军热门、重建球队。
你有七十二小时。""",
    ],
    choice_prompt="你会去哪里？",
    choices=[
        ChoiceOption(
            key="stay",
            label="留在老东家",
            description="稳定忠诚，但天花板可能已清晰",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale",    (8, 15)),
                AttrEffect("leadership", 2),
            ],
            narrative="""你打给老东家的GM：我回来。

媒体把这个叫做忠诚。""",
        ),
        ChoiceOption(
            key="contender",
            label="去冠军热门",
            description="降薪可能，角色变化，但离冠军最近",
            impact_scope="career",
            attr_effects=[
                AttrEffect("morale",        (3, 10)),
                AttrEffect("clutch_factor",  3),
                AttrEffect("leadership",    -2),
            ],
            narrative="""你选了那条最快通往冠军的路。

外界的声音很多，你不去看。""",
        ),
        ChoiceOption(
            key="rebuild",
            label="去重建球队做核心",
            description="最重压力，但成功则历史地位极高",
            impact_scope="career",
            attr_effects=[
                AttrEffect("leadership",  5),
                AttrEffect("work_ethic",  3),
                AttrEffect("clutch_factor", 3),
            ],
            narrative="""你选了那支在重建的球队。

你走进新训练馆，站在空荡荡的球场中间。
这里的一切需要从零建立。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.mentor_decision",
    category="personal_life",
    title="年轻球员需要你",
    severity="normal",
    base_prob=0.12,
    monthly_only=True,
    cooldown_weeks=8,
    conditions=[
        Condition("career_year", ">=", 3),  # 降低：3年就有资格带人
    ],
    narratives=[
        """那个年轻球员在你更衣室隔壁坐着，
练球练到很晚，但你能看出来他遇到了什么事。

他抬起头，你们对上了眼神。""",
    ],
    choice_prompt="你怎么对待这个年轻球员？",
    choices=[
        ChoiceOption(
            key="invest",
            label="主动带他，花时间指导",
            description="领导力大幅提升，他可能成为长期盟友",
            impact_scope="career",
            attr_effects=[
                AttrEffect("leadership",    (3, 5)),
                AttrEffect("basketball_iq",  1),
                AttrEffect("morale",        (5, 10)),
                AttrEffect("fatigue",       (3, 8)),
            ],
            narrative="""你坐下来，说：有什么事吗？

他说了一些，你听完，说了一些不多但在点子上的话。""",
        ),
        ChoiceOption(
            key="distance",
            label="保持距离，让他自己摸索",
            description="有时独立解决才会真正成长",
            impact_scope="month",
            attr_effects=[
                AttrEffect("fatigue", (-3, 0)),
            ],
            narrative="""你走出去，没有回头。

有些东西需要自己摸，旁边有人扶着反而学不会。""",
        ),
    ],
))

register(EventDefinition(
    key="choice.system_conflict",
    category="team_chemistry",
    title="战术体系冲突",
    severity="major",
    base_prob=0.10,
    cooldown_weeks=12,
    conditions=[
        Condition("career_year", ">=", 2),  # 降低：2年就可能有自己想法
    ],
    narratives=[
        """新教练的体系和你的风格有根本上的冲突。

训练结束后，他单独留下了你，说：你怎么看这件事？""",
    ],
    choice_prompt="你怎么和教练沟通？",
    choices=[
        ChoiceOption(
            key="adapt",
            label="全面适应，学新东西",
            description="短期效率下降，长期IQ和多面性提升",
            impact_scope="career",
            attr_effects=[
                AttrEffect("basketball_iq", (2, 5)),
                AttrEffect("morale",        (-5, -2)),
                AttrEffect("passing",        1),
            ],
            narrative="""你说：教练，我跟着你走。

接下来你打得很不顺，但你在学一种新的维度。""",
        ),
        ChoiceOption(
            key="negotiate",
            label="私下沟通，找中间地带",
            description="双方妥协，短期最稳定",
            impact_scope="season",
            attr_effects=[
                AttrEffect("basketball_iq", 1),
                AttrEffect("leadership",    2),
                AttrEffect("morale",        (2, 6)),
            ],
            narrative="""你说：教练，我们能不能谈谈？

你们都做了让步，这不是任何一个人完全想要的版本，但可以运作。""",
        ),
        ChoiceOption(
            key="insist",
            label="坚持自己的打法，让数据说话",
            description="高风险高回报：成绩好教练妥协，成绩差关系破裂",
            impact_scope="season",
            attr_effects=[
                AttrEffect("morale",     (-5, 10)),
                AttrEffect("clutch_factor", 2),
            ],
            narrative="""你说：我需要按我的方式打。

他点头：那就让我们看看结果。""",
        ),
    ],
))
