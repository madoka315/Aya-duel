# -*- coding: utf-8 -*-
"""战斗：队伍"""
from hoshino.typing import CQEvent
import re
from .. import chara
from .. import sv
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.rules import get_card_ce



@sv.on_rex(f'^创建队伍(.*)队名(.*)$')
async def add_team(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id

    # 处理输入数据
    match = ev['match']
    
    teamname = str(match.group(2))
    teamname = re.sub(r'[?？，,_ ]', '', teamname)
    if not teamname:
        await bot.finish(ev, '请发送"创建队伍+女友名+队名+队伍名称"，无需+号', at_sender=True)
    defen = str(match.group(1))
    defen = re.sub(r'[?？，,_]', '', defen)
    defen, unknown = chara.roster.parse_team(defen)
    duel = DuelCounter()
    cidlist = duel._get_cards(gid, uid)
    if unknown:
        _, name, score = chara.guess_id(unknown)
        if score < 70 and not defen:
            return  # 忽略无关对话
        msg = f'无法识别"{unknown}"' if score < 70 else f'无法识别"{unknown}" 您说的有{score}%可能是{name}'
        await bot.finish(ev, msg)
    if not defen:
        await bot.finish(ev, '请发送"创建队伍+女友名+队名+队伍名称"，无需+号', at_sender=True)
    if len(defen) > 5:
        await bot.finish(ev, '编队不能多于5名角色', at_sender=True)
    if len(defen) != len(set(defen)):
        await bot.finish(ev, '编队中含重复角色', at_sender=True)
    if 1004 in defen:
        await bot.finish(ev, '\n⚠️您正在查询普通版炸弹人\n※万圣版可用万圣炸弹人/瓜炸等别称', at_sender=True)
    for cid in defen:
        c = chara.fromid(cid)
        nvmes = c.icon.cqcode
        owner = duel._get_card_owner(gid, cid)
        if owner == 0:
            await bot.finish(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        if uid!=owner:
            msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法编队哦。'
            await bot.finish(ev, msg)
    CE = CECounter()
    teaminfo = CE._get_teamlist(gid, uid, teamname)
    
    if teaminfo!=0:
        z_ce=0
        bianzu=''
        for i in teaminfo:
            cid = i[0]
            c = chara.fromid(cid)
            card_ce=get_card_ce(gid,uid,cid)
            z_ce=z_ce+card_ce
            bianzu=bianzu+f"{c.name} "
        msg1=f"创建队伍失败！\n已有重复的队伍：{teamname}\n队伍成员为：{bianzu}\队伍战力为：{z_ce}"
        await bot.finish(ev, msg1, at_sender=True)
    
    teamnum = CE._get_teamnum(gid, uid)
    if teamnum>=5:
        await bot.finish(ev, '保存的队伍不能超过5支，请删除其他队伍再来创建吧', at_sender=True)
    
    z_ce=0
    bianzu=''
    for cid in defen:
        c = chara.fromid(cid)
        card_ce=get_card_ce(gid,uid,cid)
        z_ce=z_ce+card_ce
        bianzu=bianzu+f"{c.name} "
        CE._add_team(gid, uid, cid, teamname)
    msg=f"创建队伍成功！\n队伍名称：{teamname}\n队伍成员为：{bianzu}\n队伍战力为：{z_ce}"
    await bot.send(ev, msg, at_sender=True)
  
@sv.on_prefix(['解散队伍','删除队伍'])
async def delete_team(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    duel = DuelCounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 解散队伍+队伍名 中间用空格隔开。', at_sender=True)
    teamname = args[0]  
    teaminfo = CE._get_teamlist(gid, uid, teamname)
    
    if teaminfo!=0:
        CE._delete_team(gid, uid, teamname)
        await bot.send(ev, f'解散队伍{teamname}成功', at_sender=True)
    else:
        await bot.finish(ev, '队伍名称出错，无法查询到此队伍', at_sender=True)
        
@sv.on_fullmatch(['我的队伍','查询队伍'])
async def my_teamlst(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    teamlist = CE._get_teamname(gid, uid)
    if teamlist==0:
        await bot.finish(ev, '您还没有创建队伍，请发送"创建队伍+女友名+队名+队伍名称"创建您的队伍', at_sender=True)
    msg = ''
    for name in teamlist:
        teamname = name[0]
        cidlist = CE._get_teamlist(gid, uid, teamname)
        z_ce=0
        bianzu=''
        for i in cidlist:
            cid = i[0]
            c = chara.fromid(cid)
            card_ce=get_card_ce(gid,uid,cid)
            z_ce=z_ce+card_ce
            bianzu=bianzu+f"{c.name} "
        msg = msg + f"队伍名称：{teamname}\n队伍成员：{bianzu}\n队伍战力：{z_ce}\n"
    await bot.send(ev, msg, at_sender=True)