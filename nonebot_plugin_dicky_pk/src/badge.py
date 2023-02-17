from .config import Config
from .db import DB
from .badge_parser import BadgeSystem_Parser
from .constants import OpFrom

cache = None


class BadgeSystem:

    parser = BadgeSystem_Parser()

    @classmethod
    def normalize_config(cls, config: dict):
        # normalize condition
        origin_condition = config["condition"]
        condition = {}
        # filter start with '##' key
        for key in origin_condition:
            if key.startswith("##"):
                continue
            value = origin_condition[key]
            # not need empty string
            if not value:
                continue
            # ensure array
            if not isinstance(value, list):
                value = [value]
            check_funs = []
            for expr in value:
                new_func = cls.parser.create_expr_func(expr)
                check_funs.append(new_func)

            # See https://blog.csdn.net/weixin_34082376/article/details/90551457
            def func_creater(funcs: list):
                def inner(left: int):
                    for i in funcs:
                        if not i(left):
                            return False
                    return True

                return inner

            condition[key] = func_creater(funcs=check_funs)
        # check condition cannot be empty dict
        if not condition:
            raise Exception("成就获取条件不能为空，至少要有一个条件！")
        config["condition"] = condition

        # normalize addition
        origin_addition = config["addition"]
        addition = {}
        for key in origin_addition:
            if key.startswith("##"):
                continue
            value = origin_addition[key]
            # not need empty string
            if not value:
                continue
            # ensure array
            if not isinstance(value, list):
                value = [value]
            weighting_funs = []
            for expr in value:
                weighting_funs.append(cls.parser.create_weighting_func(expr))

            def func_creater(funcs: list):
                def inner(left: int):
                    sum = 0
                    for i in funcs:
                        sum += i(left)
                    return left + sum

                return inner

            addition[key] = func_creater(funcs=weighting_funs)
        config["addition"] = addition
        # 成就可以仅仅是名义上的，没有加成效果
        return config

    @classmethod
    def get_badge_configs(cls):
        global cache
        if cache is None:
            configs = Config.get_config("badge")["categories"]
            # make id to value map
            map = {}
            for config in configs:
                map[config["id"]] = cls.normalize_config(config)
            cache = map
        return cache

    @classmethod
    def parse_badge_ids(cls, user_badge_data: dict):
        ids_str_arr = user_badge_data.get("badge_ids", "").split(",")
        if not ids_str_arr:
            return []
        ids = [int(i) for i in ids_str_arr if i]
        configs = cls.get_badge_configs()
        badge_arr = []
        for id in ids:
            badge_arr.append(configs[id])
        # sort bt priority desc
        badge_arr.sort(key=lambda x: x["priority"], reverse=True)
        return badge_arr

    @classmethod
    def get_badge_by_qq(cls, qq: int):
        badge_data = DB.sub_db_badge.get_badge_data(qq)
        if not badge_data:
            return None
        return cls.parse_badge_ids(badge_data)

    @classmethod
    def get_badge_label_by_qq(cls, qq: int):
        badge_arr = cls.get_badge_by_qq(qq)
        if not badge_arr:
            return None
        badge_names = [i["name"] for i in badge_arr]
        return "、".join(badge_names)

    @classmethod
    def get_first_badge_by_badge_string_arr(cls, bade_ids: str = None):
        """
        "1,2,3" -> "xxx"
        """
        if not bade_ids:
            return None
        ids_str_arr = bade_ids.split(",")
        ids = [int(i) for i in ids_str_arr if i]
        configs = cls.get_badge_configs()
        max_priority_badge = None
        for id in ids:
            badge = configs[id]
            if (max_priority_badge is None) or (
                badge["priority"] > max_priority_badge["priority"]
            ):
                max_priority_badge = badge
        return max_priority_badge["name"]

    @classmethod
    def get_badge_view(cls, qq: int):
        badge_arr = cls.get_badge_by_qq(qq)
        if not badge_arr:
            return None
        arr = []
        for badge in badge_arr:
            index = badge_arr.index(badge)
            arr.append(f"{index + 1}. 【{badge['name']}】：{badge['description']}")
        return "\n".join(arr)

    @classmethod
    def check_whether_get_new_badge(cls, qq: int):
        user_badge_data = DB.sub_db_badge.get_badge_data(qq)
        if not user_badge_data:
            return None
        configs = cls.get_badge_configs()
        badges = list(configs.values())
        will_get_badges = []
        for badge in badges:
            condition = badge["condition"]
            # check all condition are true
            is_fufilled = True
            for key in condition:
                if condition[key](user_badge_data[key]):
                    is_fufilled = True
                else:
                    is_fufilled = False
                    break
            if is_fufilled:
                will_get_badges.append(badge)
        current_has_badges = cls.parse_badge_ids(user_badge_data)
        current_has_badges_id = [i["id"] for i in current_has_badges]
        current_not_has_badges = []
        for badge in will_get_badges:
            badge_id = badge["id"]
            if badge_id not in current_has_badges_id:
                current_not_has_badges.append(badge)
        if not current_not_has_badges:
            return None
        # change database
        new_badge_ids = [str(i["id"]) for i in current_not_has_badges]
        badge_ids = ",".join(new_badge_ids)
        DB.sub_db_badge.update_badge_ids(qq, badge_ids)
        # return msg
        new_badge_names = [i["name"] for i in current_not_has_badges]
        beatify_names = [f"【{i}】" for i in new_badge_names]
        msg = f"🎉恭喜你获得新成就：{'、'.join(beatify_names)}"
        return msg

    @classmethod
    def handle_weighting_by_qq(cls, qq: int, length: float, source: str = OpFrom.OTHER):
        badge_arr = cls.get_badge_by_qq(qq)
        if not badge_arr:
            return length
        for badge in badge_arr:
            addition = badge["addition"]
            # lock weighting
            lock_weight_fun = addition.get("lock_weight")
            if lock_weight_fun and OpFrom.is_lock(source):
                length = lock_weight_fun(length)
            # glue weighting
            glue_weight_fun = addition.get("glue_weight")
            if glue_weight_fun and OpFrom.is_glue(source):
                length = glue_weight_fun(length)
            # pk weighting
            pk_weight_fun = addition.get("pk_weight")
            if pk_weight_fun and OpFrom.is_pk(source):
                length = pk_weight_fun(length)
        return length
