# -*- coding: utf-8 -*-
"""战斗：挂机修炼与经验池"""
from hoshino.typing import CQEvent
import math
import time
from .. import chara
from .. import sv
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import add_exp


        
@sv.on_prefix(['挂机修炼','开始挂机'])
async def xiulian_start(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 挂机修炼+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    CE = CECounter()
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    owner = duel._get_card_owner(gid, cid)
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法绑定哦。'
        await bot.send(ev, msg)
        return
    guajiinfo = CE._get_xiulian(gid,uid)
    if guajiinfo[0] > 0:
        cgj = chara.fromid(guajiinfo[0])
        nvmesgj = cgj.icon.cqcode
        await bot.finish(ev, f'{cgj.name}已经在修炼中了哦。{nvmesgj}', at_sender=True)
    if uid==owner:
        xltime = time.time()
        xltime = math.ceil(xltime)
        CE._add_xiulian(gid,uid,cid,xltime)
        await bot.send(ev, f'您的女友{c.name}开始修炼了\n注：一次性修炼最长不能超过24小时哦。{nvmes}', at_sender=True)
    
@sv.on_fullmatch(['结束修炼','取消修炼'])
async def xiulian_end(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    guajiinfo = CE._get_xiulian(gid,uid)
    if guajiinfo[0] == 0:
        await bot.finish(ev, f'您没有正在修炼中的女友，请输入 挂机修炼+女友名 开始修炼哦。', at_sender=True)
    endtime = time.time()
    endtime = math.ceil(endtime)
    jgtime = endtime-guajiinfo[1]
    if jgtime<60:
        CE._delete_xiulian(gid,uid)
        await bot.finish(ev, f'修炼结束，修炼时间小于1分钟，无法获得经验。', at_sender=True)
    sj_msg = ''
    if jgtime>86400:
        xlmin1 = math.ceil(jgtime/60)
        sj_msg = sj_msg + f"总共修炼时间{xlmin1}分钟，由于超过24小时，实际"
        jgtime = 86400
    xlmin = math.ceil(jgtime/60)
    sj_msg = sj_msg + f"修炼时间为{xlmin}分钟，"
    addexp = xlmin*10
    card_level=add_exp(gid,uid,guajiinfo[0],addexp)
    CE._delete_xiulian(gid,uid)
    c = chara.fromid(guajiinfo[0])
    nvmes = c.icon.cqcode
    bd_msg = f"修炼结束，{sj_msg}\n您的女友{c.name}获得了{addexp}点经验，{card_level[2]}\n{nvmes}"
    await bot.send(ev, bd_msg, at_sender=True)

@sv.on_fullmatch(['我的经验池','经验池'])
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
    if len(args)!=2:
        await bot.finish(ev, '请输入 分配经验+女友名+经验值 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    addexp = int(args[1])
    if addexp<1:
        await bot.finish(ev, '请输入正确的经验数。', at_sender=True)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    CE = CECounter()
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    owner = duel._get_card_owner(gid, cid)
    if uid!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法绑定哦。'
        await bot.send(ev, msg)
        return
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid==owner:
        myexp = CE._get_exp_chizi(gid, uid)
        if addexp>myexp:
            await bot.finish(ev, f'您的经验池经验只有{myexp}点，不足{addexp}，无法分配哦。', at_sender=True)
        card_level=add_exp(gid,uid,cid,addexp)
        last_exp = 0-addexp
        CE._add_exp_chizi(gid, uid, last_exp)
        bd_msg = f"经验分配成功\n您的女友{c.name}获得了{addexp}点经验，{card_level[2]}\n{nvmes}"
        await bot.send(ev, bd_msg, at_sender=True)