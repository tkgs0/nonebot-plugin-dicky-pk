
class OpFrom():

    PK = 'pk_weight'
    PK_WIN = 'pk_win_weight'
    PK_LOSE = 'pk_lose_weight'

    LOCK = 'lock_weight'
    LOCK_ME = 'lock_me_weight'
    LOCK_WITH_TARGET = 'lock_with_target_weight'

    GLUE = 'glue_weight'
    GLUE_ME = 'glue_me_weight'
    GLUE_WITH_TARGET = 'glue_with_target_weight'

    OTHER = 'other_weight'

    @classmethod
    def is_lock(cls, op = None):
        return op in [cls.LOCK, cls.LOCK_ME, cls.LOCK_WITH_TARGET]

    @classmethod
    def is_glue(cls, op = None):
        return op in [cls.GLUE, cls.GLUE_ME, cls.GLUE_WITH_TARGET]
    
    @classmethod
    def is_pk(cls, op = None):
        return op in [cls.PK, cls.PK_WIN, cls.PK_LOSE]
        