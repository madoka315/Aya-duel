# -*- coding: utf-8 -*-
"""战斗：副本/装备/副本商城/抽卡"""
from datetime import datetime
from decimal import Decimal
from hoshino.typing import CQEvent
import asyncio
import json
import math
import os
import random
import re
from .. import chara
from .. import sv
from ..core.constants import FILE_PATH, G2DUN_LIMIT, GECHA_DUNDCORE, GIFT_DICT
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import add_equip_info, add_exp, get_card_ce, get_dun_info, get_equip_info_id, get_equip_info_name, get_gecha_equip, get_gecha_info
from ..core.state import daily_GOLDTODUN_limiter, daily_dun_limiter, daily_equip_limiter


    
@sv.on_fullmatch(['副本系统帮助','副本帮助','装备帮助'])
async def dun_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             副本系统帮助
1. 编队+女友名(最多5名，用空格隔开)进入副本+副本名称
*可以[创建队伍+女友名+队名xxx]后，使用队名进入副本
2. 装备列表（查询我未穿戴的装备列表）
3. 穿装备+女友名+装备名(一键穿戴+女友名)
4. 取消装备+女友名+装备名(一键取消+女友名)
5. 副本列表
6. 副本商城（兑换装备 + 装备名）
7. 用金币兑换副本币（每日比例随机）
注:
通过副本战斗可以获得角色经验，好感度，礼物与装备产出
升级角色等级，装备装备可以提升角色战力
╚                                        ╝
 '''  
    await bot.send(ev, msg)  

@sv.on_fullmatch(['副本列表','查看副本'])
async def dungeon_list(bot, ev: CQEvent):
    dungeonlist={}
    with open(os.path.join(FILE_PATH,'dungeon.json'),'r',encoding='UTF-8') as fa:
        dungeonlist = json.load(fa, strict=False)  
    tas_list = []
    for dungeon in dungeonlist:
        msg = ''
        msg = msg + f"\n副本名  ：{dungeonlist[dungeon]['name']}"
        msg = msg + f"\n副本难度：{dungeonlist[dungeon]['model']}"
        msg = msg + f"\n推荐战力：{dungeonlist[dungeon]['recommend_ce']}"
        msg = msg + f"\n战胜获得经验：{dungeonlist[dungeon]['add_exp']}"
        msg = msg + f"\n战胜获得好感：{dungeonlist[dungeon]['add_favor']}"
        msg = msg + f"\n副本描述：{dungeonlist[dungeon]['content']}"
        data = {
            "type": "node",
            "data": {
                "name": "副本列表",
                "uin": "794275021",
                "content": msg
                    }
                }
        tas_list.append(data)
    #await bot.send(ev, msg)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=tas_list)
    
@sv.on_rex(f'^编队(.*)进入副本(.*)$')
async def add_duiwu(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    # 处理输入数据
    match = ev['match']
    dunname = str(match.group(2))
    dunname = re.sub(r'[?？，,_ ]', '', dunname)
    defen = str(match.group(1))
    defen = re.sub(r'[?？，,_]', '', defen)
    if not defen:
        await bot.finish(ev, '请发送"编队+女友名/队伍名+进入副本+副本名"，无需+号', at_sender=True)
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
    z_ce=0
    bianzu=''
    dungeoninfo=get_dun_info(dunname)
    if dungeoninfo:
        #获取编队战力与信息
        for cid in defen:
            c = chara.fromid(cid)
            nvmes = c.icon.cqcode
            owner = duel._get_card_owner(gid, cid)
            if owner == 0:
                await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
                return
            if uid!=owner:
                msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法编队哦。'
                await bot.send(ev, msg)
                return
            card_ce=get_card_ce(gid,uid,cid)
            z_ce=z_ce+card_ce
            bianzu=bianzu+f"{c.name} "
        #获取进入副本信息
        #判定每日上限
        guid = gid ,uid
        if not daily_dun_limiter.check(guid):
            await bot.send(ev, '今天的副本次数已经超过上限了哦，明天再来吧。', at_sender=True)
            return
        daily_dun_limiter.increase(guid)
        recommend_ce = dungeoninfo['recommend_ce']
        is_win = Decimal(z_ce/recommend_ce).quantize(Decimal('0.00'))*100
        if is_win>100:
            is_win=100
        msg1=f"编组成功{bianzu}\n开始进入副本{dunname}\n当前副本推荐战力{recommend_ce}，您的编组战力为{z_ce}，您的胜率为{is_win}%，开始战斗"
        await bot.send(ev, msg1, at_sender=True)
        await asyncio.sleep(5)
        if_win = int(math.floor( random.uniform(1,100) ))
        #战斗胜利
        if if_win<=is_win:
            msg = "战斗胜利了！\n"
            for cid in defen:
                duel._add_favor(gid,uid,cid,dungeoninfo['add_favor'])
                card_level=add_exp(gid,uid,cid,dungeoninfo['add_exp'])
            msg = msg + f"您的女友们获得了{dungeoninfo['add_exp']}点经验，{dungeoninfo['add_favor']}点好感\n"
            #增加副本币
            CE._add_dunscore(gid, uid, dungeoninfo['dun_score'])
            msg = msg + f"您获得了{dungeoninfo['dun_score']}副本币\n"
            msg = msg + "您获得的战利品为：\n"
            favor_ran = int(math.floor( random.uniform(1,100) ))
            z_favor = 0
            dun_get_favor = 0
            for favor_num in dungeoninfo['drop']['favor']:
                z_favor = z_favor + dungeoninfo['drop']['favor'][favor_num]
                if z_favor>=favor_ran:
                    dun_get_favor = int(favor_num)
                    break
            gift_list = ''
            for x in range(dun_get_favor):
                select_gift = random.choice(list(GIFT_DICT.keys()))
                gfid = GIFT_DICT[select_gift]
                duel._add_gift(gid,uid,gfid)
                gift_list = gift_list + f"[{select_gift}] "
            msg = msg + f'获得了礼物:\n{gift_list}\n'
            equip_ran = int(math.floor( random.uniform(1,100) ))
            z_equip = 0
            dun_get_equip = 0
            for equip_num in dungeoninfo['drop']['equipment']['num']:
                z_equip = z_equip + dungeoninfo['drop']['equipment']['num'][equip_num]
                if z_equip>=equip_ran:
                    dun_get_equip = int(equip_num)
                    break
            equip_list = ''
            if dun_get_equip>0:
                for y in range(dun_get_equip):
                    equip_type_run = int(math.floor( random.uniform(1,100) ))
                    get_equip_quality = 1
                    z_equip_quality = 0
                    for equip_num_quality in dungeoninfo['drop']['equipment']['quality']:
                        z_equip_quality = z_equip_quality + dungeoninfo['drop']['equipment']['quality'][equip_num_quality]
                        if z_equip_quality>=equip_type_run:
                            get_equip_quality = int(equip_num_quality)
                            break
                    down_list=[]
                    for equip_down in dungeoninfo['drop']['equipment']['equip']:
                        if int(get_equip_quality) == int(equip_down):
                            down_list = dungeoninfo['drop']['equipment']['equip'][equip_down]
                    #随机获得一个品质的装备
                    equip_info = add_equip_info(gid,uid,get_equip_quality,down_list)
                    #print(equip_info)
                    equip_list = equip_list + f"{equip_info['model']}品质{equip_info['type']}:{equip_info['name']}\n"
            if equip_list:
                 msg = msg + f"获得了装备:\n{equip_list}"
            await bot.send(ev, msg, at_sender=True)
        else:
            await bot.send(ev, "您战斗失败了，副本次数-1", at_sender=True)
            return
    else:
        await bot.finish(ev, '请输入正确的副本名称', at_sender=True)
        return

@sv.on_prefix(['取消装备'])
async def equip_unequip(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()  
    if len(args)!=2:
        await bot.finish(ev, '请输入 取消装备+女友名+装备名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    equipname = args[1]
    equipinfo = get_equip_info_name(equipname)
    if len(equipinfo)>0:
        c = chara.fromid(cid)
        CE = CECounter()
        now_dress = CE._get_dress_info(gid, uid, cid, equipinfo['type_id'])
        if now_dress>0:
            if now_dress == equipinfo['eid']:
                now_equipinfo = get_equip_info_id(now_dress)
                #保存数据库
                CE._dress_equip(gid, uid, cid, equipinfo['type_id'], 0)
                #可用装备加一
                CE._add_equip(gid, uid, equipinfo['eid'], 1)

                msg_x = f"取消了{equipinfo['type']}部位的装备{equipinfo['name']}"
                nvmes = c.icon.cqcode
                msg = f"您为您的女友{c.name}，{msg_x}\n{nvmes}"
                await bot.send(ev, msg, at_sender=True)   
            else:
                msg = f"您的女友{c.name}，当前{equipinfo['type']}部位穿戴的装备是{now_equipinfo['name']}，不是{equipinfo['name']}哦！"
                await bot.finish(ev, msg, at_sender=True)
        else:
            await bot.finish(ev, f"您的女友{c.name}当前{equipinfo['type']}部位未穿戴装备哦。", at_sender=True)
    else:
        await bot.finish(ev, '请输入正确的装备名。', at_sender=True)

@sv.on_prefix(['穿装备','穿戴装备'])
async def equip_dress(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()  
    if len(args)!=2:
        await bot.finish(ev, '请输入 穿装备+女友名+装备名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    equipname = args[1]
    equipinfo = get_equip_info_name(equipname)
    if len(equipinfo)>0:
        c = chara.fromid(cid)
        CE = CECounter()
        if CE._get_equip_num(gid,uid,equipinfo['eid'])==0:
            await bot.finish(ev, '你的这件装备的库存不足哦。', at_sender=True)
        #获取当前穿戴的装备
        now_dress = CE._get_dress_info(gid, uid, cid, equipinfo['type_id'])
        #保存数据库
        CE._dress_equip(gid, uid, cid, equipinfo['type_id'], equipinfo['eid'])
        #可用装备减一
        CE._add_equip(gid, uid, equipinfo['eid'], -1)
        if now_dress>0:
            now_equipinfo = get_equip_info_id(now_dress)
            #替换的装备数量增加
            CE._add_equip(gid, uid, now_dress, 1)
            msg_x = f"取消了{equipinfo['type']}部位的装备{now_equipinfo['name']}，穿上了装备{equipinfo['name']}"
        else:
            msg_x = f"穿上了{equipinfo['type']}部位的装备{equipinfo['name']}"
        nvmes = c.icon.cqcode
        msg = f"您为您的女友{c.name}，{msg_x}\n{nvmes}"
        await bot.send(ev, msg, at_sender=True)    
    else:
        await bot.finish(ev, '请输入正确的装备名。', at_sender=True)

@sv.on_fullmatch(['装备列表','我的装备'])
async def my_equip_list(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter() 
    CE = CECounter()
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    equip_list = CE._get_equip_list(gid, uid)
    if len(equip_list)>0:
        msg_list = '我的装备列表：'
        for i in equip_list:
            equipinfo=get_equip_info_id(i[0])
            msg_list = msg_list + f"\n{equipinfo['type']}:({equipinfo['model']}){equipinfo['name']}:{i[1]}件"
        await bot.send(ev, msg_list, at_sender=True)
    else:
        await bot.finish(ev, '您还没有获得装备哦。', at_sender=True)

@sv.on_prefix(['一键穿戴'])
async def dress_equip_list(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 一键穿戴+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    
    equip_list = CE._get_equip_list(gid, uid)
    #记录不同部位的品质最高装备的品质和eid
    emax = [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
    if len(equip_list)>0:
        msg_list = '我的装备列表：'
        for i in equip_list:
            equipinfo=get_equip_info_id(i[0])
            if equipinfo['type_id'] == 1 and equipinfo['level'] > emax[0][0] and equipinfo['add_ce'] > emax[0][2]:
                emax[0] = [equipinfo['level'],i[0],equipinfo['add_ce']]
            if equipinfo['type_id'] == 2 and equipinfo['level'] > emax[1][0] and equipinfo['add_ce'] > emax[1][2]:
                emax[1] = [equipinfo['level'],i[0],equipinfo['add_ce']]
            if equipinfo['type_id'] == 3 and equipinfo['level'] > emax[2][0] and equipinfo['add_ce'] > emax[2][2]:
                emax[2] = [equipinfo['level'],i[0],equipinfo['add_ce']]
            if equipinfo['type_id'] == 4 and equipinfo['level'] > emax[3][0] and equipinfo['add_ce'] > emax[3][2]:
                emax[3] = [equipinfo['level'],i[0],equipinfo['add_ce']]
    else:
        await bot.finish(ev, '您还没有获得装备哦。', at_sender=True)
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    msg = ''
    for y in emax:
        if y[1] > 0:
            #获取当前穿戴的装备
            equipinfo = get_equip_info_id(y[1])
            now_dress = CE._get_dress_info(gid, uid, cid, equipinfo['type_id'])
            if now_dress>0:
                now_equipinfo = get_equip_info_id(now_dress)
                if now_equipinfo['level'] < y[0] or now_equipinfo['add_ce'] < y[2]:
                    #保存数据库
                    CE._dress_equip(gid, uid, cid, equipinfo['type_id'], equipinfo['eid'])
                    #可用装备减一
                    CE._add_equip(gid, uid, equipinfo['eid'], -1)
                    #替换的装备数量增加
                    CE._add_equip(gid, uid, now_dress, 1)
                    msg = msg + f"取消了{equipinfo['type']}部位的装备({now_equipinfo['model']}){now_equipinfo['name']}，穿上了装备({equipinfo['model']}){equipinfo['name']}\n"
                else:
                    msg = msg + f"{equipinfo['type']}部位已穿戴同等或更高等级的装备({now_equipinfo['model']}){now_equipinfo['name']}，无替换\n"
            else:
                #保存数据库
                CE._dress_equip(gid, uid, cid, equipinfo['type_id'], equipinfo['eid'])
                #可用装备减一
                CE._add_equip(gid, uid, equipinfo['eid'], -1)
                msg = msg + f"穿上了{equipinfo['type']}部位的装备({equipinfo['model']}){equipinfo['name']}\n"
    await bot.send(ev, f"您为您的女友{c.name}\n{msg}{nvmes}", at_sender=True)


@sv.on_prefix(['一键装备'])
async def dress_equip_list_r(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 一键穿戴+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    rank = CE._get_rank(gid, uid, cid)
    lastrank = rank+1
    if lastrank<=3:
        needmodel = 'N'
        needlevel = 1
    elif lastrank>3 and lastrank<6:
        needmodel = 'R'
        needlevel = 2
    else:
        needmodel = 'SR'
        needlevel = 3
    equip_list = CE._get_equip_list(gid, uid)
    #记录不同部位的品质最高装备的品质和eid
    emax = [[0,0],[0,0],[0,0],[0,0]]
    if len(equip_list)>0:
        msg_list = '我的装备列表：'
        for i in equip_list:
            equipinfo=get_equip_info_id(i[0])
            if equipinfo['type_id'] == 1 and equipinfo['level'] <= needlevel and equipinfo['level'] > emax[0][0]:
                emax[0] = [equipinfo['level'],i[0]]
            if equipinfo['type_id'] == 2 and equipinfo['level'] <= needlevel and equipinfo['level'] > emax[1][0]:
                emax[1] = [equipinfo['level'],i[0]]
            if equipinfo['type_id'] == 3 and equipinfo['level'] <= needlevel and equipinfo['level'] > emax[2][0]:
                emax[2] = [equipinfo['level'],i[0]]
            if equipinfo['type_id'] == 4 and equipinfo['level'] <= needlevel and equipinfo['level'] > emax[3][0]:
                emax[3] = [equipinfo['level'],i[0]]
    else:
        await bot.finish(ev, '您还没有获得装备哦。', at_sender=True)
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    msg = ''
    for y in emax:
        if y[1] > 0:
            #获取当前穿戴的装备
            equipinfo = get_equip_info_id(y[1])
            now_dress = CE._get_dress_info(gid, uid, cid, equipinfo['type_id'])
            if now_dress>0:
                now_equipinfo = get_equip_info_id(now_dress)
                if now_equipinfo['level'] < y[0]:
                    #保存数据库
                    CE._dress_equip(gid, uid, cid, equipinfo['type_id'], equipinfo['eid'])
                    #可用装备减一
                    CE._add_equip(gid, uid, equipinfo['eid'], -1)
                    #替换的装备数量增加
                    CE._add_equip(gid, uid, now_dress, 1)
                    msg = msg + f"取消了{equipinfo['type']}部位的装备({now_equipinfo['model']}){now_equipinfo['name']}，穿上了装备({equipinfo['model']}){equipinfo['name']}\n"
                else:
                    msg = msg + f"{equipinfo['type']}部位已穿戴同等或更高等级的装备({now_equipinfo['model']}){now_equipinfo['name']}，无替换\n"
            else:
                #保存数据库
                CE._dress_equip(gid, uid, cid, equipinfo['type_id'], equipinfo['eid'])
                #可用装备减一
                CE._add_equip(gid, uid, equipinfo['eid'], -1)
                msg = msg + f"穿上了{equipinfo['type']}部位的装备({equipinfo['model']}){equipinfo['name']}\n"
    await bot.send(ev, f"您为您的女友{c.name}\n{msg}{nvmes}", at_sender=True)

@sv.on_fullmatch(['副本商城'])
async def equip_shop(bot, ev: CQEvent):
    equiplist={}
    with open(os.path.join(FILE_PATH,'equipment.json'),'r',encoding='UTF-8') as fa:
        equiplist = json.load(fa, strict=False)  
    tas_list = []
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    myscore = CE._get_dunscore(gid, uid)
    msg_t = f"您的副本币为{myscore}，每日可以兑换装备5次"
    #合并转发： 
    data = {
        "type": "node",
        "data": {
            "name": "副本商城",
            "uin": "794275021",
            "content": msg_t
                }
            }
    tas_list.append(data)
    #await bot.send(ev, msg_t)
    for equip in equiplist:
        shul = 0
        msg = ''
        for eid in equiplist[equip]['e_list']:
            if equiplist[equip]['e_list'][eid]['dun_score'] > 0:
                shul += 1
                msg = msg + f"装备信息：[{equiplist[equip]['e_list'][eid]['type']}]{equiplist[equip]['e_list'][eid]['name']}\n装备品质：{equiplist[equip]['model']}\n售价(副本币)：{equiplist[equip]['e_list'][eid]['dun_score']}\n"
        if shul>0:
            #合并转发： 
            data = {
                "type": "node",
                "data": {
                    "name": "副本商城",
                    "uin": "794275021",
                    "content":msg
                        }
                    }
            tas_list.append(data)
            #await bot.send(ev, msg)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=tas_list)

@sv.on_prefix(['兑换装备'])
async def buy_equip(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    #判定每日上限
    guid = gid ,uid
    if not daily_equip_limiter.check(guid):
        await bot.send(ev, '今天的兑换次数已经超过上限了哦，明天再来吧。', at_sender=True)
        return
    if not args:
        await bot.send(ev, '请输入兑换装备+装备名称。', at_sender=True)
        return
    equipinfo = get_equip_info_name(args[0])
    if len(equipinfo)>0:
        if equipinfo['dun_score']>0:
            myscore = CE._get_dunscore(gid, uid)
            if myscore < equipinfo['dun_score']:
                await bot.finish(ev, f"您的副本币不足，兑换{equipinfo['name']}需要{equipinfo['dun_score']}哦。", at_sender=True)
            daily_equip_limiter.increase(guid)
            need_score = 0 - equipinfo['dun_score']
            last_score = myscore - equipinfo['dun_score']
            CE._add_dunscore(gid, uid, need_score)
            CE._add_equip(gid, uid, equipinfo['eid'], 1)
            msg = f"兑换装备({equipinfo['model']}){equipinfo['type']}:{equipinfo['name']}成功，消耗副本币{equipinfo['dun_score']}，您剩余副本币为{last_score}"
            await bot.send(ev, msg, at_sender=True) 
        else:
            await bot.finish(ev, '限购商品无法兑换哦。', at_sender=True)
    else:
        await bot.finish(ev, '请输入正确的装备名。', at_sender=True)

@sv.on_fullmatch(['抽卡系统帮助','抽卡帮助'])
async def gecha_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             抽卡系统帮助
1. 查看武器池 (查看当前武器池)
2. 抽装备+(单抽/十连)+装备池名称 (抽取武器)
3. 我的保底 (查看我的保底情况)
4. 查副本币/我的副本币 (查看我剩余的副本币)
5. 装备分解+装备名 (分解装备)
6. 一键分解+装备等级(N/R/SR/SSR/UR/MR) (一键分解指定等级及以下的装备)
注:
副本币获取其他路径：通关每日副本
╚                                        ╝
 '''
    await bot.send(ev, msg)

@sv.on_fullmatch(['查看武器池','武器池'])
async def get_equipgecha(bot, ev: CQEvent):
    gechalist={}
    with open(os.path.join(FILE_PATH,'equipgecha.json'),'r',encoding='UTF-8') as fa:
        gechalist = json.load(fa, strict=False)  
    tas_list = []
    for gecha in gechalist:
        meg = ''
        meg = meg + f"武器池名称：{gechalist[gecha]['name']}\n"
        equiplist = ''
        for eid in gechalist[gecha]['up_equip']:
            equipinfo = get_equip_info_id(eid)
            equiplist = equiplist + f"[{equipinfo['name']}] "
        meg = meg + f"up武器：{equiplist}\n"
        meg = meg + f"保底：第{gechalist[gecha]['up_num']}抽之前没有抽到SSR/SSR以上装备时，必定抽到SSR/SSR以上装备\n"
        gl_list = ''
        for level in gechalist[gecha]['gecha']['quality']:
            if level=='2':
                gl_name = 'R'
            if level=='3':
                gl_name = 'SR'
            if level=='4':
                gl_name = 'SSR'
            if level=='5':
                gl_name = 'UR'    
            gl_list = gl_list + f"{gl_name}:{gechalist[gecha]['gecha']['quality'][level]}%\n"
        meg = meg + f"概率公示：\n{gl_list}"
        data = {
            "type": "node",
            "data": {
                "name": "武器概率公示",
                "uin": "794275021",
                "content":meg
                    }
                }
        tas_list.append(data)
        
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=tas_list)

@sv.on_fullmatch(['我的保底','查看保底'])
async def get_my_baodi(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    bdinfo = CE._get_gecha_num(gid, uid)
    xnum = bdinfo[0]#10连小保底进度
    last_xnum = 10-xnum
    dnum = bdinfo[1]#大保底进度
    last_dnum = 100-dnum
    msg = f"您已经{xnum}次没有抽到SR/SR以上装备了，再抽{last_xnum}次必定获得SR/SR以上装备\n您已经{dnum}次没有抽到SSR/SSR以上装备了，再抽{last_dnum}次必定获得SSR/SSR以上装备"
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['我的副本币','查副本币'])
async def get_my_dunscore(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    myscore = CE._get_dunscore(gid, uid)
    await bot.send(ev, f"您的副本币为{myscore}", at_sender=True)

@sv.on_prefix(['抽装备'])
async def add_equip_gecha(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args)!=2:
        await bot.finish(ev, '请输入 抽装备+(单抽/十连)+装备池名称 中间用空格隔开。', at_sender=True)
    if args[0] == '单抽':
        gechanum = 1
    elif args[0] == '十连':
        gechanum = 10
    else:
        await bot.finish(ev, '请输入正确的抽取数量（单抽/十连）。', at_sender=True)
    if args[1] == '':
        await bot.finish(ev, '请输入装备池名称。', at_sender=True)
    need_dunscore = GECHA_DUNDCORE*gechanum
    myscore = CE._get_dunscore(gid, uid)
    if need_dunscore>myscore:
        await bot.finish(ev, f'您的副本币不足{need_dunscore}，无法抽卡哦。', at_sender=True)
    gechainfo = get_gecha_info(args[1])
    if gechainfo['name']:
        #print(gechainfo['name'])
        bdinfo = CE._get_gecha_num(gid, uid)
        xnum = bdinfo[0]#10连小保底进度
        dnum = bdinfo[1]#大保底进度
        getequip = get_gecha_equip(gid, uid, gechanum, xnum, dnum, gechainfo)
        last_score = myscore - need_dunscore
        need_score = 0-need_dunscore
        CE._add_dunscore(gid, uid, need_score)
        msg = f"消耗{need_dunscore}副本币，剩余副本币{last_score}\n本次{args[0]}获得的装备为：{getequip}"
        await bot.send(ev, msg, at_sender=True)
    else:
        await bot.finish(ev, '请输入正确的武器池名称。', at_sender=True)
    
@sv.on_prefix(['装备分解','分解装备'])
async def equip_fenjie_one(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 装备分解+装备名称 中间用空格隔开。', at_sender=True)
    equipinfo = get_equip_info_name(args[0])
    if len(equipinfo)>0:
        equipnum = CE._get_equip_num(gid,uid,equipinfo['eid'])
        if equipnum==0:
            await bot.finish(ev, '你的这件装备的库存不足哦。', at_sender=True)
        if equipinfo['level']<=3:
            chenji = 1
        else:
            chenji = 3
        fj_one = equipinfo['level']*chenji*10
        get_dunscore = fj_one * equipnum
        CE._add_dunscore(gid, uid, get_dunscore)
        deletenum = 0-equipnum
        CE._add_equip(gid, uid, equipinfo['eid'], deletenum)
        msg = f"您成功分解了{equipnum}件{equipinfo['model']}级装备，获得了{get_dunscore}副本币"
        await bot.send(ev, msg, at_sender=True)
    else:
        await bot.finish(ev, '请输入正确的装备名。', at_sender=True)
    
@sv.on_prefix(['一键分解'])
async def equip_fenjie_n(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 装备分解+装备等级(N/R/SR/SSR/UR/MR) 中间用空格隔开。', at_sender=True)
    modelname = args[0]
    equiplist={}
    with open(os.path.join(FILE_PATH,'equipment.json'),'r',encoding='UTF-8') as fa:
        equiplist = json.load(fa, strict=False)  
    equiplevel = 0
    for i in equiplist:
        if str(modelname) == str(equiplist[i]['model']):
            equiplevel = equiplist[i]['level']
            break
    if equiplevel == 0:
        await bot.finish(ev, '请输入正确的装备等级(N/R/SR/SSR/UR/MR)。', at_sender=True)
    
    equip_list = CE._get_equip_list(gid, uid)
    if len(equip_list)>0:
        msg_list = ''
        dunscore = 0
        for i in equip_list:
            equipinfo=get_equip_info_id(i[0])
            if equipinfo['level'] <= equiplevel:
                if equipinfo['level']<=3:
                    chenji = 1
                else:
                    chenji = 3
                fj_one = equipinfo['level']*chenji*10
                equipnum = i[1]
                get_dunscore = fj_one * equipnum
                dunscore = dunscore + get_dunscore
                deletenum = 0-equipnum
                CE._add_equip(gid, uid, equipinfo['eid'], deletenum)
                msg_list = msg_list + f"\n{equipnum}件{equipinfo['model']}级装备,{equipinfo['name']}"
        if dunscore>0:
            CE._add_dunscore(gid, uid, dunscore)
            msg = f"分解成功，您分解了{msg_list}\n一共获得了{dunscore}副本币"
            await bot.send(ev, msg, at_sender=True)
        else:
            await bot.finish(ev, f'您没有{modelname}级及以下的装备哦。', at_sender=True)
    else:
        await bot.finish(ev, '您还没有获得装备哦。', at_sender=True)
        
@sv.on_prefix(['星尘兑换'])
async def xngchen_change(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 星尘兑换+UP的武器名称 中间用空格隔开。', at_sender=True)
    xc_num = CE._get_xingchen_num(gid, uid)
    if xc_num<300:
        await bot.finish(ev, f'您的星尘剩余{xc_num}，不足300，无法兑换哦。', at_sender=True)
    equipinfo = get_equip_info_name(args[0])
    if len(equipinfo)>0:
        eid = equipinfo['eid']
        gechalist={}
        with open(os.path.join(FILE_PATH,'equipgecha.json'),'r',encoding='UTF-8') as fa:
            gechalist = json.load(fa, strict=False)  
        tas_list = []
        find_flag = 0
        for gecha in gechalist:
            if eid in gechalist[gecha]['up_equip']:
                find_flag = 1
                break
        if find_flag==0:
            await bot.finish(ev, f'{args[0]}目前没有UP哦。', at_sender=True)
        now_num = CE._add_xingchen_num(gid, uid, -300)
        CE._add_equip(gid, uid, equipinfo['eid'], 1)
        msg = f"您消耗了300星尘，成功兑换了装备{args[0]}，剩余星尘{now_num}"
        await bot.send(ev, msg, at_sender=True)
    else:
        await bot.finish(ev, '请输入正确的装备名称。', at_sender=True)
        
@sv.on_rex(f'^用(.*)金币兑换副本币$')
async def buy_duncoin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    guid = gid,uid
    CE = CECounter()
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    ritsu = random.Random(datetime.now().day + gid).choice([10,20,40,60,60,80,80,80,100,100,100])
    match = ev['match']
    if not (match.group(1)):
        await bot.finish(ev, f'请输入要兑换的金币数量哦\n本群今天的兑换比例为：{ritsu}:1')
    try:
        num = int(match.group(1))
    except Exception:
        await bot.finish(ev, f'请输入正确的金币数量！您今天还剩{G2DUN_LIMIT - daily_GOLDTODUN_limiter.checks(guid)}金币可以兑换！')
    if num > G2DUN_LIMIT - daily_GOLDTODUN_limiter.checks(guid) :
        await bot.finish(ev, f'超出兑换最大限额！您今天还剩{G2DUN_LIMIT - daily_GOLDTODUN_limiter.checks(guid)}金币可以兑换！', at_sender=True) 
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还没有在本群创建贵族哦。', at_sender = True)
    score = score_counter._get_score(gid, uid)
    if num > score:
        msg = f'您的金币只有{score}，无法兑换哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    dunscore = int(num/ritsu)
    score_counter._reduce_score(gid, uid, num)
    CE._add_dunscore(gid, uid, dunscore)
    scoreyou = score_counter._get_score(gid, uid)
    dunscoreyou = CE._get_dunscore(gid, uid)
    daily_GOLDTODUN_limiter.increase2(guid,num)
    msg = f'本群今天的兑换比例为：{ritsu}:1\n使用{num}金币兑换{dunscore}副本币成功\n您的副本币为{dunscoreyou}，金币剩余{scoreyou}。'
    await bot.send(ev, msg, at_sender = True)

@sv.on_prefix(['一键卸装','一键取消'])
async def quxiao_equip(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 一键取消+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.finish(ev, msg, at_sender=True)
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    dreeslist = CE._get_dress_list(gid, uid, cid)
    if len(dreeslist)>0:
        msg = ''
        for eid in dreeslist:
            equipinfo = get_equip_info_id(eid)
            if equipinfo:
                #保存数据库
                CE._dress_equip(gid, uid, cid, equipinfo['type_id'], 0)
                #替换的装备数量增加
                CE._add_equip(gid, uid, equipinfo['eid'], 1)
                msg = msg + f"取消了{equipinfo['type']}部位的装备({equipinfo['model']}){equipinfo['name']}\n"
        await bot.send(ev, f"您为您的女友{c.name}\n{msg}{nvmes}", at_sender=True)
    else:
        await bot.finish(ev, f"您的女友{c.name}目前没有穿戴的装备哦\n{nvmes}", at_sender = True)