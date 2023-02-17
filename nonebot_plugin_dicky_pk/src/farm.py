from .config import Config
from .db import DB
from .constants import FarmConst, TimeConst
from .utils import ArrowUtil

cache = None


class FarmSystem:
    @staticmethod
    def read_farm_config():
        global cache
        if cache:
            return cache
        configs = Config.get_config("farm")
        # transform duration
        configs["can_play_time"]["duration"] = Config.sub_parser_time.parse_time_string(
            configs["can_play_time"]["duration"]
        )
        # transform cost
        cost = configs["cost"]
        for i in range(len(cost)):
            value = cost[i]
            value["time"] = Config.sub_parser_time.parse_time_string(value["time"])
            cost[i] = value
        # sort by time h
        cost = sorted(cost, key=lambda x: x["time"]["h"])
        configs["cost"] = cost
        # cache
        cache = configs
        return cache

    @staticmethod
    def modify_config_in_runtime(config: dict):
        global cache
        cache = config

    @classmethod
    def is_current_can_play(cls):
        config = cls.read_farm_config()
        start_time = ArrowUtil.complete_date_with_today_from_h_s(
            config["can_play_time"]["start"]
        )
        duration = config["can_play_time"]["duration"]
        total_duration_minutes = duration["h"] * 60 + duration["m"]
        end_time = ArrowUtil.get_time_with_shift(
            time=start_time, shift_mins=total_duration_minutes
        )
        is_can_play = ArrowUtil.is_now_in_time_range(start=start_time, end=end_time)
        return is_can_play

    @classmethod
    def is_current_planting(cls, qq: int):
        data = DB.sub_db_farm.get_user_data(qq)
        status = data["farm_status"]
        # 检查过期
        is_empty = FarmConst.is_empty(status)
        if is_empty:
            return False
        latest_plant_time = data["farm_latest_plant_time"]
        need_time = data["farm_need_time"]  # minutes
        end_time = ArrowUtil.get_time_with_shift(
            time=latest_plant_time, shift_mins=need_time
        )
        now = ArrowUtil.get_now_time()
        is_plant_over = ArrowUtil.lt(time_1=end_time, time_2=now)
        if is_plant_over:
            return False
        return True

    @staticmethod
    def reset_user_data(qq: int):
        data = DB.sub_db_farm.get_user_data(qq)
        data["farm_status"] = FarmConst.status_empty
        data["farm_need_time"] = 0
        data["farm_expect_get_length"] = 0
        DB.sub_db_farm.update_user_data(data)

    @classmethod
    def get_reward_length(cls, qq: int):
        config = cls.read_farm_config()
        reward = config["reward"]
        min = reward["min"]
        max = reward["max"]
        base = reward["base"]
        user_data = DB.load_data(qq)
        length = user_data["length"]
        result = Config.random_value(min, max) * length + base
        return result

    @classmethod
    def start_plant(cls, qq: int):
        data = DB.sub_db_farm.get_user_data(qq)
        # change status
        data["farm_status"] = FarmConst.status_planting
        # change latest plant time
        data["farm_latest_plant_time"] = ArrowUtil.get_now_time()
        # change count
        data["farm_count"] += 1
        # change need time
        # TODO: 现在花费时间是固定的，以后可以根据一些设定有不同修炼时间
        config = cls.read_farm_config()
        need_time = config["cost"][-1]["time"]
        need_time_minutes = need_time["h"] * 60 + need_time["m"]
        data["farm_need_time"] = need_time_minutes
        # 预期收益在开始的时候就知道了，因为后续可能被偷取
        data["farm_expect_get_length"] = cls.get_reward_length(qq)
        # update
        DB.sub_db_farm.update_user_data(data)
        return {
            "need_time_minutes": need_time_minutes,
        }

    @classmethod
    def get_current_status(cls, spent_time: int):
        config = cls.read_farm_config()
        current_status_idx = 0
        cost = config["cost"]
        for i in range(len(cost)):
            if i == 0:
                first_time = cost[i]["time"]
                first_time_minutes = first_time["h"] * 60 + first_time["m"]
                if spent_time <= first_time_minutes:
                    current_status_idx = i
                    break
                continue
            # current
            time = cost[i]["time"]
            time_minutes = time["h"] * 60 + time["m"]
            # prev
            prev_idx = i - 1
            prev_time = cost[prev_idx]["time"]
            prev_time_minutes = prev_time["h"] * 60 + prev_time["m"]
            # > prev and <= current
            if spent_time > prev_time_minutes and spent_time <= time_minutes:
                current_status_idx = i
                break
        return cost[current_status_idx]

    @classmethod
    def get_farm_view(cls, qq: int):
        data = DB.sub_db_farm.get_user_data(qq)
        is_current_planting = FarmConst.is_planting(data["farm_status"])
        latest_time = data["farm_latest_plant_time"]
        if not is_current_planting:
            status_text = "未修炼"
        else:
            now = ArrowUtil.get_now_time()
            spent_time = ArrowUtil.calc_diff_minutes(time_1=now, time_2=latest_time)
            total_need_time = data["farm_need_time"]
            current_status = cls.get_current_status(spent_time)
            remain_time = int(total_need_time - spent_time)
            status_text = (
                f'{current_status["status"]}，已修炼{spent_time}分钟，剩余{remain_time}分钟'
            )
        count = data["farm_count"]
        message_arr = [
            "【牛子仙境】",
            f"阶段：{status_text}",
            f"修炼次数：{count}次",
        ]
        if latest_time != TimeConst.DEFAULT_NONE_TIME:
            message_arr.append(
                f"上次修炼时间：{ArrowUtil.date_improve(latest_time)}",
            )
        return "\n".join(message_arr)
