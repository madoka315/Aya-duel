# -*- coding: utf-8 -*-
"""贵族决斗：武器与弹匣（固定 3 种）"""
from hoshino.typing import CQEvent
from .. import sv
from ..core.db.duel import DuelCounter
from ..core.state import duel_judger


WEAPON_LIST = [
    ('俄罗斯左轮', 6),
    ('战术型沙漠之鹰', 12),
    ('格洛克', 20),
]


@sv.on_fullmatch('武器列表')
async def weapon(bot, ev: CQEvent):
    gid = ev.group_id
    duel = DuelCounter()
    n = duel._get_weapon(gid)
    name = next((w[0] for w in WEAPON_LIST if w[1] == n), '自定义武器')
    msg = f'目前本群启用的武器是{name}，弹匣量为{n}\n'
    msg += '[切换武器+武器名]\n可用的武器有\n'
    for i, (wname, wnum) in enumerate(WEAPON_LIST):
        msg += f'{i + 1}.{wname}  {wnum}发\n'
    await bot.send(ev, msg, at_sender=True)


@sv.on_rex(r'^切换武器(俄罗斯左轮|战术型沙漠之鹰|格洛克)$')
async def weaponchange(bot, ev: CQEvent):
    gid = ev.group_id
    match = (ev['match'])
    weaponname = (match.group(1))
    duel = DuelCounter()
    if duel_judger.get_on_off_status(gid):
        await bot.send(ev, '现在正在决斗中哦，无法切换武器。', at_sender=True)
        return
    n = dict(WEAPON_LIST)[weaponname]
    duel._set_weapon(gid, n)
    msg = f'已启用武器{weaponname}，弹匣量为{n}'
    await bot.send(ev, msg, at_sender=True)
