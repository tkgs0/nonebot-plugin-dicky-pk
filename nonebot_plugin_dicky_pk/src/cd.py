from .db import DB
from .config import Config
from .utils import ArrowUtil


class CD_Check:
    @staticmethod
    def is_lock_in_cd(qq: int):
        user_data = DB.load_data(qq)
        current_total_lock_count = user_data["daily_lock_count"]
        max = Config.get_config("lock_daily_max")
        rate = Config.get_config("cd_trigger_lock_rate")
        is_count_in_cd = current_total_lock_count > (max * rate)
        if not is_count_in_cd:
            return False
        latest_lock_time = user_data["latest_daily_lock"]
        time_gap_mins = ArrowUtil.get_arrow_gap_minutes(
            ArrowUtil.get_now_time(), latest_lock_time
        )
        is_time_in_cd = time_gap_mins < Config.get_config("cd_trigger_lock_time")
        if not is_time_in_cd:
            return False
        return True

    @staticmethod
    def is_glue_in_cd(qq: int):
        user_data = DB.load_data(qq)
        current_total_glue_count = user_data["daily_glue_count"]
        max = Config.get_config("glue_daily_max")
        rate = Config.get_config("cd_trigger_glue_rate")
        is_count_in_cd = current_total_glue_count > (max * rate)
        if not is_count_in_cd:
            return False
        latest_glue_time = user_data["latest_daily_glue"]
        time_gap_mins = ArrowUtil.get_arrow_gap_minutes(
            ArrowUtil.get_now_time(), latest_glue_time
        )
        is_time_in_cd = time_gap_mins < Config.get_config("cd_trigger_glue_time")
        if not is_time_in_cd:
            return False
        return True

    @staticmethod
    def is_pk_in_cd(qq: int):
        user_data = DB.load_data(qq)
        current_total_pk_count = user_data["daily_pk_count"]
        max = Config.get_config("pk_daily_max")
        rate = Config.get_config("cd_trigger_pk_rate")
        is_count_in_cd = current_total_pk_count > (max * rate)
        if not is_count_in_cd:
            return False
        latest_pk_time = user_data["latest_daily_pk"]
        time_gap_mins = ArrowUtil.get_arrow_gap_minutes(
            ArrowUtil.get_now_time(), latest_pk_time
        )
        is_time_in_cd = time_gap_mins < Config.get_config("cd_trigger_pk_time")
        if not is_time_in_cd:
            return False
        return True
