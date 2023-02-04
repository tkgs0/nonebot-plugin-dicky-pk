from .db import DB, lazy_init_database
from .impl import get_at_segment, send_message
from .utils import create_match_func_factory, join, get_now_time, fixed_two_decimal_digits, date_improve
from .config import Config
from .cd import CD_Check
from typing import Optional
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot

KEYWORDS = {
    'chinchin': ['牛子'],
    'pk': ['pk'],
    'lock_me': ['🔒我', 'suo我', '嗦我', '锁我'],
    'lock': ['🔒', 'suo', '嗦', '锁'],
    'glue': ['打胶'],
    'see_chinchin': ['看他牛子', '看看牛子'],
    'sign_up': ['注册牛子'],
    'ranking': ['牛子排名', '牛子排行'],
}

DEFAULT_NONE_TIME = '2000-01-01 00:00:00'


def message_processor(
    bot: Bot,
    matcher: Matcher,
    message: str,
    qq: int,
    group: int,
    at_qq: Optional[int] = None,
    nickname: Optional[str] = None,
    fuzzy_match: bool = False,
    impl_at_segment=None,
    impl_send_message=None
):
    """
        main entry
        TODO: 破解牛子：被破解的 牛子 长度操作 x 100 倍
        TODO: 不同群不同的配置参数
        TODO: 成就系统
    """
    # lazy init database
    lazy_init_database()

    # message process
    message = message.strip()
    match_func = create_match_func_factory(fuzzy=fuzzy_match)

    # hack impl
    if impl_at_segment:
        global get_at_segment
        get_at_segment = impl_at_segment
    if impl_send_message:
        global send_message
        send_message = impl_send_message

    # 记录数据
    DB.sub_db_info.record_user_info(qq, {
        'latest_speech_group': group,
        'latest_speech_nickname': nickname,
    })

    # 注册牛子
    if match_func(KEYWORDS.get('sign_up'), message):
        return Chinchin_me.sign_up(bot, matcher, qq, group)

    # 下面的逻辑必须有牛子
    if not DB.is_registered(qq):
        message_arr = [
            get_at_segment(qq),
            '你还没有牛子！'
        ]
        send_message(bot, matcher, qq, group, join(message_arr, '\n'))
        return

    # 牛子排名
    if match_func(KEYWORDS.get('ranking'), message):
        return Chinchin_info.entry_ranking(bot, matcher, qq, group)

    # 查询牛子信息
    if match_func(KEYWORDS.get('chinchin'), message):
        return Chinchin_info.entry_chinchin(bot, matcher, qq, group)

    # 对别人的
    if at_qq:
        if not DB.is_registered(at_qq):
            message_arr = [
                get_at_segment(qq),
                '对方还没有牛子！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return

        # pk别人
        if match_func(KEYWORDS.get('pk'), message):
            return Chinchin_with_target.entry_pk_with_target(bot, matcher, qq, group, at_qq)

        # 🔒别人
        if match_func(KEYWORDS.get('lock'), message):
            return Chinchin_with_target.entry_lock_with_target(bot, matcher, qq, group, at_qq)

        # 打胶别人
        if match_func(KEYWORDS.get('glue'), message):
            return Chinchin_with_target.entry_glue_with_target(bot, matcher, qq, group, at_qq)

        # 看别人的牛子
        if match_func(KEYWORDS.get('see_chinchin'), message):
            return Chinchin_info.entry_see_chinchin(bot, matcher, qq, group, at_qq)
    else:
        # 🔒自己
        if match_func(KEYWORDS.get('lock_me'), message):
            return Chinchin_me.entry_lock_me(bot, matcher, qq, group)

        # 自己打胶
        if match_func(KEYWORDS.get('glue'), message):
            return Chinchin_me.entry_glue(bot, matcher, qq, group)


class Chinchin_info():

    @staticmethod
    def entry_ranking(bot: Bot, matcher: Matcher, qq: int, group: int):
        top_users = DB.get_top_users()
        message_arr = [
            '【牛子国最长大牛子】',
        ]
        for user in top_users:
            idx = top_users.index(user) + 1
            prefix = ''
            if idx == 1:
                prefix = '🥇'
            elif idx == 2:
                prefix = '🥈'
            elif idx == 3:
                prefix = '🥉'
            if 'latest_speech_nickname' not in user:
                user['latest_speech_nickname'] = ''
            nickname = user['latest_speech_nickname']
            if len(nickname) == 0:
                nickname = '无名英雄'
            message_arr.append(
                f'{idx}. {prefix}{nickname} 长度：{fixed_two_decimal_digits(user["length"])}cm')
        send_message(bot, matcher, qq, group, join(message_arr, '\n'))

    @staticmethod
    def entry_chinchin(bot: Bot, matcher: Matcher, qq: int, group: int):
        user_chinchin_info = ChinchinInternal.internal_get_chinchin_info(
            qq)
        send_message(bot, matcher, qq, group, join(user_chinchin_info, '\n'))

    @staticmethod
    def entry_see_chinchin(bot: Bot, matcher: Matcher, qq: int, group: int, at_qq: int):
        target_chinchin_info = ChinchinInternal.internal_get_chinchin_info(
            at_qq)
        msg_text = join(target_chinchin_info, '\n')
        msg_text = msg_text.replace('【牛子信息】', '【对方牛子信息】')
        send_message(bot, matcher, qq, group, msg_text)


class ChinchinInternal():
    @staticmethod
    def internal_get_chinchin_info(qq: int):
        user_data = DB.load_data(qq)
        message_arr = [
            get_at_segment(qq),
            '【牛子信息】',
        ]
        # length
        message_arr.append(
            '长度: {}厘米'.format(fixed_two_decimal_digits(
                user_data.get('length'),
                to_number=False
            ))
        )
        # locked
        if user_data.get('locked_time') != DEFAULT_NONE_TIME:
            message_arr.append(
                '最近被🔒时间: {}'.format(
                    date_improve(
                        user_data.get('locked_time')
                    )
                )
            )
        # pk
        if user_data.get('pk_time') != DEFAULT_NONE_TIME:
            message_arr.append(
                '最近pk时间: {}'.format(
                    date_improve(
                        user_data.get('pk_time')
                    )
                )
            )
        # pked
        if user_data.get('pked_time') != DEFAULT_NONE_TIME:
            message_arr.append(
                '最近被pk时间: {}'.format(
                    date_improve(
                        user_data.get('pked_time')
                    )
                )
            )
        # glueing
        if user_data.get('glueing_time') != DEFAULT_NONE_TIME:
            message_arr.append(
                '最近打胶时间: {}'.format(
                    date_improve(
                        user_data.get('glueing_time')
                    )
                )
            )
        # glued
        if user_data.get('glued_time') != DEFAULT_NONE_TIME:
            message_arr.append(
                '最近被打胶时间: {}'.format(
                    date_improve(
                        user_data.get('glued_time')
                    )
                )
            )
        # register
        message_arr.append(
            '注册时间: {}'.format(date_improve(
                user_data.get('register_time')
            ))
        )
        return message_arr


class Chinchin_me():

    @staticmethod
    def entry_lock_me(bot: Bot, matcher: Matcher, qq: int, group: int):
        # check limited
        is_today_limited = DB.is_lock_daily_limited(qq)
        if is_today_limited:
            message_arr = [
                get_at_segment(qq),
                '你的牛子今天太累了，改天再来吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # check cd
        is_in_cd = CD_Check.is_lock_in_cd(qq)
        if is_in_cd:
            message_arr = [
                get_at_segment(qq),
                '歇一会吧，嘴都麻了！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        lock_me_min = Config.get_config('lock_me_chinchin_min')
        user_data = DB.load_data(qq)
        DB.record_time(qq, 'locked_time')
        DB.count_lock_daily(qq)
        if user_data.get('length') < lock_me_min:
            is_need_punish = Config.is_hit('lock_me_negative_prob')
            if is_need_punish:
                punish_value = Config.get_lock_me_punish_value()
                DB.length_decrease(qq, punish_value)
                message_arr = [
                    get_at_segment(qq),
                    '你的牛子还不够长，你🔒不着，牛子自尊心受到了伤害，缩短了{}厘米'.format(punish_value)
                ]
                send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            else:
                message_arr = [
                    get_at_segment(qq),
                    '你的牛子太小了，还🔒不到'
                ]
                send_message(bot, matcher, qq, group, join(message_arr, '\n'))
        else:
            # FIXME: 因为🔒自己回报高，这样会导致强者一直🔒自己，越强，所以需要一种小概率制裁机制。
            is_lock_failed = Config.is_hit(
                'lock_me_negative_prob_with_strong_person')
            if is_lock_failed:
                punish_value = Config.get_lock_punish_with_strong_person_value()
                DB.length_decrease(qq, punish_value)
                message_arr = [
                    get_at_segment(qq),
                    '你的牛子太长了，没🔒住爆炸了，缩短了{}厘米'.format(punish_value)
                ]
                send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            else:
                plus_value = Config.get_lock_plus_value()
                DB.length_increase(qq, plus_value)
                # TODO: 🔒自己效果有加成
                message_arr = [
                    get_at_segment(qq),
                    '🔒的很卖力很舒服，你的牛子增加了{}厘米'.format(plus_value)
                ]
                send_message(bot, matcher, qq, group, join(message_arr, '\n'))

    @staticmethod
    def entry_glue(bot: Bot, matcher: Matcher, qq: int, group: int):
        # check limited
        is_today_limited = DB.is_glue_daily_limited(qq)
        if is_today_limited:
            message_arr = [
                get_at_segment(qq),
                '牛子快被你冲炸了，改天再来冲吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # check cd
        is_in_cd = CD_Check.is_glue_in_cd(qq)
        if is_in_cd:
            message_arr = [
                get_at_segment(qq),
                '你刚打了一胶，歇一会吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        DB.record_time(qq, 'glueing_time')
        DB.count_glue_daily(qq)
        is_glue_failed = Config.is_hit('glue_self_negative_prob')
        if is_glue_failed:
            punish_value = Config.get_glue_self_punish_value()
            DB.length_decrease(qq, punish_value)
            message_arr = [
                get_at_segment(qq),
                '打胶结束，牛子快被冲爆炸了，减小{}厘米'.format(punish_value)
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
        else:
            plus_value = Config.get_glue_plus_value()
            DB.length_increase(qq, plus_value)
            message_arr = [
                get_at_segment(qq),
                '牛子对你的付出很满意吗，增加{}厘米'.format(plus_value)
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))

    @staticmethod
    def sign_up(bot: Bot, matcher: Matcher, qq: int, group: int):
        if DB.is_registered(qq):
            message_arr = [
                get_at_segment(qq),
                '你已经有牛子了！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # 注册
        new_length = Config.new_chinchin_length()
        new_user = {
            'qq': qq,
            'length': new_length,
            'register_time': get_now_time(),
            'daily_lock_count': 0,
            'daily_pk_count': 0,
            'daily_glue_count': 0,
            'latest_daily_lock': DEFAULT_NONE_TIME,
            'latest_daily_pk': DEFAULT_NONE_TIME,
            'latest_daily_glue': DEFAULT_NONE_TIME,
            'pk_time': DEFAULT_NONE_TIME,
            'pked_time': DEFAULT_NONE_TIME,
            'glueing_time': DEFAULT_NONE_TIME,
            'glued_time': DEFAULT_NONE_TIME,
            'locked_time': DEFAULT_NONE_TIME,
        }
        DB.create_data(new_user)
        message_arr = [
            get_at_segment(qq),
            '你是第{}位拥有牛子的人，当前长度：{}厘米，请好好善待它！'.format(
                DB.get_data_counts(),
                fixed_two_decimal_digits(new_length),
            )
        ]
        send_message(bot, matcher, qq, group, join(message_arr, '\n'))


class Chinchin_with_target():

    @staticmethod
    def entry_pk_with_target(bot: Bot, matcher: Matcher, qq: int, group: int, at_qq: int):
        # 不能 pk 自己
        if qq == at_qq:
            message_arr = [
                get_at_segment(qq),
                '你不能和自己的牛子进行较量！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # check limited
        is_today_limited = DB.is_pk_daily_limited(qq)
        if is_today_limited:
            message_arr = [
                get_at_segment(qq),
                '战斗太多次牛子要虚脱了，改天再来吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # check cd
        is_in_cd = CD_Check.is_pk_in_cd(qq)
        if is_in_cd:
            message_arr = [
                get_at_segment(qq),
                '牛子刚结束战斗，歇一会吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # pk 保护机制：禁止刷分
        is_target_protected = DB.is_pk_protected(at_qq)
        if is_target_protected:
            message_arr = [
                get_at_segment(qq),
                '对方快没有牛子了，行行好吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        target_data = DB.load_data(at_qq)
        user_data = DB.load_data(qq)
        target_length = target_data.get('length')
        user_length = user_data.get('length')
        offset = user_length - target_length
        offset_abs = abs(offset)
        is_user_win = False
        if offset_abs < Config.get_config('pk_unstable_range'):
            is_user_win = Config.is_pk_win()
        else:
            is_user_win = (offset > 0)
        DB.record_time(qq, 'pk_time')
        DB.record_time(at_qq, 'pked_time')
        DB.count_pk_daily(qq)
        if is_user_win:
            user_plus_value = Config.get_pk_plus_value()
            target_punish_value = Config.get_pk_punish_value()
            DB.length_increase(qq, user_plus_value)
            DB.length_decrease(at_qq, target_punish_value)
            message_arr = [
                get_at_segment(qq),
                'pk成功了，对面牛子不值一提，你的是最棒的，牛子获得自信增加了{}厘米，对面牛子减小了{}厘米'.format(
                    user_plus_value, target_punish_value)
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
        else:
            user_punish_value = Config.get_pk_punish_value()
            target_plus_value = Config.get_pk_plus_value()
            DB.length_decrease(qq, user_punish_value)
            DB.length_increase(at_qq, target_plus_value)
            message_arr = [
                get_at_segment(qq),
                'pk失败了，在对面牛子的阴影笼罩下，你的牛子减小了{}厘米，对面牛子增加了{}厘米'.format(
                    user_punish_value, target_plus_value)
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))

    @staticmethod
    def entry_lock_with_target(bot: Bot, matcher: Matcher, qq: int, group: int, at_qq: int):
        # 🔒 自己是单独的逻辑
        if qq == at_qq:
            Chinchin_me.entry_lock_me(bot, matcher, qq, group)
            return
        # TODO：🔒别人可能失败
        # check limited
        is_today_limited = DB.is_lock_daily_limited(qq)
        if is_today_limited:
            message_arr = [
                get_at_segment(qq),
                '别🔒了，要口腔溃疡了，改天再🔒吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # check cd
        is_in_cd = CD_Check.is_lock_in_cd(qq)
        if is_in_cd:
            message_arr = [
                get_at_segment(qq),
                '歇一会吧，嘴都麻了！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        target_plus_value = Config.get_lock_plus_value()
        DB.length_increase(at_qq, target_plus_value)
        DB.record_time(at_qq, 'locked_time')
        DB.count_lock_daily(qq)
        message_arr = [
            get_at_segment(qq),
            '🔒的很卖力很舒服，对方牛子增加了{}厘米'.format(target_plus_value)
        ]
        send_message(bot, matcher, qq, group, join(message_arr, '\n'))

    @staticmethod
    def entry_glue_with_target(bot: Bot, matcher: Matcher, qq: int, group: int, at_qq: int):
        # 打胶自己跳转
        if qq == at_qq:
            Chinchin_me.entry_glue(bot, matcher, qq, group)
            return
        # check limited
        is_today_limited = DB.is_glue_daily_limited(qq)
        if is_today_limited:
            message_arr = [
                get_at_segment(qq),
                '你今天帮太多人打胶了，改天再来吧！ '
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        # check cd
        is_in_cd = CD_Check.is_glue_in_cd(qq)
        if is_in_cd:
            message_arr = [
                get_at_segment(qq),
                '你刚打了一胶，歇一会吧！'
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
            return
        DB.record_time(at_qq, 'glued_time')
        DB.count_glue_daily(qq)
        is_glue_failed = Config.is_hit('glue_negative_prob')
        if is_glue_failed:
            target_punish_value = Config.get_glue_punish_value()
            DB.length_decrease(at_qq, target_punish_value)
            message_arr = [
                get_at_segment(qq),
                '对方牛子快被大家冲坏了，减小{}厘米'.format(target_punish_value)
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
        else:
            target_plus_value = Config.get_glue_plus_value()
            DB.length_increase(at_qq, target_plus_value)
            message_arr = [
                get_at_segment(qq),
                '你的打胶让对方牛子感到很舒服，对方牛子增加{}厘米'.format(target_plus_value)
            ]
            send_message(bot, matcher, qq, group, join(message_arr, '\n'))
