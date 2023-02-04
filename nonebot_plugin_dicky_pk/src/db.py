from pathlib import Path
from .utils import get_now_time, is_date_outed, fixed_two_decimal_digits
from .config import Config
import sqlite3

sql_ins = None


class Paths():
    @staticmethod
    def base_db_path_v1():
        return Path() / 'data' / 'chinchin_pk' / 'data'

    @staticmethod
    def base_db_dir():
        _file = Path() / 'data' / 'chinchin_pk' / 'data-v2'
        _file.mkdir(parents=True, exist_ok=True)
        return _file

    @classmethod
    def sqlite_path(cls):
        return cls.base_db_dir() / 'data.sqlite'


class MigrationHelper():
    @staticmethod
    def old_data_check():
        # check old v1 data exist and tip
        if Paths.base_db_path_v1().exists:
            print(
                '[Chinchin::Deprecated]: 目录 src/data-v2 新数据已经初始化，旧 v1 版本数据 src/data 已经不再使用，可以备份后手动删除！')
            print(
                '[Chinchin::Deprecated]: 若使用了 scripts/database_migrate_python/migrate.py 备份脚本，默认会备份到 src/data-v1-backup 下面')


class Sql_UserInfo():
    @staticmethod
    def _empty_data_handler(data: dict):
        if data["latest_speech_nickname"] is None:
            data['latest_speech_nickname'] = ''
        return data

    @staticmethod
    def _sql_create_table():
        return 'create table if not exists `info` (`qq` bigint, `latest_speech_nickname` varchar(255), `latest_speech_group` bigint, primary key (`qq`));'

    @classmethod
    def _sql_insert_single_data(cls, data: dict):
        data = cls._empty_data_handler(data)
        return f'insert into `info` (`latest_speech_group`, `latest_speech_nickname`, `qq`) values (:latest_speech_group, :latest_speech_nickname, {data["qq"]});'

    @staticmethod
    def _sql_select_single_data(qq: int):
        return f'select * from `info` where `qq` = {qq};'

    @staticmethod
    def _sql_check_table_exists():
        return 'select count(*) from sqlite_master where type = "table" and name = "info";'

    @classmethod
    def _sql_update_single_data(cls, data: dict):
        data = cls._empty_data_handler(data)
        return f'update `info` set `latest_speech_nickname` = :latest_speech_nickname, `latest_speech_group` = :latest_speech_group where `qq` = {data["qq"]};'

    @staticmethod
    def _sql_batch_select_data(qqs: list):
        return f'select * from `info` where `qq` in {tuple(qqs)};'

    @staticmethod
    def _sql_delete_single_data(qq: int):
        return f'delete from `info` where `qq` = {qq};'

    @staticmethod
    def deserialize(data: tuple):
        return {
            'qq': data[0],
            'latest_speech_nickname': data[1],
            'latest_speech_group': data[2],
        }

    @classmethod
    def select_batch_data_by_qqs(cls, qqs: list):
        sql_ins.cursor.execute(cls._sql_batch_select_data(qqs))
        return [cls.deserialize(data) for data in sql_ins.cursor.fetchall()]

    @classmethod
    def delete_single_data(cls, qq: int):
        sql_ins.cursor.execute(cls._sql_delete_single_data(qq))
        sql_ins.conn.commit()


class Sql():

    sub_table_info = Sql_UserInfo()

    def __init__(self):
        self.sqlite_path = Paths.sqlite_path()
        self.conn = sqlite3.connect(self.sqlite_path)
        self.cursor = self.conn.cursor()

    @staticmethod
    def __sql_create_table():
        return 'create table if not exists `users` (`qq` bigint, `length` float, `daily_lock_count` integer, `daily_pk_count` integer, `daily_glue_count` integer, `register_time` varchar(255), `latest_daily_lock` varchar(255), `latest_daily_pk` varchar(255), `latest_daily_glue` varchar(255), `pk_time` varchar(255), `pked_time` varchar(255), `glueing_time` varchar(255), `glued_time` varchar(255), `locked_time` varchar(255), primary key (`qq`));'

    @staticmethod
    def __sql_insert_single_data(data: dict):
        return f'insert into `users` (`daily_glue_count`, `daily_lock_count`, `daily_pk_count`, `glued_time`, `glueing_time`, `latest_daily_glue`, `latest_daily_lock`, `latest_daily_pk`, `length`, `locked_time`, `pk_time`, `pked_time`, `qq`, `register_time`) values ({data["daily_glue_count"]}, {data["daily_lock_count"]}, {data["daily_pk_count"]}, "{data["glued_time"]}", "{data["glueing_time"]}", "{data["latest_daily_glue"]}", "{data["latest_daily_lock"]}", "{data["latest_daily_pk"]}", {data["length"]}, "{data["locked_time"]}", "{data["pk_time"]}", "{data["pked_time"]}", {data["qq"]}, "{data["register_time"]}");'

    @staticmethod
    def __sql_select_single_data(qq: int):
        return f'select * from `users` where `qq` = {qq};'

    @staticmethod
    def __sql_check_table_exists():
        return 'select count(*) from sqlite_master where type = "table" and name = "users";'

    @staticmethod
    def __sql_update_single_data(data: dict):
        return f'update `users` set `length` = {data["length"]}, `register_time` = "{data["register_time"]}", `daily_lock_count` = {data["daily_lock_count"]}, `daily_pk_count` = {data["daily_pk_count"]}, `daily_glue_count` = {data["daily_glue_count"]}, `latest_daily_lock` = "{data["latest_daily_lock"]}", `latest_daily_pk` = "{data["latest_daily_pk"]}", `latest_daily_glue` = "{data["latest_daily_glue"]}", `pk_time` = "{data["pk_time"]}", `pked_time` = "{data["pked_time"]}", `glueing_time` = "{data["glueing_time"]}", `glued_time` = "{data["glued_time"]}", `locked_time` = "{data["locked_time"]}" where `qq` = {data["qq"]};'

    @staticmethod
    def __sql_get_data_counts():
        return 'select count(*) from `users`;'

    @staticmethod
    def __sql_order_by_length():
        max = Config.get_config('ranking_list_length')
        return f'select * from `users` order by `length` desc limit {max};'

    @classmethod
    def get_top_users(cls) -> list:
        sql_ins.cursor.execute(cls.__sql_order_by_length())
        some = sql_ins.cursor.fetchall()
        if not some:
            return None
        return [cls.deserialize(one) for one in some]

    @classmethod
    def get_data_counts(cls) -> int:
        sql_ins.cursor.execute(cls.__sql_get_data_counts())
        one = sql_ins.cursor.fetchone()
        return one[0]

    @classmethod
    def insert_single_data(cls, data: dict):
        sql_ins.cursor.execute(cls.__sql_insert_single_data(data))
        sql_ins.conn.commit()

    @staticmethod
    def deserialize(one: tuple):
        return {
            'qq': one[0],
            'length': one[1],
            'daily_lock_count': one[2],
            'daily_pk_count': one[3],
            'daily_glue_count': one[4],
            'register_time': one[5],
            'latest_daily_lock': one[6],
            'latest_daily_pk': one[7],
            'latest_daily_glue': one[8],
            'pk_time': one[9],
            'pked_time': one[10],
            'glueing_time': one[11],
            'glued_time': one[12],
            'locked_time': one[13]
        }

    @classmethod
    def select_data_by_qq(cls, qq: int):
        sql_ins.cursor.execute(cls.__sql_select_single_data(qq))
        one = sql_ins.cursor.fetchone()
        if one is None:
            return None
        return cls.deserialize(one)

    @classmethod
    def check_table_exists(cls):
        # users table exists
        sql_ins.cursor.execute(cls.__sql_check_table_exists())
        one = sql_ins.cursor.fetchone()
        is_table_exists = one[0] == 1
        if not is_table_exists:
            sql_ins.cursor.execute(sql_ins.__sql_create_table())
            sql_ins.conn.commit()
        # info table exists
        sql_ins.cursor.execute(cls.sub_table_info._sql_check_table_exists())
        one = sql_ins.cursor.fetchone()
        is_table_exists = one[0] == 1
        if not is_table_exists:
            sql_ins.cursor.execute(cls.sub_table_info._sql_create_table())
            sql_ins.conn.commit()

    @classmethod
    def update_data_by_qq(cls, data: dict):
        sql_ins.cursor.execute(cls.__sql_update_single_data(data))
        sql_ins.conn.commit()

    @staticmethod
    def init_database():
        global sql_ins
        if sql_ins:
            return sql_ins
        if not Paths.sqlite_path().is_file():
            open(Paths.sqlite_path(), 'w').close()
        sql_ins = Sql()
        sql_ins.check_table_exists()
        MigrationHelper.old_data_check()
        return sql_ins

    def destroy(self):
        self.conn.close()


class DB_UserInfo():
    @staticmethod
    def is_user_exists(qq: int):
        sql_ins.cursor.execute(Sql.sub_table_info._sql_select_single_data(qq))
        return sql_ins.cursor.fetchone() is not None

    @classmethod
    def record_user_info(cls, qq: int, data: dict):
        data["qq"] = qq
        is_exists = cls.is_user_exists(qq)
        if is_exists:
            sql_ins.cursor.execute(
                Sql.sub_table_info._sql_update_single_data(data), data)
        else:
            sql_ins.cursor.execute(
                Sql.sub_table_info._sql_insert_single_data(data), data)
        sql_ins.conn.commit()


class DataUtils():
    @staticmethod
    def __assign(data_1: dict, data_2: dict):
        return {**data_1, **data_2}

    @staticmethod
    def __make_qq_to_data_map(data: list):
        return {one['qq']: one for one in data}

    @classmethod
    def merge_data(cls, datas: list):
        maps = [cls.__make_qq_to_data_map(one) for one in datas]
        for key in maps[0].keys():
            for i in range(1, len(maps)):
                if key in maps[i]:
                    maps[0][key] = cls.__assign(maps[0][key], maps[i][key])
        result = []
        for user in datas[0]:
            result.append(maps[0][user['qq']])
        return result


class DB():

    sub_db_info = DB_UserInfo()
    utils = DataUtils()

    @staticmethod
    def create_data(data: dict):
        Sql.insert_single_data(data)

    @staticmethod
    def load_data(qq: int):
        return Sql.select_data_by_qq(qq)

    @classmethod
    def is_registered(cls, qq: int):
        return cls.load_data(qq) is not None

    @classmethod
    def write_data(cls, data: dict):
        Sql.update_data_by_qq(data)

    @staticmethod
    def get_data_counts():
        return Sql.get_data_counts()

    @classmethod
    def length_increase(cls, qq: int, length: float):
        user_data = cls.load_data(qq)
        user_data['length'] += length
        # ensure fixed 2
        user_data['length'] = fixed_two_decimal_digits(
            user_data['length'], to_number=True)
        cls.write_data(user_data)

    @classmethod
    def length_decrease(cls, qq: int, length: float):
        user_data = cls.load_data(qq)
        user_data['length'] -= length
        # ensure fixed 2
        user_data['length'] = fixed_two_decimal_digits(
            user_data['length'], to_number=True)
        # TODO: 禁止负值，更好的提示
        if user_data['length'] < 0:
            user_data['length'] = 0
        cls.write_data(user_data)

    @classmethod
    def record_time(cls, qq: int, key: str):
        user_data = cls.load_data(qq)
        user_data[key] = get_now_time()
        cls.write_data(user_data)

    @classmethod
    def reset_daily_count(cls, qq: int, key: str):
        user_data = cls.load_data(qq)
        user_data[key] = 0
        cls.write_data(user_data)

    @classmethod
    def is_lock_daily_limited(cls, qq: int):
        user_data = cls.load_data(qq)
        current_count = user_data['daily_lock_count']
        is_outed = is_date_outed(user_data['latest_daily_lock'])
        if is_outed:
            cls.reset_daily_count(qq, 'daily_lock_count')
            return False
        max = Config.get_config('lock_daily_max')
        if current_count >= max:
            return True
        return False

    @classmethod
    def count_lock_daily(cls, qq: int):
        user_data = cls.load_data(qq)
        user_data['daily_lock_count'] += 1
        user_data['latest_daily_lock'] = get_now_time()
        cls.write_data(user_data)

    @classmethod
    def is_glue_daily_limited(cls, qq: int):
        user_data = cls.load_data(qq)
        current_count = user_data['daily_glue_count']
        is_outed = is_date_outed(user_data['latest_daily_glue'])
        if is_outed:
            cls.reset_daily_count(qq, 'daily_glue_count')
            return False
        max = Config.get_config('glue_daily_max')
        if current_count >= max:
            return True
        return False

    @classmethod
    def count_glue_daily(cls, qq: int):
        user_data = cls.load_data(qq)
        user_data['daily_glue_count'] += 1
        user_data['latest_daily_glue'] = get_now_time()
        cls.write_data(user_data)

    @classmethod
    def is_pk_daily_limited(cls, qq: int):
        user_data = cls.load_data(qq)
        current_count = user_data['daily_pk_count']
        is_outed = is_date_outed(user_data['latest_daily_pk'])
        if is_outed:
            cls.reset_daily_count(qq, 'daily_pk_count')
            return False
        max = Config.get_config('pk_daily_max')
        if current_count >= max:
            return True
        return False

    @classmethod
    def count_pk_daily(cls, qq: int):
        user_data = cls.load_data(qq)
        user_data['daily_pk_count'] += 1
        user_data['latest_daily_pk'] = get_now_time()
        cls.write_data(user_data)

    @classmethod
    def is_pk_protected(cls, qq: int):
        user_data = cls.load_data(qq)
        min_length = Config.get_config('pk_guard_chinchin_length')
        if user_data['length'] <= min_length:
            return True
        return False

    @staticmethod
    def get_top_users():
        top_users = Sql.get_top_users()
        qqs = [one["qq"] for one in top_users]
        info_list = Sql.sub_table_info.select_batch_data_by_qqs(qqs)
        merged = DB.utils.merge_data([top_users, info_list])
        return merged


def lazy_init_database():
    Sql.init_database()
