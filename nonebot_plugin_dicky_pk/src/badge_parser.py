TOKEN = {
    "gt": ">",
    "gt_eq": ">=",
}


class BadgeSystem_Parser:
    @staticmethod
    def create_expr_func(expr: str):
        # gt_eq
        # FIXME: 必须先判断长的，否则就命中短的了
        if TOKEN["gt_eq"] in expr:
            right = expr.split(TOKEN["gt_eq"])[1].strip()
            right_num = float(right)
            return lambda left: left >= right_num
        # gt
        if TOKEN["gt"] in expr:
            right = expr.split(TOKEN["gt"])[1].strip()
            right_num = float(right)
            return lambda left: left > right_num
        raise Exception("表达式不合法，不支持的运算符：{}".format(expr))

    @staticmethod
    def create_weighting_func(expr: str):
        # is number
        is_number = isinstance(expr, int) or isinstance(expr, float)
        if is_number:
            # plus
            return lambda _: expr
        # has '%'
        has_percent = "%" in expr
        if has_percent:
            # percent
            percent = float(expr.strip().replace("%", ""))
            return lambda left: left * (percent / 100)
        raise Exception("表达式不合法，不支持的运算符：{}".format(expr))
