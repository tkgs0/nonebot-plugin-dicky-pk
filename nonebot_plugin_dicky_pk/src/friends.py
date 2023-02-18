from .config import Config
from .db import DB
from .utils import fixed_two_decimal_digits, ArrowUtil, join
from .constants import OpFrom

cache = None


class FriendsSystem:
    @staticmethod
    def read_config():
        global cache
        if cache:
            return cache
        json = Config.get_config("friends")
        cache = json
        return cache

    @staticmethod
    def modify_config_in_runtime(data: dict):
        global cache
        cache = data

    @classmethod
    def get_friends_data(cls, qq: int):
        config = cls.read_config()
        data = DB.sub_db_friends.get_user_data(qq)
        friends = []
        friends_list_str = data["friends_list"]
        # parse string to int list
        if len(friends_list_str) != 0:
            friends_str_list = friends_list_str.split(",")
            for friend in friends_str_list:
                qq_int = int(friend)
                friends.append(qq_int)
            data["friends_list"] = friends
        else:
            data["friends_list"] = []
        # search user data and merge
        user_data = DB.load_data(qq)
        info_data = DB.sub_db_info.get_user_info(qq)
        # add calc cost
        friends_need_cost = fixed_two_decimal_digits(
            user_data['length'] * (
                config['cost']['base'] + config['cost']['share'] * data['friends_share_count']),
            to_number=True
        )
        data['friends_need_cost'] = friends_need_cost
        merge = DB.utils.merge_data(user_data, data, info_data)
        return merge

    @classmethod
    def get_batch_friends_info_by_qqs(cls, qqs: list):
        config = cls.read_config()
        friends_data = DB.sub_db_friends.get_batch_user_data(qqs)
        users_data = DB.get_batch_users(qqs)
        info_table_data = DB.sub_db_info.get_batch_user_infos(qqs)
        merge = DB.utils.merge_data_list(
            [users_data, info_table_data, friends_data],
        )
        infos = []
        for user in merge:
            base_friend_cost_percent = config["cost"]["base"]
            share_friend_cost_percent = config["cost"]["share"] * \
                user["friends_share_count"]
            total_cost_percent = base_friend_cost_percent + share_friend_cost_percent
            total_cost_length = user["length"] * total_cost_percent
            total_cost = fixed_two_decimal_digits(
                total_cost_length, to_number=True
            )
            info = {
                "friends_need_cost": total_cost,
                **user,
            }
            infos.append(info)
        # sort by cost desc
        infos = sorted(
            infos, key=lambda x: x["friends_need_cost"], reverse=True)
        return infos

    @classmethod
    def get_friends_list_view(cls, qq: int):
        friends_data = cls.get_friends_data(qq)
        friends_list = friends_data["friends_list"]
        is_not_has_friends = len(friends_list) == 0
        if is_not_has_friends:
            message_arr = ["相比之下，你就是个没有朋友的土地瓜。"]
            return "\n".join(message_arr)
        # has friends, show list
        message_arr = [
            "【牛友列表】",
        ]
        # search friends info
        infos = cls.get_batch_friends_info_by_qqs(friends_list)
        for info in infos:
            index = infos.index(info)
            nickname = info.get("latest_speech_nickname")
            if not nickname:
                nickname = '无名英雄'
            cost_daily = info["friends_need_cost"]
            share_count = info["friends_share_count"]
            message_arr.append(
                f"{index + 1}. {nickname} ({share_count}人共享、朋友费{cost_daily}cm)"
            )
        return "\n".join(message_arr)

    @staticmethod
    def add_friends(qq: int, target_qq: int):
        # add friend to qq
        data = DB.sub_db_friends.get_user_data(qq)
        friends_list_str = data["friends_list"]
        friends_list = friends_list_str.split(
            ",") if len(friends_list_str) != 0 else []
        is_in_list = str(target_qq) in friends_list
        if not is_in_list:
            friends_list.append(str(target_qq))
        data["friends_list"] = ",".join(friends_list)
        # update pay time
        data["friends_cost_latest_time"] = ArrowUtil.get_now_time()
        DB.sub_db_friends.update_user_data(data)
        # add share count to target_qq
        target_data = DB.sub_db_friends.get_user_data(target_qq)
        target_data["friends_share_count"] += 1
        DB.sub_db_friends.update_user_data(target_data)

    @staticmethod
    def delete_friends(qq: int, target_qq: int):
        # remove target from qq
        data = DB.sub_db_friends.get_user_data(qq)
        friends_list_str = data["friends_list"]
        friends_list = friends_list_str.split(
            ",") if len(friends_list_str) != 0 else []
        is_in_list = str(target_qq) in friends_list
        if is_in_list:
            friends_list.remove(str(target_qq))
        data["friends_list"] = ",".join(friends_list)
        DB.sub_db_friends.update_user_data(data)
        # remove share count from target_qq
        target_data = DB.sub_db_friends.get_user_data(target_qq)
        target_data["friends_share_count"] -= 1
        DB.sub_db_friends.update_user_data(target_data)

    @classmethod
    def transfer_length(cls, target_qq: int, origin_length: float):
        config = cls.read_config()
        fee = config["fee"]["friends"]
        # transfer length to target
        will_transfer_length = origin_length * (1 - fee)
        data = DB.sub_db_friends.get_user_data(target_qq)
        data["friends_will_collect_length"] += will_transfer_length
        DB.sub_db_friends.update_user_data(data)

    @classmethod
    def check_friends_daily(cls, qq: int):
        """
        1. 注意朋友如果不上线（说话），长度不会自动转账，可以一直不说话跑路，上线那一天才会转账或友尽
        2. 朋友系统是懒支付，每天先说话的当天收益要到第二天才能领取，后说话的可以领先结算的人的收益
        """
        friends_data = cls.get_friends_data(qq)
        is_not_has_friends = len(friends_data["friends_list"]) == 0
        share_count = friends_data["friends_share_count"]
        is_not_share = share_count == 0
        if is_not_has_friends and is_not_share:
            return None
        # 收款额
        will_get_length = fixed_two_decimal_digits(
            friends_data["friends_will_collect_length"], to_number=True
        )
        # 有朋友，就有花费
        if not is_not_has_friends:
            latest_pay_time = friends_data["friends_cost_latest_time"]
            is_need_pay = ArrowUtil.is_date_outed(latest_pay_time)
            if not is_need_pay:
                return None
            else:
                # need pay
                infos = cls.get_batch_friends_info_by_qqs(
                    friends_data["friends_list"])
                origin_length = friends_data["length"] + will_get_length
                current_has_length = origin_length
                can_keep_friends_list = []
                friends_over_list = []
                # gap days
                now = ArrowUtil.get_now_time()
                gap_days = ArrowUtil.get_time_diff_days(now, latest_pay_time)
                # 由大到小支付
                for info in infos:
                    need_pay_length = gap_days * info["friends_need_cost"]
                    if current_has_length >= need_pay_length:
                        # can keep
                        can_keep_friends_list.append(info)
                        current_has_length -= need_pay_length
                    else:
                        # over
                        friends_over_list.append(info)
                total_need_cost_length = fixed_two_decimal_digits(
                    origin_length - current_has_length, to_number=True
                )
                income_text = ""
                if will_get_length > 0:
                    income_text = f"收入{will_get_length}cm"
                message_arr = [
                    join(
                        [
                            f"今日朋友费支出{total_need_cost_length}cm",
                            income_text,
                            "好幸福。"
                        ],
                        '，'
                    )
                ]
                profit = fixed_two_decimal_digits(
                    will_get_length - total_need_cost_length, to_number=True
                )
                # batch pay to every friend
                for info in can_keep_friends_list:
                    cls.transfer_length(info["qq"], info["friends_need_cost"])
                has_over_friends = len(friends_over_list) > 0
                if has_over_friends:
                    first_over_friend = friends_over_list[0]
                    nickname = first_over_friend.get("latest_speech_nickname")
                    if not nickname:
                        nickname = '无名英雄'
                    numbers = len(friends_over_list)
                    over_text = None
                    if numbers == 1:
                        over_text = f"{nickname}已取关你！"
                    else:
                        over_text = f"{nickname}等{numbers}人已取关你！"
                    message_arr.append(
                        f"“今天的朋友费...”，“土地瓜，还想白嫖我”，因为你付不起朋友费，{over_text}")
                    for info in friends_over_list:
                        target_qq = info["qq"]
                        # batch delete friends_list
                        is_in_list = target_qq in friends_data["friends_list"]
                        if is_in_list:
                            friends_data["friends_list"].remove(target_qq)
                        # batch delete friends share count
                        target_friends_data = DB.sub_db_friends.get_user_data(
                            target_qq)
                        target_friends_data["friends_share_count"] -= 1
                        DB.sub_db_friends.update_user_data(target_friends_data)
                # update latest pay time
                friends_data["friends_cost_latest_time"] = ArrowUtil.get_now_time()
                # clear friends_will_collect_length
                friends_data["friends_will_collect_length"] = 0
                # update latest collect time: 这个字段还没什么用，先保留着吧
                friends_data["friends_collect_latest_time"] = ArrowUtil.get_now_time()
                DB.sub_db_friends.update_user_data(friends_data)
                return {
                    "message": "\n".join(message_arr),
                    "profit": profit,  # > 0 or < 0
                }
        else:
            # 否则，检查有没有收入
            if will_get_length > 0:
                # update latest collect time
                friends_data["friends_collect_latest_time"] = ArrowUtil.get_now_time()
                # clear friends_will_collect_length
                friends_data["friends_will_collect_length"] = 0
                DB.sub_db_friends.update_user_data(friends_data)
                return {
                    "message": f"今日朋友费收入{will_get_length}cm，好幸福。",
                    "profit": will_get_length
                }
            else:
                return None

    @classmethod
    def handle_weighting(cls, qq: int, at_qq: int, length: float, source = OpFrom.OTHER):
        config = cls.read_config()
        addition = config['addition']
        # qq lock at_qq weighting
        if source == OpFrom.LOCK_WITH_TARGET:
            # check qq in at_qq friends list, then at_qq get extra length
            friends_data = cls.get_friends_data(at_qq)
            is_in_list = qq in friends_data["friends_list"]
            if is_in_list:
                qq_friends_data = cls.get_friends_data(qq)
                share_count = qq_friends_data["friends_share_count"]
                base_plus_percent = addition['lock_plus']['base']
                share_plus_percent = addition['lock_plus']['share'] * share_count
                total_plus_percent = base_plus_percent + share_plus_percent
                return length * (1 + total_plus_percent)
        # qq glue at_qq weighting
        # FIXME: 这里只对成功有加成，其实不好，大力出奇迹，应该失败也加倍失败
        if source == OpFrom.GLUE_WITH_TARGET_SUCCESS:
            # check qq in at_qq friends list, then at_qq get extra length
            friends_data = cls.get_friends_data(at_qq)
            is_in_list = qq in friends_data["friends_list"]
            if is_in_list:
                qq_friends_data = cls.get_friends_data(qq)
                share_count = qq_friends_data["friends_share_count"]
                base_plus_percent = addition['glue_plus']['base']
                share_plus_percent = addition['glue_plus']['share'] * share_count
                total_plus_percent = base_plus_percent + share_plus_percent
                return length * (1 + total_plus_percent)
        # qq pk at_qq weighting
        if source == OpFrom.PK_FROM_LENGTH:
            friends_data = cls.get_friends_data(qq)
            friends_list = friends_data["friends_list"]
            has_friends = len(friends_list) > 0
            if not has_friends:
                return length
            # 如果 pk 朋友，要剔除掉被 pk 的朋友，他不会帮你，更真实
            if at_qq in friends_list:
                friends_list.remove(at_qq)
            # weighting all friends
            infos = cls.get_batch_friends_info_by_qqs(friends_list)
            total_plus_length = 0
            base_plus_percent = addition['pk_plus']['base']
            share_plus_percent = addition['pk_plus']['share']
            for info in infos:
                share_count = info["friends_share_count"]
                total_plus_percent = base_plus_percent + share_plus_percent * share_count
                total_plus_length += info['length'] * total_plus_percent
            return length + total_plus_length
        return length
    