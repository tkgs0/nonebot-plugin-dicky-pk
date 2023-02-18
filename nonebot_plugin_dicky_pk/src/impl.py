"""
TODO：实际接入的时候，需要实现的消息对接函数
"""

'''
def get_at_segment(qq: int):
    """
    如果 at 会风控，可以用昵称/群昵称代替，也可以返回 None 不实现
    """
    # return '{}'.format(qq)
    # return 'nickname: '
    return None


def send_message(qq: int, group: int, message: str):
    # print('send_message({}, {}, {})'.format(qq, group, message))
    print(message)
'''


import asyncio
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageSegment,
)


def get_at_segment(qq: int):
    return f'{MessageSegment.at(qq)}'


def send_message(bot: Bot, qq: int, group: int, message: str):
    loop = asyncio.get_running_loop()
    loop.create_task(
        bot.send_group_msg(
            group_id=group,
            message=message
        )
    )
    return

