class OpFrom:

    PK = "pk_weight"
    PK_WIN = "pk_win_weight"
    PK_LOSE = "pk_lose_weight"

    LOCK = "lock_weight"
    LOCK_ME = "lock_me_weight"
    LOCK_WITH_TARGET = "lock_with_target_weight"

    GLUE = "glue_weight"
    GLUE_ME = "glue_me_weight"
    GLUE_WITH_TARGET = "glue_with_target_weight"

    FARM_OVER = "farm_over_weight"

    OTHER = "other_weight"

    @classmethod
    def is_lock(cls, op=None):
        return op in [cls.LOCK, cls.LOCK_ME, cls.LOCK_WITH_TARGET]

    @classmethod
    def is_glue(cls, op=None):
        return op in [cls.GLUE, cls.GLUE_ME, cls.GLUE_WITH_TARGET]

    @classmethod
    def is_pk(cls, op=None):
        return op in [cls.PK, cls.PK_WIN, cls.PK_LOSE]


class FarmConst:

    status_empty = "empty"
    status_planting = "planting"

    @classmethod
    def is_planting(cls, status=None):
        return status == cls.status_planting

    @classmethod
    def is_empty(cls, status=None):
        return status == cls.status_empty


class TimeConst:

    DEFAULT_NONE_TIME = "2000-01-01 00:00:00"
