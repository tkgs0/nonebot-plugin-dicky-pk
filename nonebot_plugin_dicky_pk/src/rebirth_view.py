from .config import Config


class RebirthSystem_View:
    @staticmethod
    def get_rebirth_config():
        config = Config.get_config("rebirth")
        levels = config["levels"]
        # sort by level
        levels = sorted(levels, key=lambda x: x["level"])
        # calc acc need length
        for i in range(len(levels)):
            current_level_cost_length = levels[i]["cost_length"]
            if i == 0:
                levels[i]["acc_need_length"] = current_level_cost_length
            else:
                prev_level_acc_need_length = levels[i - 1]["acc_need_length"]
                levels[i]["acc_need_length"] = (
                    current_level_cost_length + prev_level_acc_need_length
                )
        return levels

    @classmethod
    def get_rebirth_view_by_level(cls, level: int, length: int):
        rebirth_config = cls.get_rebirth_config()
        for level_info in rebirth_config:
            if level_info["level"] == level:
                pure_length = length - level_info["acc_need_length"]
                return {
                    "current_level_info": level_info,
                    "pure_length": pure_length,
                }
        # impossible: throw exception
        raise Exception("level not found: 当你看到这个错误时，说明你的转生数据库和配置间出现了 level 匹配差错")
