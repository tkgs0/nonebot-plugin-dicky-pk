import asyncio
from pathlib import Path
import ujson as json
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    MessageEvent,
    GroupMessageEvent,
    GROUP_OWNER,
    GROUP_ADMIN,
)

from .src.main import KEYWORDS, message_processor as chinchin


confpath = Path() / 'data' / 'chinchin_pk' / 'chinchin.json'
confpath.parent.mkdir(parents=True, exist_ok=True)

enablelist = (
    json.loads(confpath.read_text(encoding='utf-8'))
    if confpath.is_file()
    else {'all': False, 'group': []}
)


def save_conf():
    confpath.write_text(json.dumps(enablelist), encoding='utf-8')


_help = [
    '/็ๅญ',
    '/pk @็จๆท',
    '/๐(/suo/ๅฆ/้)ๆ',
    '/๐(/suo/ๅฆ/้) @็จๆท',
    '/ๆ่ถ',
    '/็ไป็ๅญ(/็็็ๅญ) @็จๆท',
    '/ๆณจๅ็ๅญ',
    '/็ๅญๆๅ(/็ๅญๆ่ก)',
    '/็ๅ(/็ๅญๅฅฝๅ/็ๅญๆๅ)',
    '/ๅณๆณจ็ๅญ(/ๆทปๅ ็ๅ)',
    '/ๅๅณ็ๅญ(/ๅ ้ค็ๅ)',
    '/็ๅญ่ฝฌ็',
    '/็ๅญๆๅฐฑ',
    '/็ๅญไปๅข',
    '/็ๅญไฟฎ็ผ(/็ๅญ็ปๅ/็ๅญไฟฎไป)',
]


def dicky_run(msg: str, bot: Bot, event: GroupMessageEvent):

    def get_at_segment(qq: int):
        return f'{MessageSegment.at(qq)}'
    def send_message(qq: int, group: int, message: str):
        loop = asyncio.get_running_loop()
        loop.create_task(bot.send_group_msg(group_id=group, message=message))

    if not enablelist['all']:
        return
    if not event.group_id in enablelist['group']:
        return
    uid = event.user_id
    gid = event.group_id
    uids = [at.data['qq'] for at in event.get_message()['at']]
    at_id = int(uids[0]) if uids else None
    nickname = event.sender.card if event.sender.card else event.sender.nickname
    fuzzy_match = True
    chinchin(
        msg, uid, gid, at_id, nickname, fuzzy_match,
        get_at_segment, send_message
    )


get_chinchin = on_command(
    '/็ๅญ',
    priority=15,
    block=True
)

@get_chinchin.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    if not enablelist['all']:
        return
    if not event.group_id in enablelist['group']:
        return
    if (msg := arg.extract_plain_text()).startswith('ๅธฎๅฉ'):
        await get_chinchin.finish('\n'.join(_help))
    dicky_run('็ๅญ'+msg, bot, event)
    return


@on_command(
    '/pk',
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['pk'][0], bot, event)
    return


@on_command(
    '/๐ๆ',
    aliases={"/suoๆ", "/ๅฆๆ", "/้ๆ"},
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['lock_me'][0], bot, event)
    return


@on_command(
    '/๐',
    aliases={"/suo", "/ๅฆ", "/้"},
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['lock'][0], bot, event)
    return


@on_command(
    '/ๆ่ถ',
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['glue'][0], bot, event)
    return


@on_command(
    '/็ไป็ๅญ',
    aliases={"/็็็ๅญ"},
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['see_chinchin'][0], bot, event)
    return


@on_command(
    '/ๆณจๅ็ๅญ',
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['sign_up'][0], bot, event)
    return


@on_command(
    '/็ๅ',
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['friends'][0], bot, event)
    return


@on_command(
    '/ๅณๆณจ็ๅญ',
    aliases={"/ๆทปๅ ็ๅ"},
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['friends_add'][0], bot, event)
    return


@on_command(
    '/ๅๅณ็ๅญ',
    aliases={"/ๅ ้ค็ๅ"},
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['friends_delete'][0], bot, event)
    return


def set_enable(gid: int, en: bool):
    if en:
        enablelist['group'].append(gid)
        list(set(enablelist['group']))
    else:
        enablelist['group'] = [uid for uid in enablelist['group'] if not uid == gid]
    save_conf()


enable_jjpk = on_command(
    '/ๅฏ็จ็ๅญpk',
    aliases={'/ๅผๅฏ็ๅญpk', '/ๅฏ็จdicky-pk', '/ๅผๅฏdicky-pk'},
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
    priority=5,
    block=True
)

@enable_jjpk.handle()
async def _(event: GroupMessageEvent):
    if not enablelist['all']:
        return
    set_enable(event.group_id, True)
    await enable_jjpk.finish('ๅทฒๅฏ็จ็พค่ๅฐๆธธๆ: Dicky-PK')


disable_jjpk = on_command(
    '/็ฆ็จ็ๅญpk',
    aliases={'/ๅณ้ญ็ๅญpk', '/็ฆ็จdicky-pk', '/ๅณ้ญdicky-pk'},
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
    priority=5,
    block=True
)

@disable_jjpk.handle()
async def _(event: GroupMessageEvent):
    if not enablelist['all']:
        return
    set_enable(event.group_id, False)
    await disable_jjpk.finish('ๅทฒ็ฆ็จ็พค่ๅฐๆธธๆ: Dicky-PK')


chinchin_enable = on_command(
    '/ๅผๅฏ็ๅญ็งๅข',
    permission=SUPERUSER,
    priority=2,
    block=True
)

@chinchin_enable.handle()
async def _(event: MessageEvent):
    msg = ''
    if isinstance(event, GroupMessageEvent):
        set_enable(event.group_id, True)
        msg += '\nๅทฒๅจๆฌ็พคๅฏ็จ็ๅญpk'
    enablelist['all']  = True
    save_conf()
    await chinchin_enable.finish('็ๅญ็งๅขๅทฒๅผๅฏ.'+msg)


chinchin_disable = on_command(
    '/ๅณ้ญ็ๅญ็งๅข',
    permission=SUPERUSER,
    priority=2,
    block=True
)

@chinchin_disable.handle()
async def _():
    enablelist['group'].clear()
    enablelist['all']  = False
    save_conf()
    await chinchin_disable.finish('็ๅญ็งๅขๅทฒๅณ้ญ.')
