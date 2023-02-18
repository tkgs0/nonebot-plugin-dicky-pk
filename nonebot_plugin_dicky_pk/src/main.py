from .db import DB, lazy_init_database
from .impl import get_at_segment, send_message
from .utils import create_match_func_factory, join, ArrowUtil, fixed_two_decimal_digits
from .config import Config
from .cd import CD_Check
from .rebirth import RebirthSystem
from .badge import BadgeSystem
from .constants import OpFrom, TimeConst, FarmConst
from .farm import FarmSystem
from typing import Optional
from nonebot.adapters.onebot.v11 import Bot


KEYWORDS = {
    "chinchin": ["牛子"],
    "pk": ["pk"],
    "lock_me": ["🔒我", "suo我", "嗦我", "锁我"],
    "lock": ["🔒", "suo", "嗦", "锁"],
    "glue": ["打胶"],
    "see_chinchin": ["看他牛子", "看看牛子"],
    "sign_up": ["注册牛子"],
    "ranking": ["牛子排名", "牛子排行"],
    "rebirth": ["牛子转生"],
    "badge": ["牛子成就"],
    # farm
    "farm": ["牛子仙境"],
    "farm_start": ["牛子修炼", "牛子练功", "牛子修仙"],
}

DEFAULT_NONE_TIME = TimeConst.DEFAULT_NONE_TIME


def message_processor(
    bot: Bot,
    message: str,
    qq: int,
    group: int,
    at_qq: Optional[int] = None,
    nickname: Optional[str] = None,
    fuzzy_match: bool = False,
    impl_at_segment=None,
    impl_send_message=None,
):
    """
    main entry
    TODO: 破解牛子：被破解的 牛子 长度操作 x 100 倍
    TODO：疯狂牛子星期四，牛子长度操作加倍
    TODO: 不同群不同的配置参数
    TODO: 转生级别不同不能较量
    TODO: 牛子最小排行
    TODO：牛子成就额外的提示语
    TODO: 物品系统
    TODO: 抽取 utils 文件的导入

    TODO: 朋友系统
    """
    # lazy init database
    lazy_init_database()

    # message process
    message = message.strip()
    match_func = create_match_func_factory(fuzzy=fuzzy_match)

    # hack at impl
    if impl_at_segment:
        global get_at_segment
        get_at_segment = impl_at_segment

    # 消息上下文，用于追加消息
    msg_ctx = {"before": [get_at_segment(qq)], "after": []}
    # hack send message impl

    def create_send_message_hook(origin_send_message):
        def send_message_hook(bot, qq, group, message):
            before = join(msg_ctx["before"], "\n")
            content = None
            after = join(msg_ctx["after"], "\n")
            # is string
            if isinstance(message, str):
                content = message
            # is list
            elif isinstance(message, list):
                content = join(message, "\n")
            text = join([before, content, after], "\n")
            origin_send_message(bot, qq, group, text)
            msg_ctx["before"].clear()

        return send_message_hook

    global send_message
    if not impl_send_message:
        impl_send_message = send_message
    send_message = create_send_message_hook(impl_send_message)

    # >>> 记录、初始化数据阶段
    # 记录数据 - info
    DB.sub_db_info.record_user_info(
        qq,
        {
            "latest_speech_group": group,
            "latest_speech_nickname": nickname,
        },
    )
    # 初始化数据 - badge
    DB.sub_db_badge.init_user_data(qq)
    # 初始化数据 - farm
    DB.sub_db_farm.init_user_data(qq)

    # flow context
    ctx = {
        "bot": bot,
        "qq": qq,
        "at_qq": at_qq,
        "group": group,
        "msg_ctx": msg_ctx,
    }

    # 注册牛子
    if match_func(KEYWORDS.get("sign_up"), message):
        return Chinchin_me.sign_up(ctx)

    # 下面的逻辑必须有牛子
    if not DB.is_registered(qq):
        not_has_chinchin_msg = None
        if at_qq:
            not_has_chinchin_msg = "对方因为你没有牛子拒绝了你，快去注册一只牛子吧！"
        else:
            not_has_chinchin_msg = "你还没有牛子！"
        message_arr = [
            not_has_chinchin_msg,
        ]
        send_message(bot, qq, group, join(message_arr, "\n"))
        return

    # >>> 检查阶段
    # 检查成就
    badge_msg = BadgeSystem.check_whether_get_new_badge(qq)
    if badge_msg:
        msg_ctx["before"].append(badge_msg)

    # 检查修炼状态
    is_current_planting = Chinchin_farm.check_planting_status(ctx)

    def eager_return():
        # TODO ：急的次数太多获得 “急急国王” 成就
        message_arr = ["你的牛子还在闭关修炼中，无法进行其他操作，我知道你很急，但你先别急"]
        return send_message(bot, qq, group, join(message_arr, "\n"))

    # >>> 匹配阶段
    # 牛子仙境 (search)
    if match_func(KEYWORDS.get("farm"), message):
        return Chinchin_farm.entry_farm_info(ctx)
    # 牛子修炼
    if match_func(KEYWORDS.get("farm_start"), message):
        return Chinchin_farm.entry_farm(ctx)

    # 牛子排名 (search)
    if match_func(KEYWORDS.get("ranking"), message):
        return Chinchin_info.entry_ranking(ctx)

    # 牛子成就 (search)
    if match_func(KEYWORDS.get("badge"), message):
        return Chinchin_badge.entry_badge(ctx)

    # 牛子转生 (opera)
    if match_func(KEYWORDS.get("rebirth"), message):
        # TODO：将 opera 和 search 命令分开
        if is_current_planting:
            return eager_return()
        else:
            return Chinchin_upgrade.entry_rebirth(ctx)

    # 查询牛子信息 (search)
    # FIXME: 注意因为是模糊匹配，所以 “牛子” 的命令要放到所有 "牛子xxx" 命令的最后
    if match_func(KEYWORDS.get("chinchin"), message):
        return Chinchin_info.entry_chinchin(ctx)

    # 牛子修炼：在修炼状态不能进行其他操作
    if is_current_planting:
        return eager_return()

    # 对别人的 (opera)
    if at_qq:
        if not DB.is_registered(at_qq):
            message_arr = ["对方还没有牛子！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return

        # pk别人
        if match_func(KEYWORDS.get("pk"), message):
            return Chinchin_with_target.entry_pk_with_target(ctx)

        # 🔒别人
        if match_func(KEYWORDS.get("lock"), message):
            return Chinchin_with_target.entry_lock_with_target(ctx)

        # 打胶别人
        if match_func(KEYWORDS.get("glue"), message):
            return Chinchin_with_target.entry_glue_with_target(ctx)

        # 看别人的牛子
        if match_func(KEYWORDS.get("see_chinchin"), message):
            return Chinchin_info.entry_see_chinchin(ctx)
    else:
        # 🔒自己
        if match_func(KEYWORDS.get("lock_me"), message):
            return Chinchin_me.entry_lock_me(ctx)

        # 自己打胶
        if match_func(KEYWORDS.get("glue"), message):
            return Chinchin_me.entry_glue(ctx)


class Chinchin_intercepor:
    @staticmethod
    def length_operate(qq: int, origin_change: float, source: str = OpFrom.OTHER):
        rebirth_weight = RebirthSystem.get_weight_by_qq(qq)
        result = origin_change * rebirth_weight
        result = BadgeSystem.handle_weighting_by_qq(qq, result, source)
        result = fixed_two_decimal_digits(result, to_number=True)
        return result


class Chinchin_view:
    @staticmethod
    def length_label(
        length: float,
        level: int = None,
        need_level_label: bool = True,
        data_only: bool = False,
        unit: str = "cm",
    ):
        if level is None:
            length_value = fixed_two_decimal_digits(length)
            if data_only:
                return {
                    "length": length_value,
                }
            return f"{length_value}{unit}"
        else:
            level_view = RebirthSystem.view.get_rebirth_view_by_level(
                level=level, length=length
            )
            pure_length = level_view["pure_length"]
            if data_only:
                return {
                    "length": fixed_two_decimal_digits(pure_length),
                    "current_level_info": level_view["current_level_info"],
                }
            level_label = ""
            if need_level_label:
                label = level_view["current_level_info"]["name"]
                level_label = f" ({label})"
            return f"{fixed_two_decimal_digits(pure_length)}{unit}{level_label}"


class Chinchin_info:
    @staticmethod
    def entry_ranking(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        msg_ctx = ctx["msg_ctx"]
        # remove before `at` msg
        if len(msg_ctx["before"]) > 0:
            del msg_ctx["before"][0]
        top_users = DB.get_top_users()
        message_arr = [
            "【牛子宇宙最长大牛子】",
        ]
        for user in top_users:
            idx = top_users.index(user) + 1
            prefix = ""
            if idx == 1:
                prefix = "🥇"
            elif idx == 2:
                prefix = "🥈"
            elif idx == 3:
                prefix = "🥉"
            if "latest_speech_nickname" not in user:
                user["latest_speech_nickname"] = ""
            nickname = user["latest_speech_nickname"]
            if len(nickname) == 0:
                nickname = "无名英雄"
            badge = BadgeSystem.get_first_badge_by_badge_string_arr(
                user.get("badge_ids")
            )
            if badge:
                nickname = f"【{badge}】{nickname}"
            length_label = Chinchin_view.length_label(
                length=user.get("length"),
                level=user.get("level"),
                need_level_label=True,
            )
            message_arr.append(f"{idx}. {prefix}{nickname} 长度：{length_label}")
        send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def entry_chinchin(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        user_chinchin_info = ChinchinInternal.internal_get_chinchin_info(qq)
        send_message(bot, qq, group, join(user_chinchin_info, "\n"))

    @staticmethod
    def entry_see_chinchin(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        at_qq = ctx["at_qq"]
        target_chinchin_info = ChinchinInternal.internal_get_chinchin_info(at_qq)
        msg_text = join(target_chinchin_info, "\n")
        msg_text = msg_text.replace("【牛子信息】", "【对方牛子信息】")
        send_message(bot, qq, group, msg_text)


class ChinchinInternal:
    @staticmethod
    def internal_get_chinchin_info(qq: int):
        user_data = DB.load_data(qq)
        message_arr = [
            "【牛子信息】",
        ]
        # badge
        badge_label = BadgeSystem.get_badge_label_by_qq(qq)
        if badge_label is not None:
            message_arr.append(f"成就: {badge_label}")
        length_label = Chinchin_view.length_label(
            length=user_data.get("length"),
            level=user_data.get("level"),
            need_level_label=True,
            unit="厘米",
        )
        # length
        message_arr.append(f"长度: {length_label}")
        # locked
        if user_data.get("locked_time") != DEFAULT_NONE_TIME:
            message_arr.append(
                "最近被🔒时间: {}".format(
                    ArrowUtil.date_improve(user_data.get("locked_time"))
                )
            )
        # pk
        if user_data.get("pk_time") != DEFAULT_NONE_TIME:
            message_arr.append(
                "最近pk时间: {}".format(ArrowUtil.date_improve(user_data.get("pk_time")))
            )
        # pked
        if user_data.get("pked_time") != DEFAULT_NONE_TIME:
            message_arr.append(
                "最近被pk时间: {}".format(ArrowUtil.date_improve(user_data.get("pked_time")))
            )
        # glueing
        if user_data.get("glueing_time") != DEFAULT_NONE_TIME:
            message_arr.append(
                "最近打胶时间: {}".format(
                    ArrowUtil.date_improve(user_data.get("glueing_time"))
                )
            )
        # glued
        if user_data.get("glued_time") != DEFAULT_NONE_TIME:
            message_arr.append(
                "最近被打胶时间: {}".format(
                    ArrowUtil.date_improve(user_data.get("glued_time"))
                )
            )
        # register
        message_arr.append(
            "注册时间: {}".format(ArrowUtil.date_improve(user_data.get("register_time")))
        )
        return message_arr


class Chinchin_me:
    @staticmethod
    def entry_lock_me(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        # check limited
        is_today_limited = DB.is_lock_daily_limited(qq)
        if is_today_limited:
            message_arr = ["你的牛子今天太累了，改天再来吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # check cd
        is_in_cd = CD_Check.is_lock_in_cd(qq)
        if is_in_cd:
            message_arr = ["歇一会吧，嘴都麻了！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        lock_me_min = Config.get_config("lock_me_chinchin_min")
        user_data = DB.load_data(qq)
        DB.record_time(qq, "locked_time")
        DB.count_lock_daily(qq)
        if user_data.get("length") < lock_me_min:
            is_need_punish = Config.is_hit("lock_me_negative_prob")
            if is_need_punish:
                punish_value = Config.get_lock_me_punish_value()
                # not need weighting
                DB.length_decrease(qq, punish_value)
                message_arr = ["你的牛子还不够长，你🔒不着，牛子自尊心受到了伤害，缩短了{}厘米".format(punish_value)]
                send_message(bot, qq, group, join(message_arr, "\n"))
            else:
                message_arr = ["你的牛子太小了，还🔒不到"]
                send_message(bot, qq, group, join(message_arr, "\n"))
        else:
            # record record_lock_me_count to qq
            DB.sub_db_badge.record_lock_me_count(qq)
            # FIXME: 因为🔒自己回报高，这样会导致强者一直🔒自己，越强，所以需要一种小概率制裁机制。
            is_lock_failed = Config.is_hit("lock_me_negative_prob_with_strong_person")
            if is_lock_failed:
                punish_value = Config.get_lock_punish_with_strong_person_value()
                # not need weighting
                DB.length_decrease(qq, punish_value)
                # record record_lock_punish_count to qq
                DB.sub_db_badge.record_lock_punish_count(qq)
                # record record_lock_punish_length_total to qq
                DB.sub_db_badge.record_lock_punish_length_total(qq, punish_value)
                message_arr = ["你的牛子太长了，没🔒住爆炸了，缩短了{}厘米".format(punish_value)]
                send_message(bot, qq, group, join(message_arr, "\n"))
            else:
                plus_value = Chinchin_intercepor.length_operate(
                    qq, Config.get_lock_plus_value(), source=OpFrom.LOCK_ME
                )
                # weighting from qq
                DB.length_increase(qq, plus_value)
                # record record_lock_plus_count to qq
                DB.sub_db_badge.record_lock_plus_count(qq)
                # record record_lock_plus_length_total to qq
                DB.sub_db_badge.record_lock_plus_length_total(qq, plus_value)
                # TODO: 🔒自己效果有加成
                message_arr = ["自己把自己搞舒服了，牛子涨了{}厘米".format(plus_value)]
                send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def entry_glue(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        # check limited
        is_today_limited = DB.is_glue_daily_limited(qq)
        if is_today_limited:
            message_arr = ["牛子快被你冲炸了，改天再来冲吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # check cd
        is_in_cd = CD_Check.is_glue_in_cd(qq)
        if is_in_cd:
            message_arr = ["你刚打了一胶，歇一会吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        DB.record_time(qq, "glueing_time")
        DB.count_glue_daily(qq)
        # record record_glue_me_count to qq
        DB.sub_db_badge.record_glue_me_count(qq)
        is_glue_failed = Config.is_hit("glue_self_negative_prob")
        if is_glue_failed:
            punish_value = Config.get_glue_self_punish_value()
            # not need weighting
            DB.length_decrease(qq, punish_value)
            # record record_glue_punish_count to qq
            DB.sub_db_badge.record_glue_punish_count(qq)
            # record record_glue_punish_length_total to qq
            DB.sub_db_badge.record_glue_punish_length_total(qq, punish_value)
            message_arr = ["打胶结束，牛子快被冲爆炸了，减小{}厘米".format(punish_value)]
            send_message(bot, qq, group, join(message_arr, "\n"))
        else:
            plus_value = Chinchin_intercepor.length_operate(
                qq, Config.get_glue_plus_value(), source=OpFrom.GLUE_ME
            )
            # weighting from qq
            DB.length_increase(qq, plus_value)
            # record record_glue_plus_count to qq
            DB.sub_db_badge.record_glue_plus_count(qq)
            # record record_glue_plus_length_total to qq
            DB.sub_db_badge.record_glue_plus_length_total(qq, plus_value)
            message_arr = ["牛子对你的付出很满意吗，增加{}厘米".format(plus_value)]
            send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def sign_up(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        if DB.is_registered(qq):
            message_arr = ["你已经有牛子了！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # 注册
        new_length = Config.new_chinchin_length()
        new_user = {
            "qq": qq,
            "length": new_length,
            "register_time": ArrowUtil.get_now_time(),
            "daily_lock_count": 0,
            "daily_pk_count": 0,
            "daily_glue_count": 0,
            "latest_daily_lock": DEFAULT_NONE_TIME,
            "latest_daily_pk": DEFAULT_NONE_TIME,
            "latest_daily_glue": DEFAULT_NONE_TIME,
            "pk_time": DEFAULT_NONE_TIME,
            "pked_time": DEFAULT_NONE_TIME,
            "glueing_time": DEFAULT_NONE_TIME,
            "glued_time": DEFAULT_NONE_TIME,
            "locked_time": DEFAULT_NONE_TIME,
        }
        DB.create_data(new_user)
        message_arr = [
            "你是第{}位拥有牛子的人，当前长度：{}厘米，请好好善待它！".format(
                DB.get_data_counts(),
                fixed_two_decimal_digits(new_length),
            )
        ]
        send_message(bot, qq, group, join(message_arr, "\n"))


class Chinchin_with_target:
    @staticmethod
    def entry_pk_with_target(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        at_qq = ctx["at_qq"]
        # 不能 pk 自己
        if qq == at_qq:
            message_arr = ["你不能和自己的牛子进行较量！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # check limited
        is_today_limited = DB.is_pk_daily_limited(qq)
        if is_today_limited:
            message_arr = ["战斗太多次牛子要虚脱了，改天再来吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # check cd
        is_in_cd = CD_Check.is_pk_in_cd(qq)
        if is_in_cd:
            message_arr = ["牛子刚结束战斗，歇一会吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # pk 保护机制：禁止刷分
        is_target_protected = DB.is_pk_protected(at_qq)
        if is_target_protected:
            message_arr = ["对方快没有牛子了，行行好吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        target_data = DB.load_data(at_qq)
        user_data = DB.load_data(qq)
        target_length = target_data.get("length")
        user_length = user_data.get("length")
        is_user_win = Config.is_pk_win(user_length, target_length)
        DB.record_time(qq, "pk_time")
        DB.record_time(at_qq, "pked_time")
        DB.count_pk_daily(qq)
        if is_user_win:
            is_giant_kill = user_length < target_length
            if is_giant_kill:
                pk_message = "pk成功了，对面本以为自己牛子是最棒的，但没想到被你拿下，你的才是最棒的"
            else:
                pk_message = "pk成功了，对面牛子不值一提，你的是最棒的"
            user_plus_value = Chinchin_intercepor.length_operate(
                qq, Config.get_pk_plus_value(), source=OpFrom.PK_WIN
            )
            target_punish_value = Chinchin_intercepor.length_operate(
                qq, Config.get_pk_punish_value(), source=OpFrom.PK_LOSE
            )
            # weighting from qq
            DB.length_increase(qq, user_plus_value)
            # weighting from qq
            DB.length_decrease(at_qq, target_punish_value)
            # record pk_win_count to qq
            DB.sub_db_badge.record_pk_win_count(qq)
            # record record_pk_plus_length_total to qq
            DB.sub_db_badge.record_pk_plus_length_total(qq, user_plus_value)
            message_arr = [
                f"{pk_message}，牛子获得自信增加了{user_plus_value}厘米，对面牛子减小了{target_punish_value}厘米"
            ]
            send_message(bot, qq, group, join(message_arr, "\n"))
        else:
            user_punish_value = Config.get_pk_punish_value()
            target_plus_value = Config.get_pk_plus_value()
            # not need weighting
            DB.length_decrease(qq, user_punish_value)
            DB.length_increase(at_qq, target_plus_value)
            # record pk_lose_count to qq
            DB.sub_db_badge.record_pk_lose_count(qq)
            # record record_pk_punish_length_total to qq
            DB.sub_db_badge.record_pk_punish_length_total(qq, user_punish_value)
            message_arr = [
                "pk失败了，在对面牛子的阴影笼罩下，你的牛子减小了{}厘米，对面牛子增加了{}厘米".format(
                    user_punish_value, target_plus_value
                )
            ]
            send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def entry_lock_with_target(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        at_qq = ctx["at_qq"]
        # 🔒 自己是单独的逻辑
        if qq == at_qq:
            Chinchin_me.entry_lock_me(ctx)
            return
        # TODO：🔒别人可能失败
        # check limited
        is_today_limited = DB.is_lock_daily_limited(qq)
        if is_today_limited:
            message_arr = ["别🔒了，要口腔溃疡了，改天再🔒吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # check cd
        is_in_cd = CD_Check.is_lock_in_cd(qq)
        if is_in_cd:
            message_arr = ["歇一会吧，嘴都麻了！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        target_plus_value = Chinchin_intercepor.length_operate(
            qq, Config.get_lock_plus_value(), source=OpFrom.LOCK_WITH_TARGET
        )
        # weighting from qq
        DB.length_increase(at_qq, target_plus_value)
        DB.record_time(at_qq, "locked_time")
        DB.count_lock_daily(qq)
        # record record_lock_target_count to qq
        DB.sub_db_badge.record_lock_target_count(qq)
        # record record_lock_plus_count to qq
        DB.sub_db_badge.record_lock_plus_count(qq)
        # record record_lock_plus_length_total to qq
        DB.sub_db_badge.record_lock_plus_length_total(qq, target_plus_value)
        message_arr = ["🔒的很卖力很舒服，对方牛子增加了{}厘米".format(target_plus_value)]
        send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def entry_glue_with_target(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        at_qq = ctx["at_qq"]
        # 打胶自己跳转
        if qq == at_qq:
            Chinchin_me.entry_glue(ctx)
            return
        # check limited
        is_today_limited = DB.is_glue_daily_limited(qq)
        if is_today_limited:
            message_arr = ["你今天帮太多人打胶了，改天再来吧！ "]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # check cd
        is_in_cd = CD_Check.is_glue_in_cd(qq)
        if is_in_cd:
            message_arr = ["你刚打了一胶，歇一会吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        DB.record_time(at_qq, "glued_time")
        DB.count_glue_daily(qq)
        # record record_glue_target_count to qq
        DB.sub_db_badge.record_glue_target_count(qq)
        is_glue_failed = Config.is_hit("glue_negative_prob")
        if is_glue_failed:
            target_punish_value = Chinchin_intercepor.length_operate(
                qq, Config.get_glue_punish_value(), source=OpFrom.GLUE_WITH_TARGET
            )
            # weighting from qq
            DB.length_decrease(at_qq, target_punish_value)
            # record record_glue_punish_count to qq
            DB.sub_db_badge.record_glue_punish_count(qq)
            # record record_glue_punish_length_total to qq
            DB.sub_db_badge.record_glue_punish_length_total(qq, target_punish_value)
            message_arr = ["对方牛子快被大家冲坏了，减小{}厘米".format(target_punish_value)]
            send_message(bot, qq, group, join(message_arr, "\n"))
        else:
            target_plus_value = Chinchin_intercepor.length_operate(
                qq, Config.get_glue_plus_value(), source=OpFrom.GLUE_WITH_TARGET
            )
            # weighting from qq
            DB.length_increase(at_qq, target_plus_value)
            # record record_glue_plus_count to qq
            DB.sub_db_badge.record_glue_plus_count(qq)
            # record record_glue_plus_length_total to at_qq
            DB.sub_db_badge.record_glue_plus_length_total(qq, target_plus_value)
            message_arr = ["你的打胶让对方牛子感到很舒服，对方牛子增加{}厘米".format(target_plus_value)]
            send_message(bot, qq, group, join(message_arr, "\n"))


class Chinchin_upgrade:
    @staticmethod
    def entry_rebirth(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        # TODO: 满转人士提示，不能再转了
        info = RebirthSystem.get_rebirth_info(qq)
        if info["can_rebirth"] is False:
            message_arr = ["你和牛子四目相对，牛子摇了摇头，说下次一定！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # rebirth
        is_rebirth_fail = info["failed_info"]["is_failed"]
        if is_rebirth_fail:
            # punish
            punish_length = info["failed_info"]["failed_punish_length"]
            DB.length_decrease(qq, punish_length)
            message_arr = ["细数牛界之中，贸然渡劫者九牛一生，牛子失去荔枝爆炸了，减小{}厘米".format(punish_length)]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # success
        is_first_rebirth = info["current_level_info"] is None
        rebirth_data = {
            "qq": qq,
            "level": info["next_level_info"]["level"],
            "latest_rebirth_time": ArrowUtil.get_now_time(),
        }
        if is_first_rebirth:
            DB.sub_db_rebirth.insert_rebirth_data(rebirth_data)
        else:
            DB.sub_db_rebirth.update_rebirth_data(rebirth_data)
        message_arr = [
            "你为了强度已经走了太远，却忘记当初为什么而出发，电光石火间飞升为【{}】！".format(
                info["next_level_info"]["name"]
            )
        ]
        send_message(bot, qq, group, join(message_arr, "\n"))
        return


class Chinchin_badge:
    @staticmethod
    def entry_badge(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        badge_view = BadgeSystem.get_badge_view(qq)
        message_arr = []
        if badge_view is None:
            message_arr.append("现在是幻想时间")
        else:
            message_arr.append(badge_view)
        send_message(bot, qq, group, join(message_arr, "\n"))


class Chinchin_farm:
    @staticmethod
    def entry_farm_info(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        view = FarmSystem.get_farm_view(qq)
        message_arr = [view]
        send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def entry_farm(ctx: dict):
        bot = ctx["bot"]
        qq = ctx["qq"]
        group = ctx["group"]
        # 检查是否可玩
        is_current_can_play = FarmSystem.is_current_can_play()
        if not is_current_can_play:
            message_arr = ["牛子仙境大门紧闭，晚些时候再来吧！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # 检查是否正在修炼
        is_current_planting = FarmSystem.is_current_planting(qq)
        if is_current_planting:
            message_arr = ["稍安勿躁，你的牛子正在秘密修练中！"]
            send_message(bot, qq, group, join(message_arr, "\n"))
            return
        # 可玩的逻辑, start plant
        plant_info = FarmSystem.start_plant(qq)
        need_time_minutes = plant_info["need_time_minutes"]
        message_arr = [f"神只会在必要的时候展现他牛子的冰山一角，完成飞升预计需要{need_time_minutes}分钟"]
        send_message(bot, qq, group, join(message_arr, "\n"))

    @staticmethod
    def check_planting_status(ctx):
        qq = ctx["qq"]
        is_current_planting = FarmSystem.is_current_planting(qq)
        if not is_current_planting:
            data = DB.sub_db_farm.get_user_data(qq)
            is_plant_over = FarmConst.is_planting(data["farm_status"])
            if is_plant_over:
                # reset user
                FarmSystem.reset_user_data(qq)
                # reward length
                expect_plus_length = data["farm_expect_get_length"]
                reward_length = Chinchin_intercepor.length_operate(
                    qq, expect_plus_length, source=OpFrom.FARM_OVER
                )
                # update length
                DB.length_increase(qq, reward_length)
                # add msg
                ctx["msg_ctx"]["before"].append(
                    f"牛子修炼结束，你感觉前所未有的舒服，增加了{reward_length}厘米"
                )
        return is_current_planting
