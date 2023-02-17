from .db import DB
from .config import Config
from .rebirth_view import RebirthSystem_View


class RebirthSystem:

    view = RebirthSystem_View()

    @staticmethod
    def calc_failed_info(level: dict):
        is_failed = Config.is_hit_with_rate(level["fail_prob"])
        failed_punish_length = 0
        if is_failed:
            failed_punish_length = Config.random_value(
                level["fail_negative_min"], level["fail_negative_max"]
            )
        return {
            "is_failed": is_failed,
            "failed_punish_length": failed_punish_length,
        }

    @classmethod
    def get_rebirth_info(cls, qq: int):
        user = DB.load_data(qq)
        rebirth_info = DB.sub_db_rebirth.get_rebirth_data(qq)
        rebirth_config = cls.view.get_rebirth_config()
        if rebirth_info is None:
            first_level_info = rebirth_config[0]
            min_rebirth_length = first_level_info["acc_need_length"]
            if user["length"] < min_rebirth_length:
                return {
                    "can_rebirth": False,
                }
            failed_info = cls.calc_failed_info(first_level_info)
            return {
                "can_rebirth": True,
                "current_level_info": None,
                "next_level_info": first_level_info,
                "failed_info": failed_info,
            }
        else:
            current_level = rebirth_info["level"]
            max_level_info = rebirth_config[-1]
            if current_level == max_level_info["level"]:
                return {
                    "can_rebirth": False,
                }
            # find current level index in array
            current_level_idx = 0
            for i in range(len(rebirth_config)):
                if rebirth_config[i]["level"] == current_level:
                    current_level_idx = i
                    break
            next_level_info = rebirth_config[current_level_idx + 1]
            if user["length"] < next_level_info["acc_need_length"]:
                return {
                    "can_rebirth": False,
                }
            failed_info = cls.calc_failed_info(next_level_info)
            return {
                "can_rebirth": True,
                "current_level_info": rebirth_config[current_level_idx],
                "next_level_info": next_level_info,
                "failed_info": failed_info,
            }

    @classmethod
    def get_weight_by_qq(cls, qq: int):
        user = DB.load_data(qq)
        level = user.get("level")
        if level is None:
            return 1
        configs = cls.view.get_rebirth_config()
        current_level_info = None
        for config in configs:
            if config["level"] == level:
                current_level_info = config
                break
        return current_level_info["weight"]
