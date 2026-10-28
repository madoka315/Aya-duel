# -*- coding: utf-8 -*-
"""战斗：会战/补时刀/伤害排行/月结"""
from datetime import datetime
from hoshino.typing import CQEvent
import asyncio
import json
import math
import nonebot
import os
import pytz
import random
import re
from .. import chara
from .. import sv
from ..core.constants import FILE_PATH
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.rules import add_equip_info, add_exp, get_boss_info, get_card_ce, get_nextbossinfo
from ..core.state import daily_boss_limiter


   
@sv.on_rex(f'^编队(.*)模拟(.*)$')
async def moni_huizhan(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    # 处理输入数据
    match = ev['match']
    gotype = str(match.group(2))
    gotype = re.sub(r'[?？，,_ ]', '', gotype)
    if gotype == "世界boss":
        await bot.finish(ev, '世界boss已下线，请使用boss战。', at_sender=True)
    elif gotype == "boss战":
        sendgid = gid
        shijieflag = 0
    else:
        await bot.finish(ev, '请选择正确的boss战类型（boss战）', at_sender=True)
    defen = str(match.group(1))
    defen = re.sub(r'[?？，,_]', '', defen)
    if not defen:
        await bot.finish(ev, '请发送"编队+女友名/队伍名+模拟boss战"，无需+号', at_sender=True)
    #查询是否是队伍
    teamlist = CE._get_teamlist(gid, uid, defen)
    if teamlist!=0:
        defen = []
        for i in teamlist:
            cid = i[0]
            defen.append(cid)
    else:
        defen, unknown = chara.roster.parse_team(defen)
        cidlist = duel._get_cards(gid, uid)
        if unknown:
            _, name, score = chara.guess_id(unknown)
            if score < 70 and not defen:
                return  # 忽略无关对话
            msg = f'无法识别"{unknown}"' if score < 70 else f'无法识别"{unknown}" 您说的有{score}%可能是{name}'
            await bot.finish(ev, msg)
        if len(defen) > 5:
            await bot.finish(ev, '编队不能多于5名角色', at_sender=True)
        if len(defen) != len(set(defen)):
            await bot.finish(ev, '编队中含重复角色', at_sender=True)
    for cid in defen:
        c = chara.fromid(cid)
        nvmes = c.icon.cqcode
        owner = duel._get_card_owner(gid, cid)
        if owner == 0:
            await bot.finish(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
            return
        if uid!=owner:
            msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法编队哦。'
            await bot.finish(ev, msg)
            return
    z_ce=0
    bianzu=''
    #获取本群boss状态和血量
    bossinfo = get_boss_info(sendgid)
    if len(bossinfo)>0:
        #获取编队战力与信息
        for cid in defen:
            c = chara.fromid(cid)
            card_ce=get_card_ce(gid,uid,cid)
            z_ce=z_ce+card_ce
            bianzu=bianzu+f"{c.name} "
        #
        boss_ce = bossinfo['ce']
        msg1=f"[CQ:at,qq={uid}]编组成功{bianzu}\n开始模拟会战\n当前boss为：第{bossinfo['zhoumu']}周目{bossinfo['bossid']}号boss({bossinfo['name']})\nboss战力为{bossinfo['ce']}，当前血量为{bossinfo['hp']}\n您的编组战力为{z_ce}，开始模拟战斗\n{bossinfo['icon']}"
        tas_list = []
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":msg1
                    }
                }
        tas_list.append(data)
        
        #计算造成的伤害
        #2者相加的总战力
        zhanlz = boss_ce + z_ce
        #计算总战力扩值
        kuo = zhanlz * zhanlz
        #计算总战力差值
        cha = (zhanlz/z_ce)
        #计算无战力压制因素的输出伤害
        shuchu = (kuo/boss_ce)/cha
        #计算战力压制因素印象可以造成的伤害比
        zhanbi = z_ce/zhanlz+1
        #计算输出浮动数+-10%
        fudong = int(math.floor( random.uniform(1,20) ))
        if fudong>10:
            fudong = fudong/200+1
        else:
            fudong = 1-fudong/100
        #计算最终输出伤害
        shanghai = math.ceil((shuchu * fudong)/zhanbi)
        msg = ''
        if shanghai>bossinfo['hp']:
            #计算健康状态
            card_jk = 100-math.ceil(bossinfo['hp']/shanghai*100)
            #计算下一个boss
            nextboss = bossinfo['bossid'] + 1
            nextzhoumu = bossinfo['zhoumu']
            if nextboss == 6:
                nextboss = 1
                nextzhoumu = bossinfo['zhoumu'] + 1
            nextbossinfo = get_nextbossinfo(nextzhoumu,nextboss,shijieflag)
            boss_msg = f"模拟击杀了boss\n下一个boss为：第{nextzhoumu}周目{nextboss}号boss({nextbossinfo['name']})"
            msg = msg + f"您模拟战对boss造成了{shanghai}点伤害，{boss_msg}\n由于伤害超出boss剩余血量，实际模拟造成伤害为{bossinfo['hp']}点\n您的队伍可以剩余血量{card_jk}%\n{nextbossinfo['icon']}"
        else:
            #每日次数-1
            #daily_boss_limiter.increase(guid)
            #计算下一个boss
            nextboss = bossinfo['bossid']
            nextzhoumu = bossinfo['zhoumu']
            if shanghai==bossinfo['hp']:
                nextboss = bossinfo['bossid'] + 1
                if nextboss == 6:
                    nextboss = 1
                    nextzhoumu = bossinfo['zhoumu'] + 1
                nextbossinfo = get_nextbossinfo(nextzhoumu,nextboss,shijieflag)
                boss_msg = f"击杀了boss\n下一个boss为：第{nextzhoumu}周目{nextboss}号boss({nextbossinfo['name']})\n{nextbossinfo['icon']}"
            else:
                now_hp = bossinfo['hp'] - shanghai
                boss_msg = f"boss剩余血量{now_hp}点"
            msg = msg + f"您模拟战对boss造成了{shanghai}点伤害，{boss_msg}"
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":msg
                    }
                }
        tas_list.append(data)
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=tas_list)
    else:
        await bot.finish(ev, '无法获取boss信息', at_sender=True)
        return

@sv.on_rex(f'^(.*)补时刀$')
async def start_bushi(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    gotype = str(match.group(1))
    gotype = re.sub(r'[?？，,_ ]', '', gotype)
    if gotype == "世界boss":
        await bot.finish(ev, '世界boss已下线，请使用boss战。', at_sender=True)
    elif gotype == "boss战":
        sendgid = gid
        shijieflag = 0
        keygid = gid
    else:
        await bot.finish(ev, '请选择正确的boss战类型（boss战）', at_sender=True)
    
    guid = keygid ,uid
    if not daily_boss_limiter.check(guid):
        await bot.send(ev, f'今天的{gotype}次数已经超过上限了哦，明天再来吧。', at_sender=True)
        return
    duel = DuelCounter()
    CE = CECounter()
    cidlist = duel._get_cards(gid, uid)
    nowyear = datetime.now().year
    nowmonth = datetime.now().month
    nowday = datetime.now().day
    fighttime = str(nowyear) + str(nowmonth) + str(nowday)
    bushilist = CE._get_cardbushi(gid,uid,fighttime,shijieflag)
    if bushilist==0:
        await bot.finish(ev, '您没有处于补时刀状态，请正常出刀哦', at_sender=True)
    #print(fighttime)
    z_ce=0
    bianzu=''
    #获取本群boss状态和血量
    bossinfo = get_boss_info(sendgid)
    if len(bossinfo)>0:
        #获取编队战力与信息
        card_jk = 0
        for i in bushilist:
            cid = i[0]
            card_jk = i[1]/100
            c = chara.fromid(cid)
            card_ce=get_card_ce(gid,uid,cid)
            z_ce=z_ce+card_ce
            bianzu=bianzu+f"{c.name} "
        #
        boss_ce = bossinfo['ce']
        msg1=f"[CQ:at,qq={uid}]编组成功{bianzu}\n开始进入补时刀\n当前boss为：第{bossinfo['zhoumu']}周目{bossinfo['bossid']}号boss({bossinfo['name']})\nboss战力为{bossinfo['ce']}，当前血量为{bossinfo['hp']}\n您的编组战力为{z_ce}，开始战斗\n{bossinfo['icon']}"
        tas_list = []
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":msg1
                    }
                }
        tas_list.append(data)
        
        #计算造成的伤害
        #2者相加的总战力
        zhanlz = boss_ce + z_ce
        #计算总战力扩值
        kuo = zhanlz * zhanlz
        #计算总战力差值
        cha = (zhanlz/z_ce)
        #计算无战力压制因素的输出伤害
        shuchu = (kuo/boss_ce)/cha
        #计算战力压制因素印象可以造成的伤害比
        zhanbi = z_ce/zhanlz+1
        #计算输出浮动数+-10%
        fudong = int(math.floor( random.uniform(1,20) ))
        if fudong>10:
            fudong = fudong/200+1
        else:
            fudong = 1-fudong/100
        #计算最终输出伤害
        shanghai_zc = math.ceil((shuchu * fudong)/zhanbi)
        shanghai = math.ceil((shuchu * fudong)/zhanbi * card_jk)
        msg = ''
        #for i in bushilist:
            #cid = i[0]
            #duel._add_favor(gid,uid,cid,dungeoninfo['add_favor'])
            #card_level=add_exp(gid,uid,cid,bossinfo['add_exp'])
        #每日次数-1
        daily_boss_limiter.increase(guid)
        #判断造成的伤害是否大于boss血量
        if shanghai>bossinfo['hp']:
            #计算健康状态
            #card_jk = 100-math.ceil(bossinfo['hp']/shanghai*100)
            #计算下一个boss
            nextboss = bossinfo['bossid'] + 1
            nextzhoumu = bossinfo['zhoumu']
            nexthp = 0
            if nextboss == 6:
                nextboss = 1
                nextzhoumu = bossinfo['zhoumu'] + 1
            nextbossinfo = get_nextbossinfo(nextzhoumu,nextboss,shijieflag)
            boss_msg = f"击杀了boss\n下一个boss为：第{nextzhoumu}周目{nextboss}号boss({nextbossinfo['name']})"
            msg = msg + f"您对boss造成了{shanghai}点伤害，{boss_msg}\n由于伤害超出boss剩余血量，实际造成伤害为{bossinfo['hp']}点\n{nextbossinfo['icon']}"
        else:
            
            #计算下一个boss
            nextboss = bossinfo['bossid']
            nextzhoumu = bossinfo['zhoumu']
            nexthp = 0
            if shanghai==bossinfo['hp']:
                nextboss = bossinfo['bossid'] + 1
                if nextboss == 6:
                    nextboss = 1
                    nextzhoumu = bossinfo['zhoumu'] + 1
                nextbossinfo = get_nextbossinfo(nextzhoumu,nextboss,shijieflag)
                boss_msg = f"击杀了boss\n下一个boss为：第{nextzhoumu}周目{nextboss}号boss({nextbossinfo['name']})\n{nextbossinfo['icon']}"
            else:
                now_hp = bossinfo['hp'] - shanghai
                nexthp = now_hp
                boss_msg = f"boss剩余血量{now_hp}点"
            msg = msg + f"您对boss造成了{shanghai}点伤害，{boss_msg}"
        #保存boss状态
        CE._up_bossinfo(sendgid, nextzhoumu, nextboss, nexthp)
        CE._add_bossfight(gid, uid, bossinfo['zhoumu'], bossinfo['bossid'], shanghai, shijieflag)
        for i in bushilist:
            cid = i[0]
            CE._add_cardfight(gid, uid, cid, fighttime, 0, shijieflag)
            card_level=add_exp(gid,uid,cid,bossinfo['add_exp'])
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":msg
                    }
                }
        tas_list.append(data)
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=tas_list)
        await asyncio.sleep(3)
        
        #判断是否击杀boss，分配boss掉落
        if shanghai>=bossinfo['hp']:
            #获取boss伤害输出表
            group_list=[]
            awardlist = []
            awardnum = 0
            shuchulist = CE._get_shuchulist(sendgid, bossinfo['zhoumu'], bossinfo['bossid'], shijieflag)
            for shuchu in shuchulist:
                if awardnum < 3:
                    awardlist.append(shuchu[2])
                awardnum += 1
                if shuchu[0] not in group_list:
                    group_list.append(shuchu[0])
            for groupid in group_list:
                tas_list = []
                data = {
                    "type": "node",
                    "data": {
                        "name": "会战系统",
                        "uin": "794275021",
                        "content":f"{gotype}战况：\n第{bossinfo['zhoumu']}周目{bossinfo['bossid']}号boss({bossinfo['name']})\n已被打死，开始分配boss掉落"
                            }
                        }
                tas_list.append(data)
                for shuchu in shuchulist:
                    if groupid == shuchu[0]:
                        get_equip = ''
                        get_awardequip = ''
                        for y in range(bossinfo['dropnum']):
                            equip_info = add_equip_info(shuchu[0],shuchu[1],bossinfo['dropequip'],bossinfo['equip'])
                            get_equip = get_equip + f"{equip_info['model']}品质{equip_info['type']}:{equip_info['name']}\n"
                        if shuchu[2] in awardlist:
                            awardequip_info = add_equip_info(shuchu[0],shuchu[1],bossinfo['awardequip'],bossinfo['awardlist'])
                            get_awardequip = get_awardequip + f"由于您的本次输出为前三名，额外获得装备：{awardequip_info['model']}品质{awardequip_info['type']}:{awardequip_info['name']}\n"
                        data = {
                            "type": "node",
                            "data": {
                                "name": "会战系统",
                                "uin": "794275021",
                                "content":f"[CQ:at,qq={shuchu[1]}]您对boss造成了{shuchu[2]}点伤害，获得了装备\n{get_equip}{get_awardequip}"
                                    }
                                }
                        tas_list.append(data)
                await bot.send_group_forward_msg(group_id=groupid, messages=tas_list)
    else:
        await bot.finish(ev, '无法获取boss信息', at_sender=True)
        return

   
@sv.on_rex(f'^编队(.*)开始(.*)$')
async def start_huizhan(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    # 处理输入数据
    match = ev['match']
    gotype = str(match.group(2))
    gotype = re.sub(r'[?？，,_ ]', '', gotype)
    if gotype == "世界boss":
        await bot.finish(ev, '世界boss已下线，请使用boss战。', at_sender=True)
    elif gotype == "boss战":
        sendgid = gid
        shijieflag = 0
        keygid = gid
    else:
        await bot.finish(ev, '请选择正确的boss战类型（boss战）', at_sender=True)
    nowyear = datetime.now().year
    nowmonth = datetime.now().month
    nowday = datetime.now().day
    fighttime = str(nowyear) + str(nowmonth) + str(nowday)
    guid = keygid ,uid
    if not daily_boss_limiter.check(guid):
        await bot.send(ev, f'今天的{gotype}次数已经超过上限了哦，明天再来吧。', at_sender=True)
        return
    defen = str(match.group(1))
    defen = re.sub(r'[?？，,_]', '', defen)
    if not defen:
        await bot.finish(ev, '请发送"编队+女友名/队伍名+开始boss战"，无需+号', at_sender=True)
    #查询是否是队伍
    teamlist = CE._get_teamlist(gid, uid, defen)
    if teamlist!=0:
        defen = []
        for i in teamlist:
            cid = i[0]
            defen.append(cid)
    else:
        defen, unknown = chara.roster.parse_team(defen)
        cidlist = duel._get_cards(gid, uid)
        if unknown:
            _, name, score = chara.guess_id(unknown)
            if score < 70 and not defen:
                return  # 忽略无关对话
            msg = f'无法识别"{unknown}"' if score < 70 else f'无法识别"{unknown}" 您说的有{score}%可能是{name}'
            await bot.finish(ev, msg)
        if len(defen) > 5:
            await bot.finish(ev, '编队不能多于5名角色', at_sender=True)
        if len(defen) != len(set(defen)):
            await bot.finish(ev, '编队中含重复角色', at_sender=True)
    for cid in defen:
        c = chara.fromid(cid)
        nvmes = c.icon.cqcode
        owner = duel._get_card_owner(gid, cid)
        if owner == 0:
            await bot.finish(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        if uid!=owner:
            msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法编队哦。'
            await bot.finish(ev, msg)
        fightinfo = CE._get_cardfightinfo(gid, uid, cid, fighttime, shijieflag)
        if fightinfo[0]>0:
            if fightinfo[1]>0:
                msg = f'您现在正处于补时刀状态，无法正常出刀，请输入指令‘{gotype}补时刀’进入下一轮boss战斗。'
                await bot.finish(ev, msg)
            else:
                msg = f'{c.name}今日已战斗过了，无法继续战斗了哦，请替换其他的女友出战哦。'
                await bot.finish(ev, msg)
    #print("开始会战")
    z_ce=0
    bianzu=''
    #获取本群boss状态和血量
    bossinfo = get_boss_info(sendgid)
    #print(bossinfo)
    if len(bossinfo)>0:
        #获取编队战力与信息
        for cid in defen:
            c = chara.fromid(cid)
            card_ce=get_card_ce(gid,uid,cid)
            z_ce=z_ce+card_ce
            bianzu=bianzu+f"{c.name} "
        #
        boss_ce = bossinfo['ce']
        msg1=f"[CQ:at,qq={uid}]编组成功{bianzu}\n开始进入会战\n当前boss为：第{bossinfo['zhoumu']}周目{bossinfo['bossid']}号boss({bossinfo['name']})\nboss战力为{bossinfo['ce']}，当前血量为{bossinfo['hp']}\n您的编组战力为{z_ce}，开始战斗\n{bossinfo['icon']}"
        tas_list = []
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":msg1
                    }
                }
        tas_list.append(data)
        
        #计算造成的伤害
        #2者相加的总战力
        zhanlz = boss_ce + z_ce
        #计算总战力扩值
        kuo = zhanlz * zhanlz
        #计算总战力差值
        cha = (zhanlz/z_ce)
        #计算无战力压制因素的输出伤害
        shuchu = (kuo/boss_ce)/cha
        #计算战力压制因素印象可以造成的伤害比
        zhanbi = z_ce/zhanlz+1
        #计算输出浮动数+-10%
        fudong = int(math.floor( random.uniform(1,20) ))
        if fudong>10:
            fudong = fudong/200+1
        else:
            fudong = 1-fudong/100
        #计算最终输出伤害
        shanghai = math.ceil((shuchu * fudong)/zhanbi)
        msg = ''
        #for cid in defen:
            #duel._add_favor(gid,uid,cid,dungeoninfo['add_favor'])
            #card_level=add_exp(gid,uid,cid,bossinfo['add_exp'])
        #判断造成的伤害是否大于boss血量
        card_jk = 0
        if shanghai>bossinfo['hp']:
            #计算健康状态
            card_jk = 100-math.ceil(bossinfo['hp']/shanghai*100)
            #计算下一个boss
            nextboss = bossinfo['bossid'] + 1
            nextzhoumu = bossinfo['zhoumu']
            nexthp = 0
            if nextboss == 6:
                nextboss = 1
                nextzhoumu = bossinfo['zhoumu'] + 1
            nextbossinfo = get_nextbossinfo(nextzhoumu,nextboss,shijieflag)
            boss_msg = f"击杀了boss\n下一个boss为：第{nextzhoumu}周目{nextboss}号boss({nextbossinfo['name']})"
            msg = msg + f"您对boss造成了{shanghai}点伤害，{boss_msg}\n由于伤害超出boss剩余血量，实际造成伤害为{bossinfo['hp']}点\n您的队伍剩余血量{card_jk}%，请输入指令‘{gotype}补时刀’进入下一轮boss战斗\n{nextbossinfo['icon']}"
        else:
            #每日次数-1
            daily_boss_limiter.increase(guid)
            #计算下一个boss
            nextboss = bossinfo['bossid']
            nextzhoumu = bossinfo['zhoumu']
            nexthp = 0
            if shanghai==bossinfo['hp']:
                nextboss = bossinfo['bossid'] + 1
                if nextboss == 6:
                    nextboss = 1
                    nextzhoumu = bossinfo['zhoumu'] + 1
                nextbossinfo = get_nextbossinfo(nextzhoumu,nextboss,shijieflag)
                boss_msg = f"击杀了boss\n下一个boss为：第{nextzhoumu}周目{nextboss}号boss({nextbossinfo['name']}){nextbossinfo['icon']}"
            else:
                now_hp = bossinfo['hp'] - shanghai
                nexthp = now_hp
                boss_msg = f"boss剩余血量{now_hp}点"
            msg = msg + f"您对boss造成了{shanghai}点伤害，{boss_msg}"
        CE._up_bossinfo(sendgid, nextzhoumu, nextboss, nexthp)
        CE._add_bossfight(gid, uid, bossinfo['zhoumu'], bossinfo['bossid'], shanghai, shijieflag)
        for cid in defen:
            CE._add_cardfight(gid, uid, cid, fighttime, card_jk, shijieflag)
            card_level=add_exp(gid,uid,cid,bossinfo['add_exp'])
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":msg
                    }
                }
        tas_list.append(data)
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=tas_list)
        await asyncio.sleep(3)
        #await bot.send(ev, '计算boss掉落')
        #判断是否击杀boss，分配boss掉落
        if shanghai>=bossinfo['hp']:
            #获取boss伤害输出表
            group_list=[]
            awardlist = []
            awardnum = 0
            shuchulist = CE._get_shuchulist(sendgid, bossinfo['zhoumu'], bossinfo['bossid'], shijieflag)
            for shuchu in shuchulist:
                if awardnum < 3:
                    awardlist.append(shuchu[2])
                awardnum += 1
                if shuchu[0] not in group_list:
                    group_list.append(shuchu[0])
            for groupid in group_list:
                tas_list = []
                data = {
                    "type": "node",
                    "data": {
                        "name": "会战系统",
                        "uin": "794275021",
                        "content":f"{gotype}战况：\n第{bossinfo['zhoumu']}周目{bossinfo['bossid']}号boss({bossinfo['name']})\n已被打死，开始分配boss掉落"
                            }
                        }
                tas_list.append(data)
                for shuchu in shuchulist:
                    if groupid == shuchu[0]:
                        get_equip = ''
                        get_awardequip = ''
                        for y in range(bossinfo['dropnum']):
                            equip_info = add_equip_info(shuchu[0],shuchu[1],bossinfo['dropequip'],bossinfo['equip'])
                            get_equip = get_equip + f"{equip_info['model']}品质{equip_info['type']}:{equip_info['name']}\n"
                        if shuchu[2] in awardlist:
                            awardequip_info = add_equip_info(shuchu[0],shuchu[1],bossinfo['awardequip'],bossinfo['awardlist'])
                            get_awardequip = get_awardequip + f"由于您的本次输出为前三名，额外获得装备：{awardequip_info['model']}品质{awardequip_info['type']}:{awardequip_info['name']}\n"
                        data = {
                            "type": "node",
                            "data": {
                                "name": "会战系统",
                                "uin": "794275021",
                                "content":f"[CQ:at,qq={shuchu[1]}]您对boss造成了{shuchu[2]}点伤害，获得了装备\n{get_equip}{get_awardequip}"
                                    }
                                }
                        tas_list.append(data)
                await bot.send_group_forward_msg(group_id=groupid, messages=tas_list)
    else:
        await bot.finish(ev, '无法获取boss信息', at_sender=True)
        return


@sv.on_fullmatch(['会战系统帮助','会战帮助'])
async def boss_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             会战系统帮助
1. boss战状态
2. 编队+女友名(最多5名，用空格隔开)开始boss战
3. 编队+女友名(最多5名，用空格隔开)模拟boss战
4. boss战补时刀
5. boss战伤害排行 ->查询个人伤害在本群中的排行
6. 会战群排名[+上月] ->查询本群在所有群中的排行
注:
boss战每日3次次数，打死一个boss有装备掉落
每月会进行boss重置和奖励结算，根据群排行最多可获得4000副本币！
╚                                        ╝
 '''  
    await bot.send(ev, msg)

@sv.on_rex(f'^(.*)伤害排行$')
async def shuchu_list(bot, ev: CQEvent):
    gid = ev.group_id
    CE = CECounter()
    match = ev['match']
    gotype = str(match.group(1))
    gotype = re.sub(r'[?？，,_ ]', '', gotype)
    if gotype == "世界boss":
        await bot.finish(ev, '世界boss已下线，请使用boss战。', at_sender=True)
    elif gotype == "boss战":
        sendgid = gid
        shijieflag = 0
    else:
        await bot.finish(ev, '请选择正确的boss战类型（boss战）', at_sender=True)
    shuchu_list = CE._get_shuchu_pm(gid, shijieflag)
    
    if shuchu_list == 0:
        await bot.finish(ev, f'本群没有{gotype}的出刀记录哦', at_sender=True)
    tas_list = []
    for shuchu in shuchu_list:
        #print(shuchu)
        data = {
            "type": "node",
            "data": {
                "name": "会战系统",
                "uin": "794275021",
                "content":f"[CQ:at,qq={shuchu[0]}]总共造成了{shuchu[1]}点伤害"
                    }
                }
        tas_list.append(data)
    await bot.send_group_forward_msg(group_id=gid, messages=tas_list)

@sv.on_rex(f'^(.*)状态$')
async def boss_info(bot, ev: CQEvent):
    gid = ev.group_id
    match = ev['match']
    gotype = str(match.group(1))
    gotype = re.sub(r'[?？，,_ ]', '', gotype)
    if gotype == "世界boss":
        await bot.send(ev, '世界boss已下线，请使用boss战。')
        return
    elif gotype == "boss战":
        sendgid = gid
        shijieflag = 0
    else:
        return
    bossinfo = get_boss_info(sendgid)
    msg = f"当前boss状态为：\n第{bossinfo['zhoumu']}周目{bossinfo['bossid']}号boss({bossinfo['name']})\nboss战力为{bossinfo['ce']}，当前血量为{bossinfo['hp']}\n{bossinfo['icon']}"
    await bot.send(ev, msg)

@sv.on_prefix(['群排名','会战群排名'])
async def paiming_list(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args)!=1:
        leibie = '本月'
    else:
        leibie = args[0]
    if leibie == "本月":
        nowyear = datetime.now().year
        nowmonth = datetime.now().month
        period = str(nowyear) + str(nowmonth)
    elif leibie == "上月":
        nowyear = datetime.now().year
        nowmonth = datetime.now().month
        if nowmonth == 1:
            nowyear = nowyear - 1
            nowmonth = 12
        else:
            nowyear = nowyear
            nowmonth = nowmonth - 1
        period = str(nowyear) + str(nowmonth)
    else:
        await bot.finish(ev, '请选择正确的时间(本月/上月)', at_sender=True)
    
    shuchu_list = CE._get_shuchu_pmq(period)
    if not shuchu_list[0][0]:
        await bot.finish(ev, f'无法获取到{leibie}的数据', at_sender=True)
    bosslist={}
    with open(os.path.join(FILE_PATH,'bossinfo.json'),'r',encoding='UTF-8') as fa:
        bosslist = json.load(fa, strict=False)
    bl_list = []
    for boss in bosslist:
        bv=[]
        for j in bosslist[boss]['bosslist']:
            bv_boss = bosslist[boss]['bosslist'][j]['fenshu']
            bv.append(bv_boss)
        for i in bosslist[boss]['zhoumu']:
            bl_list.append(bv)
    #print(bl_list)
    group_list = []
    for shuchu in shuchu_list:
        if shuchu[0] not in group_list:
            group_list.append(shuchu[0])
    msg_b = ''
    grouplist_b = []
    for groupid in group_list:
        defen_b = 0
        for shuchuinfo in shuchu_list:
            if shuchuinfo[0] == groupid:
                zhoumu = shuchuinfo[2] - 1
                bossid = shuchuinfo[3] - 1
                beilv = bl_list[zhoumu][bossid]
                defen = math.ceil(shuchuinfo[4] * beilv)
                if shuchuinfo[5] == 1:
                    continue
                defen_b = defen_b + defen
        grouplist_b.append([groupid, defen_b])

    grouplist_b = sorted(grouplist_b, key=lambda cus: cus[1], reverse=True)

    msg_b = ''
    mingc_b = 1
    for info in grouplist_b:
        if info[0] == gid:
            groupid = info[0]
            msg_s_b = f"本群{leibie}总积分{info[1]},排名第{mingc_b}名\n"
        else:
            groupid = str(info[0])
            groupid = str(groupid[:3]) + '****' + str(groupid[-3:])
        msg_b = msg_b + f"群号：{groupid}，总积分：{info[1]},名次：{mingc_b}\n"
        mingc_b = mingc_b + 1

    await bot.send(ev, f"{msg_s_b}{leibie}boss战群排行榜\n{msg_b}")

@sv.scheduled_job('cron', hour ='*',)
async def boss_monthly_clock():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    nowyear = now.year
    nowmonth = now.month
    nowday = now.day
    if not now.day == 1: #每月1号结算
        return
    if not now.hour == 1: #每天1点结算
        return 
    
    jianglilist={
        1:4000,
        2:3500,
        3:3000,
        4:2500,
        5:2500,
        6:2500,
        7:2000,
        8:2000,
        9:2000,
        10:2000,
        11:1500,
        12:1500,
        13:1500,
        14:1500,
        15:1500,
        16:1000,
        17:1000,
        18:1000,
        19:1000,
        20:1000,
    }
    
    bot = nonebot.get_bot()
    CE = CECounter()

    nowyear = datetime.now().year
    nowmonth = datetime.now().month
    if nowmonth == 1:
        nowyear = nowyear - 1
        nowmonth = 12
    else:
        nowyear = nowyear
        nowmonth = nowmonth - 1
    period = str(nowyear) + str(nowmonth)
    
    shuchu_list = CE._get_shuchu_pmq(period)
    bosslist={}
    with open(os.path.join(FILE_PATH,'bossinfo.json'),'r',encoding='UTF-8') as fa:
        bosslist = json.load(fa, strict=False)
    bl_list = []
    for boss in bosslist:
        bv=[]
        for j in bosslist[boss]['bosslist']:
            bv_boss = bosslist[boss]['bosslist'][j]['fenshu']
            bv.append(bv_boss)
        for i in bosslist[boss]['zhoumu']:
            bl_list.append(bv)
    #print(bl_list)
    group_list = []
    for shuchu in shuchu_list:
        if shuchu[0] not in group_list:
            group_list.append(shuchu[0])
    msg_b = ''
    grouplist_b = []
    for groupid in group_list:
        defen_b = 0
        for shuchuinfo in shuchu_list:
            if shuchuinfo[0] == groupid:
                zhoumu = shuchuinfo[2] - 1
                bossid = shuchuinfo[3] - 1
                beilv = bl_list[zhoumu][bossid]
                defen = math.ceil(shuchuinfo[4] * beilv)
                if shuchuinfo[5] == 1:
                    continue
                defen_b = defen_b + defen
        grouplist_b.append([groupid, defen_b])

    grouplist_b = sorted(grouplist_b, key=lambda cus: cus[1], reverse=True)

    mingcilist_b = {}
    mingc_b = 1
    for info in grouplist_b:
        mingcilist_b[info[0]] = mingc_b
        mingc_b = mingc_b + 1

    for groupid in group_list:
        gidmc_b = mingcilist_b.get(groupid)
        if gidmc_b is None:
            continue
        gidjl_b = jianglilist[gidmc_b]
        tas_list_b = []
        uidlist_b = []
        data = {
            "type": "node",
            "data": {
                "name": "BOSS战月排行奖励发放",
                "uin": "794275021",
                "content":f"本群boss战群排名第{gidmc_b}名，获得奖励"
                    }
                }
        tas_list_b.append(data)
        for shuchuinfo in shuchu_list:
            if shuchuinfo[0] == groupid:
                if shuchuinfo[5] == 1:
                    continue
                if shuchuinfo[1] not in uidlist_b:
                    uidlist_b.append(shuchuinfo[1])
                    CE._add_dunscore(groupid, shuchuinfo[1], gidjl_b)
                    data = {
                        "type": "node",
                        "data": {
                            "name": "奖励",
                            "uin": "794275021",
                            "content":f"[CQ:at,qq={shuchuinfo[1]}]您获得了{gidjl_b}副本币"
                                }
                            }
                    tas_list_b.append(data)
        await bot.send_group_forward_msg(group_id=groupid, messages=tas_list_b)