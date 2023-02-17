from pathlib import Path
import ujson as json
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
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
    '/牛子',
    '/pk @用户',
    '/🔒(/suo/嗦/锁)我',
    '/🔒(/suo/嗦/锁) @用户',
    '/打胶',
    '/看他牛子(/看看牛子) @用户',
    '/注册牛子',
    '/牛子排名(/牛子排行)',
    '/牛子转生',
    '/牛子成就',
    '/牛子仙境',
    '/牛子修炼(/牛子练功/牛子修仙)',
]


def dicky_run(msg: str, bot: Bot, event: GroupMessageEvent):
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
    chinchin(bot, msg, uid, gid, at_id, nickname, fuzzy_match)


get_chinchin = on_command(
    '/牛子',
    priority=15,
    block=True
)

@get_chinchin.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    if not enablelist['all']:
        return
    if not event.group_id in enablelist['group']:
        return
    if (msg := arg.extract_plain_text()).startswith('帮助'):
        await get_chinchin.finish('\n'.join(_help))
    dicky_run('牛子'+msg, bot, event)
    return


@on_command(
    '/'+KEYWORDS['pk'][0],
    aliases=set('/'+i for i in KEYWORDS['pk'][1:]),
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['pk'][0], bot, event)
    return


@on_command(
    '/'+KEYWORDS['lock_me'][0],
    aliases=set('/'+i for i in KEYWORDS['lock_me'][1:]),
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['lock_me'][0], bot, event)
    return


@on_command(
    '/'+KEYWORDS['lock'][0],
    aliases=set('/'+i for i in KEYWORDS['lock'][1:]),
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['lock'][0], bot, event)
    return


@on_command(
    '/'+KEYWORDS['glue'][0],
    aliases=set('/'+i for i in KEYWORDS['glue'][1:]),
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['glue'][0], bot, event)
    return


@on_command(
    '/'+KEYWORDS['see_chinchin'][0],
    aliases=set('/'+i for i in KEYWORDS['see_chinchin'][1:]),
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['see_chinchin'][0], bot, event)
    return


@on_command(
    '/'+KEYWORDS['sign_up'][0],
    aliases=set('/'+i for i in KEYWORDS['sign_up'][1:]),
    priority=15,
    block=True
).handle()
async def _(bot: Bot, event: GroupMessageEvent):
    dicky_run(KEYWORDS['sign_up'][0], bot, event)
    return


def set_enable(gid: int, en: bool):
    if en:
        enablelist['group'].append(gid)
        list(set(enablelist['group']))
    else:
        enablelist['group'] = [uid for uid in enablelist['group'] if not uid == gid]
    save_conf()


enable_jjpk = on_command(
    '/启用牛子pk',
    aliases={'/开启牛子pk', '/启用dicky-pk', '/开启dicky-pk'},
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
    priority=5,
    block=True
)

@enable_jjpk.handle()
async def _(event: GroupMessageEvent):
    if not enablelist['all']:
        return
    set_enable(event.group_id, True)
    await enable_jjpk.finish('已启用群聊小游戏: Dicky-PK')


disable_jjpk = on_command(
    '/禁用牛子pk',
    aliases={'/关闭牛子pk', '/禁用dicky-pk', '/关闭dicky-pk'},
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
    priority=5,
    block=True
)

@disable_jjpk.handle()
async def _(event: GroupMessageEvent):
    if not enablelist['all']:
        return
    set_enable(event.group_id, False)
    await disable_jjpk.finish('已禁用群聊小游戏: Dicky-PK')


chinchin_enable = on_command(
    '/开启牛子秘境',
    permission=SUPERUSER,
    priority=2,
    block=True
)

@chinchin_enable.handle()
async def _(event: MessageEvent):
    msg = ''
    if isinstance(event, GroupMessageEvent):
        set_enable(event.group_id, True)
        msg += '\n已在本群启用牛子pk'
    enablelist['all']  = True
    save_conf()
    await chinchin_enable.finish('牛子秘境已开启.'+msg)


chinchin_disable = on_command(
    '/关闭牛子秘境',
    permission=SUPERUSER,
    priority=2,
    block=True
)

@chinchin_disable.handle()
async def _():
    enablelist['group'].clear()
    enablelist['all']  = False
    save_conf()
    await chinchin_disable.finish('牛子秘境已关闭.')
