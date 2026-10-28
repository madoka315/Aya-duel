# -*- coding: utf-8 -*-
"""战斗：经验池（挂机修炼已下线，只保留存量经验分配）"""
from hoshino.typing import CQEvent
from .. import chara
from .. import sv
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.rules import add_exp


@sv.on_fullmatch(['我的经验池', '经验池'])
async def get_exp_chizi_num(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    myexp = CE._get_exp_chizi(gid, uid)
    await bot.send(ev, f'您的经验池目前剩余经验为{myexp}点。', at_sender=True)


@sv.on_prefix(['分配经验'])
async def add_exp_chizi(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args) != 2:
        await bot.finish(ev, '请输入 分配经验+女友名+经验值 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
    try:
        addexp = int(args[1])
    except ValueError:
        await bot.finish(ev, '请输入正确的经验数。', at_sender=True)
    if addexp < 1:
        await bot.finish(ev, '请输入正确的经验数。', at_sender=True)
    duel = DuelCounter()
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    owner = duel._get_card_owner(gid, cid)
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid != owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法分配哦。'
        await bot.send(ev, msg)
        return
    myexp = CE._get_exp_chizi(gid, uid)
    if addexp > myexp:
        await bot.finish(ev, f'您的经验池经验只有{myexp}点，不足{addexp}，无法分配哦。', at_sender=True)
    card_level = add_exp(gid, uid, cid, addexp)
    CE._add_exp_chizi(gid, uid, 0 - addexp)
    bd_msg = f"经验分配成功\n您的女友{c.name}获得了{addexp}点经验，{card_level[2]}\n{nvmes}"
    await bot.send(ev, bd_msg, at_sender=True)
