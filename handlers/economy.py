# -*- coding: utf-8 -*-
"""贵族决斗：金币/声望/转账/排行榜"""
from hoshino import priv
from hoshino.typing import CQEvent
from .. import sv
from ..core.constants import SW_DAILY_LIMIT, ZERO_GET_AMOUNT, Zhuan_Low_LIMIT
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import get_user_card_dict
from ..core.state import daily_GOLDTOSW_limiter, daily_allowance_limiter



# 以下部分与赛跑的重合，有一个即可，两个插件都装建议注释掉。

@sv.on_prefix(['领金币', '领取金币'])
async def add_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id
        guid = gid,uid
        if not daily_allowance_limiter.check(guid):
            await bot.send(ev, '您今天已领取过10次了，明天才能领取哦', at_sender=True)
            return
        current_score = score_counter._get_score(gid, uid)
        if current_score == 0:
            score_counter._add_score(gid, uid, ZERO_GET_AMOUNT)
            daily_allowance_limiter.increase(guid)
            msg = f'您已领取{ZERO_GET_AMOUNT}金币'
            await bot.send(ev, msg, at_sender=True)
            return
        else:
            msg = '金币为0才能领取哦。'
            await bot.send(ev, msg, at_sender=True)
            return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_prefix(['查金币', '查询金币', '查看金币'])
async def get_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id

        current_score = score_counter._get_score(gid, uid)
        msg = f'您的金币为{current_score}'
        await bot.send(ev, msg, at_sender=True)
        return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_rex(f'^为(.*)充值(\d+)金币$')
async def score_recharge(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '只有机器人管理才能使用氪金功能哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except Exception:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    score_counter._add_score(gid, id, num)
    score = score_counter._get_score(gid, id)
    msg = f'已为[CQ:at,qq={id}]充值{num}金币。\n现在共有{score}金币。'
    await bot.send(ev, msg)


#重置某一用户的金币，只用做必要时删库用。
@sv.on_prefix('重置金币')
async def reset_score(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置金币功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置金币+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, id,current_score)
        await bot.finish(ev, f'已清空用户{id}的金币。', at_sender=True)

@sv.on_fullmatch('用金币兑换声望')
async def cheat_intro(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    score_counter = ScoreCounter2()
    msg = '用法：[用x金币兑换声望]\n请注意：请不要输入非等倍的数字，不会找还零钱！随着本群贵族的总金币数增加，兑换比例也会增加！\n'
    user_card_dict = await get_user_card_dict(bot, gid)
    total_score = 0
    for uid in user_card_dict.keys():
        if uid != ev.self_id:
            total_score += score_counter._get_score(gid, uid)
    msg += f'当前所有人有金币{total_score}个，'
    if total_score < 20000:
        ritsu = 10
    elif total_score < 100000:
        up = int(str(total_score)[:1])
        ritsu = 10+up
    else:
        ritsu = 20
    msg += f'当前的金币:声望为{ritsu}:1。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^用(\d+)金币兑换声望$')
async def prestige_exchange(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    num = int(match.group(1))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    guid = gid, uid
    prestige = score_counter._get_prestige(gid,uid)   
    if num > SW_DAILY_LIMIT - daily_GOLDTOSW_limiter.checks(guid) :
        await bot.finish(ev, f'超出兑换最大限额！您今天还剩{SW_DAILY_LIMIT - daily_GOLDTOSW_limiter.checks(guid)}金币可以兑换！', at_sender=True) 
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还没有在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '您未开启声望系统哦！。', at_sender=True)   
    score = score_counter._get_score(gid, uid)
    pay_score=num
    user_card_dict = await get_user_card_dict(bot, gid)
    total_score = 0
    for uid in user_card_dict.keys():
        if uid != ev.self_id:
            total_score += score_counter._get_score(gid, uid)
    if total_score < 20000:
        ritsu = 10
        num2 = int(pay_score/ritsu)
    elif total_score < 100000:
        up = int(str(total_score)[:1])
        ritsu = 10+up
        num2 = int(pay_score/ritsu)
    else:
        ritsu = 20
        num2 = int(pay_score/ritsu)
    if pay_score > score:
        msg = f'您的金币只有{score}，无法兑换哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        uid = ev.user_id
        score_counter._reduce_score(gid, uid, pay_score)
        score_counter._add_prestige(gid,uid,num2)
        scoreyou = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        daily_GOLDTOSW_limiter.increase2(guid,num)
        msg = f'使用{num}金币兑换{num2}声望成功\n您的声望为{prestige}，金币剩余{scoreyou}。'
        await bot.send(ev, msg, at_sender=True)
   
@sv.on_rex(f'^为(.*)转账(\d+)金币$')
async def score_transfer(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except Exception:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if num < Zhuan_Low_LIMIT :
        await bot.finish(ev, f'低于转账最小限额！最少转出{Zhuan_Low_LIMIT}', at_sender=True)
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < num:
        msg = f'您的金币不足{num}哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._add_score(gid, id, num)
        score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, uid, num)
        scoreyou = score_counter._get_score(gid, uid)
        msg = f'已为[CQ:at,qq={id}]转账{num}金币。\n您的金币剩余{scoreyou}金币，对方金币剩余{score}金币。'
        await bot.send(ev, msg)

@sv.on_fullmatch(('声望排行榜', '声望排行'))
async def prestige_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_prestige(gid, uid)
                if score_dict[user_card_dict[uid]] == None:
                   score_dict[user_card_dict[uid]] = 0
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决声望排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 声望: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))      

@sv.on_fullmatch(('胜场排行榜', '贵族胜场排行'))
async def SC_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        duel = DuelCounter() 
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = duel._get_WLCWIN(gid, uid)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 累计胜场: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))  

@sv.on_fullmatch(('女友排行榜', '女友排行'))
async def girl_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        duel = DuelCounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                cidlist = duel._get_cards(gid, uid)
                score_dict[user_card_dict[uid]] = cidnum = len(cidlist)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决女友数排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 女友数: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))     