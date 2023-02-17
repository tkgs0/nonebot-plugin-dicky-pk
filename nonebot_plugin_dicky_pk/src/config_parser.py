class TimeParser:
    @staticmethod
    def parse_date_string(text: str):
        """
        10:00 -> { h: 10, m: 0 }
        """
        has_colon = ":" in text
        if not has_colon:
            raise Exception("Time format error, example: 10:00, 10:20 ", text)
        result = text.strip().split(":")
        h = int(result[0].strip())
        m = int(result[1].strip())
        # check range
        # 0 <= h <= 23
        # 0 <= m <= 59
        if h < 0 or h > 23:
            raise Exception(
                "Time format error, hour must be 0-23 , example: 00:00, 23:59 ", text
            )
        if m < 0 or m > 59:
            raise Exception(
                "Time format error, minute must be 0-59 , example: 00:00, 23:59 ", text
            )
        return {"h": h, "m": m}

    @staticmethod
    def parse_time_string(text: str):
        """
        目前支持 Ahbm 的格式
        1h2m -> { h: 1, m: 2 }
        """
        h = 0
        m = 0
        result = text.strip().split("h")
        # 1m -> ['1m']
        if len(result) == 1:
            result = result[0].split("m")
            if len(result) != 2:
                raise Exception("Time format error, example: 1h2m, 1h, 2h ", text)
            m = int(result[0].strip())
            return {"h": h, "m": m}
        # 1h -> ['1', '']
        elif len(result) == 2:
            has_m = "m" in result[1]
            if not has_m:
                h = int(result[0].strip())
                return {"h": h, "m": m}
            # 1h2m -> ['1', '2m']
            h = int(result[0].strip())
            result = result[1].split("m")
            if len(result) != 2:
                raise Exception("Time format error, example: 1h2m, 1h, 2h ", text)
            m = int(result[0].strip())
            return {"h": h, "m": m}
        else:
            raise Exception("Time format error, example: 1h2m, 1h, 2h ", text)
