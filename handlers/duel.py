# -*- coding: utf-8 -*-
"""贵族决斗：俄罗斯轮盘决斗主流程与下注"""
from datetime import datetime
from hoshino import priv
from hoshino.typing import CQEvent
import asyncio
import nonebot
import pytz
import random
from .. import chara
from .. import sv
from ..core.constants import DUEL_SUPPORT_TIME, WAIT_TIME, WIN_EXP, WIN_NUM, favor_reduce, favor_reduce_NEED
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import add_exp, get_girlnum, get_noblename, get_noblescore, girl_outlimit
from ..core.state import daily_duel_limiter, duel_judger, refund_allin_support




@sv.on_prefix('贵族决斗')
async def duel_start(bot, ev: CQEvent):
    if ev.message[0].type == 'at':
        id2 = int(ev.message[0].data['qq'])
    else:
        await bot.finish(ev, '参数格式错误, 请重试')
    if duel_judger.get_on_off_status(ev.group_id):
        await bot.send(ev, "此轮决斗还没结束，请勿重复使用指令。")
        return
        
    gid = ev.group_id
    duel_judger.turn_on(gid)
    id1 = ev.user_id
    duel = DuelCounter()
    is_overtime = 0
    if id2 == id1:
        await bot.send(ev, "不能和自己决斗！", at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return 

    if duel._get_level(gid, id1) == 0:
        msg = f'[CQ:at,qq={id1}]决斗发起者还未在创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id1) == {}:
        msg = f'[CQ:at,qq={id1}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return

    if duel._get_level(gid, id2) == 0:
        msg = f'[CQ:at,qq={id2}]被决斗者还未在本群创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id2) == {}:
        msg = f'[CQ:at,qq={id2}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
   #判定每日上限
    guid = gid ,id1
    if not daily_duel_limiter.check(guid):
        await bot.send(ev, '今天的决斗次数已经超过上限了哦，明天再来吧。', at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return
    



   # 判定双方的女友是否已经超过上限

   # 这里设定大于才会提醒，就是可以超上限1名，可以自己改成大于等于。
    if girl_outlimit(gid,id1):
        msg = f'[CQ:at,qq={id1}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    if girl_outlimit(gid,id2):
        msg = f'[CQ:at,qq={id2}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    duel_judger.init_isaccept(gid)
    duel_judger.set_duelid(gid, id1, id2)
    duel_judger.turn_on_accept(gid)
    msg = f'[CQ:at,qq={id2}]对方向您发起了优雅的贵族决斗，请在{WAIT_TIME}秒内[接受/拒绝]。'

    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME)
    duel_judger.turn_off_accept(gid)
    if duel_judger.get_isaccept(gid) is False:
        msg = '决斗被拒绝。'
        duel_judger.turn_off(gid)
        await bot.send(ev, msg, at_sender=True)
        return
    daily_duel_limiter.increase(guid)
    duel = DuelCounter()
    level1 = duel._get_level(gid, id1)
    noblename1 = get_noblename(level1)
    level2 = duel._get_level(gid, id2)
    noblename2 = get_noblename(level2)
    id1Win = duel._get_WLCWIN(gid,id1)
    id2Win = duel._get_WLCWIN(gid,id2)
    id1Lose = duel._get_WLCLOSE(gid,id1)
    id2Lose = duel._get_WLCLOSE(gid,id2)
   #开局快照弹匣量：中途改武器不影响本局的轮数判定与超时判定
    weapon_num = duel._get_weapon(gid)
    if weapon_num == 6:
        msg = '''目前本群启用的武器是俄罗斯左轮，弹匣量为6\n'''
    elif weapon_num == 2:
        msg = '''目前本群启用的武器是贝雷塔687，弹匣量为2\n'''
    elif weapon_num == 20:
        msg = '''目前本群启用的武器是Glock，弹匣量为20\n'''
    elif weapon_num == 12:
        msg = '''目前本群启用的武器是战术型沙漠之鹰，弹匣量为12\n'''
    elif weapon_num == 10:
        msg = '''目前本群启用的武器是巴雷特，弹匣量为10\n'''
    else:
        msg = f'目前本群启用的是自定义武器，弹匣量为{weapon_num}\n'
    msg += f'''对方接受了决斗！    
1号：[CQ:at,qq={id1}]
爵位为：{noblename1}
胜负场：{id1Win}/{id1Lose}
2号：[CQ:at,qq={id2}]
爵位为：{noblename2}
胜负场：{id2Win}/{id2Lose}
其他人请在{DUEL_SUPPORT_TIME}秒选择支持的对象。
[支持1/2号xxx金币]
[梭哈1/2号]'''

    await bot.send(ev, msg)
    duel_judger.turn_on_support(gid)
    await asyncio.sleep(DUEL_SUPPORT_TIME)
    duel_judger.turn_off_support(gid)
    deadnum = random.randint(1,weapon_num)
    duel_judger.set_deadnum(gid, deadnum)
    duel_judger.init_turn(gid)
    duel_judger.turn_on_fire(gid)
    duel_judger.turn_off_hasfired(gid)
    msg = f'支持环节结束，下面请决斗双方轮流[开枪]。\n[CQ:at,qq={id1}]先开枪，30秒未开枪自动认输'

    await bot.send(ev, msg)
    n = 1
    while (n <= weapon_num):
        wait_n = 0
        while (wait_n < 30):
            if duel_judger.get_on_off_hasfired_status(gid):
                break

            wait_n += 1
            await asyncio.sleep(1)
        if wait_n >= 30:
           # 超时未开枪的胜负判定
            loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
            winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
            msg = f'[CQ:at,qq={loser}]\n你明智的选择了认输。'
            await bot.send(ev, msg)
            
           #记录本局为超时局。
            is_overtime = 1
            
            
            break
        else:
            if n == duel_judger.get_deadnum(gid):
               # 被子弹打到的胜负判定
                loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={loser}]\n砰！你死了。'
                await bot.send(ev, msg)
                break
            else:
                id = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                id2 = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={id}]\n砰！松了一口气，你并没有死。\n[CQ:at,qq={id2}]\n轮到你开枪了哦。'
                await bot.send(ev, msg)
                n += 1
                duel_judger.change_turn(gid)
                duel_judger.turn_off_hasfired(gid)
                duel_judger.turn_on_fire(gid)
    score_counter = ScoreCounter2()
    cidlist = duel._get_cards(gid, loser)
    selected_girl = random.choice(cidlist)
    queen = duel._search_queen(gid,loser)

    CE = CECounter()
    bangdinwin = CE._get_guaji(gid,winner)
    bangdinlose = CE._get_guaji(gid,loser)
    #判断决斗胜利者是否有绑定角色,有则增加经验值
    bd_msg=''
    if bangdinwin:
        bd_info = chara.fromid(bangdinwin)
        card_level=add_exp(gid,winner,bangdinwin,WIN_EXP)
        nvmes = bd_info.icon.cqcode
        bd_msg = f"\n您绑定的女友{bd_info.name}获得了{WIN_EXP}点经验，{card_level[2]}\n{nvmes}"
        
   #判定被输掉的是否是复制人可可萝，是则换成金币。
    if selected_girl==9999:
        score_counter._add_score(gid, winner, 300)
        c = chara.fromid(1059)
        duel._delete_card(gid, loser, selected_girl)
        msg = f'[CQ:at,qq={winner}]\n您赢得了神秘的可可萝，但是她微笑着消失了。\n本次决斗获得了300金币。'
        await bot.send(ev, msg)
        msg = f'[CQ:at,qq={loser}]\n您输掉了贵族决斗，被抢走了女友\n{c.name}，\n只要招募，她就还会来到你的身边哦。{c.icon.cqcode}'
        msg += '\n获得了安慰金50金币。'
        score_counter._add_score(gid, loser, 50)
        await bot.send(ev, msg)

   #判断被输掉的是否为皇后。    
    elif selected_girl==queen:
        score_counter._add_score(gid, winner, 300)
        msg = f'[CQ:at,qq={winner}]您赢得的角色为对方的皇后，\n您改为获得300金币。'
        await bot.send(ev, msg)
        score_counter._reduce_prestige(gid,loser,500)
        msg = f'[CQ:at,qq={loser}]您差点输掉了皇后，失去了500声望。'
        msg += '\n获得了安慰金50金币。'
        score_counter._add_score(gid, loser, 50)
        await bot.send(ev, msg)


    elif girl_outlimit(gid,winner):
        score_counter._add_score(gid, winner, 300)
        msg = f'[CQ:at,qq={winner}]您的女友超过了爵位上限，\n本次决斗获得了300金币。'
        c = chara.fromid(selected_girl)
       #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)
        if favor>=favor_reduce_NEED:
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了{favor_reduce}点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)            
        else:
            duel._delete_card(gid, loser, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗且对方超过了爵位上限，您的女友恢复了单身。\n{c.name}{c.icon.cqcode}'
            msg += '\n获得了安慰金50金币。'
            score_counter._add_score(gid, loser, 50)
            await bot.send(ev, msg)

    else:
        c = chara.fromid(selected_girl)
       #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)    
        if favor>=favor_reduce_NEED:
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了{favor_reduce}点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)      
            score_counter._add_score(gid, winner, 300)
            msg = f'[CQ:at,qq={winner}]您赢得了决斗，对方女友仍有一定好感。\n本次决斗获得了300金币。'
            await bot.send(ev, msg)  
        else:
            duel._delete_card(gid, loser, selected_girl)
            duel._add_card(gid, winner, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您被抢走了女友\n{c.name}{c.icon.cqcode}'
            msg += '\n获得了安慰金50金币。'
            score_counter._add_score(gid, loser, 50)
            await bot.send(ev, msg)
       #判断赢家的角色列表里是否有复制人可可萝。
        wincidlist = duel._get_cards(gid, winner)
        if 9999 in wincidlist:
            duel._delete_card(gid, winner, 9999)
            score_counter._add_score(gid, winner, 300)
            msg = f'[CQ:at,qq={winner}]\n“主人有了女友已经不再孤单了，我暂时离开了哦。”\n您赢得了{c.name},可可萝微笑着消失了。\n您获得了300金币。'
            await bot.send(ev, msg)
   #判断胜者败者是否需要增减声望
    winprestige = score_counter._get_prestige(gid,winner)
    if winprestige != None:
        if is_overtime == 1:
            score_counter._add_prestige(gid,winner,1)
            await bot.send(ev, f"[CQ:at,qq={winner}]本局为超时局，您的声望上升了1点。")
        else:
            score_counter._add_prestige(gid,winner,200)
            msg = f'[CQ:at,qq={winner}]决斗胜利使您的声望上升了200点。'
            await bot.send(ev, msg)
    loseprestige = score_counter._get_prestige(gid,loser)
    if loseprestige != None:
        score_counter._reduce_prestige(gid,loser,100)
        msg = f'[CQ:at,qq={loser}]决斗失败使您的声望下降了100点。'
        await bot.send(ev, msg)
    if bd_msg:
        await bot.send(ev, f'[CQ:at,qq={winner}]{bd_msg}')

   #判定败者是否掉爵位，皇帝不会因为决斗掉爵位。
    level_loser = duel._get_level(gid, loser)
    if level_loser > 1 and level_loser!=7:
        noblename_loser = get_noblename(level_loser)
        girlnum_loser = get_girlnum(level_loser - 1)
        cidlist_loser = duel._get_cards(gid, loser)
        cidnum_loser = len(cidlist_loser)
        if cidnum_loser < girlnum_loser:
            duel._reduce_level(gid, loser)
            reward = int(get_noblescore(level_loser)/2)
            score_counter._add_score(gid, loser, reward)
            new_noblename = get_noblename(level_loser - 1)
            msg = f'[CQ:at,qq={loser}]\n您的女友数为{cidnum_loser}名\n小于爵位需要的女友数{girlnum_loser}名\n您的爵位下降到了{new_noblename}\n获得掉段补偿金{reward}'
            await bot.send(ev, msg)
    duel._add_Lose(gid,loser)
   #结算下注金币，判定是否为超时局。
    if is_overtime == 1 and n != weapon_num:
        msg = '本局为超时局，记为认输，不进行金币结算，支持的金币全部返还。'
        refunded = refund_allin_support(gid)
        if refunded:
            msg += '\n梭哈托管金币已退还:\n' + ''.join(f'[CQ:at,qq={uid}]+{score}金币\n' for uid, score in refunded)
        await bot.send(ev, msg)
        duel._add_ADMIT(gid,loser)
        duel_judger.set_support(ev.group_id)
        duel_judger.turn_off(ev.group_id)
        return
    
    support = duel_judger.get_support(gid)
    duel._add_Win(gid,winner)
    duel._DALIY_add(gid,loser)
    duel._DALIY_add(gid,winner)

    winuid = []
    supportmsg = '金币结算:\n'
    winmsg = get_noblename(level_loser)
    win_reward = level_loser*40+random.randint(0,20)
    score_counter._add_score(gid, winner, win_reward)
    supportmsg += f'(决斗 {winmsg} 获胜)[CQ:at,qq={winner}]+{win_reward}金币\n'
    winnum = duel_judger.get_duelnum(gid, winner)

    if support != 0:
        for uid in support:
            support_id = support[uid][0]
            support_score = support[uid][1]
            allin = support[uid][2]
            if support_id == winnum:
                winuid.append(uid)
                if allin:
                   #梭哈已托管扣款，胜利返还本金1.5倍（净赚0.5倍）
                    winscore = int(support_score*1.5)
                else:
                   #这里是赢家获得的金币结算，可以自己修改倍率。
                    winscore = support_score*WIN_NUM
                score_counter._add_score(gid, uid, winscore)
                supportmsg += f'[CQ:at,qq={uid}]+{winscore}金币\n'
            else:
                if allin:
                   #梭哈金币下注时已扣除，失败不再重复扣款
                    supportmsg += f'[CQ:at,qq={uid}]-{support_score}金币\n'
                else:
                    score_counter._reduce_score(gid, uid, support_score)
                    supportmsg += f'[CQ:at,qq={uid}]-{support_score}金币\n'
    await bot.send(ev, supportmsg)
    duel_judger.set_support(ev.group_id)
    duel_judger.turn_off(ev.group_id)
    return


@sv.on_fullmatch('接受')
async def duel_accept(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '贵族决斗接受成功，请耐心等待决斗开始。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.on_isaccept(gid)


@sv.on_fullmatch('拒绝')
async def duel_refuse(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '您已拒绝贵族决斗。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.off_isaccept(gid)


@sv.on_fullmatch('开枪')
async def duelfire(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_fire_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]:
            duel_judger.turn_on_hasfired(gid)
            duel_judger.turn_off_fire(gid)


@sv.on_rex(r'^支持(1|2)号(\d+)(金币|币)$')
async def on_input_duel_score(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            uid = ev.user_id

            match = ev['match']
            select_id = int(match.group(1))
            input_score = int(match.group(2))
            score_counter = ScoreCounter2()
           # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
           # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
           # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return

               # 检查金币是否足够下注
            if score_counter._judge_score(gid, uid, input_score) == 0:
                msg = '您的金币不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'支持{select_id}号成功。'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_rex(r'^梭哈(1|2)号$')
async def on_input_duel_score2(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            duel = DuelCounter()
            uid = ev.user_id
            score_counter = ScoreCounter2()
            match = ev['match']
            select_id = int(match.group(1))
            current_score = score_counter._get_score(gid, uid)
            score_counter = ScoreCounter2()
           # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
           # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
           # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return
               # 检查金币是否足够下注
            if current_score == 0:
                msg = '您的金币为0，不能梭哈。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
               #下注即托管：立即扣除全部金币，胜利时返还本金的1.5倍
                score_counter._reduce_score(gid, uid, current_score)
                duel_judger.add_support(gid, uid, select_id, current_score, allin=True)
                msg = f'梭哈{select_id}号{current_score}金币成功（金币已全部托管扣除），胜利时返还本金的1.5倍金币！'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_fullmatch('重置决斗')
async def duel_reset(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置决斗哦。', at_sender=True)
    duel_judger.turn_off(ev.group_id)
    refunded = refund_allin_support(ev.group_id)
    duel_judger.set_support(ev.group_id)
    msg = '已重置本群决斗状态！'
    if refunded:
        msg += '\n梭哈托管金币已退还:\n' + ''.join(f'[CQ:at,qq={uid}]+{score}金币\n' for uid, score in refunded)
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('开启本群不决斗惩罚')
async def ON_SWITCH2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您的权限不足！', at_sender=True)
    duel = DuelCounter()
    duel._set_SWITCH2(gid,1)
    await bot.finish(ev, '开启成功！', at_sender=True)

@sv.on_fullmatch('关闭本群不决斗惩罚')
async def OFF_SWITCH2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您的权限不足！', at_sender=True)
    duel = DuelCounter()
    duel._set_SWITCH2(gid,0)
    await bot.finish(ev, '关闭成功！', at_sender=True)

@sv.on_fullmatch('查询本群不决斗惩罚')
async def search_SWITCH2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    msg = '[开启本群不决斗惩罚]\n[关闭本群不决斗惩罚]\n开启后，每天5点当检测到本群贵族连续两天未决斗，将会发生女友跑路事件！\n'
    if duel._get_SWITCH2(gid) ==0:
        msg += '❗目前本群不决斗惩罚处于关闭状态！'
        await bot.finish(ev, msg, at_sender=True)
    else:
        msg += '❗目前本群不决斗惩罚处于开启状态！'
        await bot.finish(ev, msg, at_sender=True)

@sv.scheduled_job('cron', hour ='*',)
async def duel_daily_clock():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if not now.hour == 5:#每天5点结算
        return         
    score_dict = {}
    score_counter = ScoreCounter2()
    duel = DuelCounter() 
    bot = nonebot.get_bot()
    r = 0
    n = 0
    glist = await bot.get_group_list()
    d = {}
    for m in glist:
        d[m['group_id']] = m['group_id']
    mlist = duel._get_gid_list()
    for e in range(len(mlist)):
     gid = int(mlist[e])       
     if not gid in d: #判断是否在群，避免100
        continue
     if duel._get_SWITCH2(gid) == 0:#判断是否开启惩罚，默认为关
            continue
     umlist = duel._get_uid_list(gid)
     for s in range(len(umlist)):
        uid = int(umlist[s])
        if uid != '':#避免返回空uid
         Game = duel._get_DALIY(gid,uid)
         DayS = duel._get_TOTAL(gid,uid)#获取连续多少天不决斗
         level = duel._get_level(gid,uid)
         if level >=1 and Game == 0:#如果需要连续多少天不决斗惩罚在这改
            duel._TOTAL_ADD(gid,uid)#增加一天未决斗天数
           #惩罚内容
            if DayS >= 2:#连续两天不决斗
             n = 1
             r = 0
            else:
             n = 0
            while(n):
             cidlist = duel._get_cards(gid, uid)
             try:
                selected_girl = random.choice(cidlist)
             except Exception:
                break
             queen = duel._search_queen(gid,uid)
           #判断被扣掉的的是否为妻子，是则重选。    
             if selected_girl==queen:
                if r!=10:
                    r+=1
                    continue
                else:
                    break
             else:
               #判断好感是否足够，足够则扣掉好感
                favor = duel._get_favor(gid,uid,selected_girl)    
                if favor>=favor_reduce_NEED:
                    c = chara.fromid(selected_girl)
                    duel._reduce_favor(gid,uid,selected_girl,favor_reduce)
                    msg = f'[CQ:at,qq={uid}]由于连续两天未决斗，您与{c.name}的好感下降了{favor_reduce}点。\n{c.icon.cqcode}'
                    n = 0
                else:
                    c = chara.fromid(selected_girl)
                    duel._delete_card(gid, uid, selected_girl)
                    msg = f'[CQ:at,qq={uid}]由于昨日未决斗，且好感过低，您的女友{c.name}离开了\n{c.icon.cqcode}'
                    n = 0
                await asyncio.sleep(1)
                await bot.send_group_msg(
                    group_id = int(gid),
                    message = msg
                )
         duel._DALIY_SET(gid,uid)#重置今日是否决斗
         s += 1
    #await bot.send_group_msg(
                   #group_id = int(gid),
                   #message = f'本群公爵以上，未参与过改版后决斗的有{i}人，请注意，超出7天不决斗您的数据会被清除！'
               #) 
    e += 1