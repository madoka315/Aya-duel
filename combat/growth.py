# -*- coding: utf-8 -*-
"""战斗：绑定女友/rank/战力榜"""
from hoshino.typing import CQEvent
from .. import chara
from .. import sv
from ..core.constants import MAX_RANK, RANK_LIST
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import get_equip_info_id, get_noblename, get_power_rank, get_user_card_dict, uid2card


@sv.on_fullmatch(['战斗系统帮助','战斗帮助'])
async def combat_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             战斗系统帮助
1. 绑定女友 +角色名 (绑定xx女友作为决斗伴侣，会获取经验值升级)
2. 我的女友 +角色名 (查看女友战力等信息)
3. 查看绑定/查看战斗女友
4. rank等级表/rank表 (查看rank等级提升需求)
5. 升级rank/rank升级/提升rank +角色名 (升级女友的rank)
6. 创建队伍+女友名(最多5名，用空格隔开)+队名+队伍名称 (保存队伍)
7. 解散队伍+队伍名
8. 我的队伍(查询我的队伍情况)
9. 挂机修炼+女友名
10. 结束修炼
11. 我的经验池
12. 分配经验+女友名+经验值
13. 战力排行榜
注:
战力计算器：
    基础战力 = 100 + 等级*50 + 好感度*0.4
    女友战力 = 基础战力*(1+rank/10)
    最大rank等级为10级，达到r10可以增幅2倍战力
╚                                        ╝
 '''
    await bot.send(ev, msg)

@sv.on_prefix(['绑定女友'])
async def card_bangdin(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    if not args:
        await bot.send(ev, '请输入绑定女友+pcr角色名。', at_sender=True)
        return
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
    if uid==owner:
        CE._add_guaji(gid,uid,cid)
        msg = f"女友{c.name}绑定成功\n之后决斗胜利后{c.name}可以获得经验值哦\n{nvmes}"
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['查看绑定','查看战斗女友'])
async def get_bangdin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    duel = DuelCounter()
    cid = CE._get_guaji(gid,uid)
    if cid==0:
        msg = '您尚未绑定任何角色参与战斗。'
        await bot.finish(ev, msg)
    owner = duel._get_card_owner(gid, cid)
    c = chara.fromid(cid)
    if uid!=owner:
        msg = f'您绑定了：{c.name}，但她已不在您身边，请重新绑定您的女友。'
        await bot.finish(ev, msg)
    nvmes = c.icon.cqcode
    msg = f"您当前绑定的女友是：{c.name}，每位贵族只能绑定一位女友参与战斗哦~\n{nvmes}"
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['女友rank等级表','rank表','rank等级表'])
async def rank_list(bot, ev: CQEvent):
    msg = '女友rank等级需求表：\n'
    rank = 1
    while (rank <= 10):
        rankInfo = RANK_LIST[rank]
        if rank <= 7:
            noblename = get_noblename(rank)
        else:
        	noblename = get_noblename(7)
        ce_up = 1+rank/10
        if rank<=3:
            needmodel = 'N'
        elif rank>3 and rank<6:
            needmodel = 'R'
        else:
            needmodel = 'SR'
        msg += f'"R{rank}": 需求贵族等级≥{noblename}，消耗{rankInfo}金币，身上穿戴的4件{needmodel}品质及以上装备，女友战力提升为{ce_up}倍\n'
        rank = rank + 1
    await bot.send(ev, msg)

@sv.on_prefix(['升级rank','rank升级','提升rank'])
async def up_rank(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    if len(args)!=1:
        await bot.finish(ev, '请输入 rank升级+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    rank = CE._get_rank(gid,uid,cid)
    if rank==MAX_RANK:
        await bot.finish(ev, '该女友rank已升至满级，无法继续升级啦。', at_sender=True)
    new_rank = rank + 1
    if new_rank > 7:
    	new_rank = 7
    level = duel._get_level(gid,uid)
    if new_rank>level:
        await bot.finish(ev, '您的贵族等级不足，请发送[升级贵族]提升您的等级吧。', at_sender=True)
    rank_score = RANK_LIST[int(new_rank)]
    score_counter = ScoreCounter2()
    myscore = score_counter._get_score(gid,uid)
    if myscore < rank_score:
        await bot.finish(ev, f'升级rank所需金币不足！\n由{rank}级升至{new_rank}级需要：{rank_score}个，您当前剩余：{myscore}个',at_sender=True)
    
    #获取角色穿戴装备列表
    dreeslist = CE._get_dress_list(gid, uid, cid)
    if dreeslist:
        dreesnum = len(dreeslist)
    else:
        dreesnum = 0
    
    if dreesnum<4:
        await bot.finish(ev, f'升级rank所需需要穿戴4件装备哦！您当前穿戴的装备数量为：{dreesnum}件',at_sender=True)
    islevelok = 1
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
    for eid in dreeslist:
        equipinfo = get_equip_info_id(eid)
        if equipinfo:
            if equipinfo['level']<needlevel:
                islevelok = 0
                break
    if islevelok==0:
        await bot.finish(ev, f'升级rank所需需要穿戴4件{needmodel}品质的装备哦！您未达到要求哦',at_sender=True)
    
    for eid in dreeslist:
        equipinfo = get_equip_info_id(eid)
        if equipinfo:
            CE._dress_equip(gid, uid, cid, equipinfo['type_id'], 0)
            CE._add_equip(gid, uid, equipinfo['eid'], 1)
    equip_list = CE._get_equip_list(gid, uid)
    lowest = [99, 99, 99, 99]
    removelist = [[0,''],[0,''],[0,''],[0,'']]
    for i in equip_list:
        equipinfo = get_equip_info_id(i[0])
        if equipinfo['type_id'] == 1 and equipinfo['level'] >= needlevel and equipinfo['level'] < lowest[0]:
            removelist[0][0] = equipinfo['eid']
            removelist[0][1] = equipinfo['model']
            removelist[0][1] += equipinfo['name']
            lowest[0] = equipinfo['level']
            continue
        if equipinfo['type_id'] == 2 and equipinfo['level'] >= needlevel and equipinfo['level'] < lowest[1]:
            removelist[1][0] = equipinfo['eid']
            removelist[1][1] = equipinfo['model']
            removelist[1][1] += equipinfo['name']
            lowest[1] = equipinfo['level']
            continue
        if equipinfo['type_id'] == 3 and equipinfo['level'] >= needlevel and equipinfo['level'] < lowest[2]:
            removelist[2][0] = equipinfo['eid']
            removelist[2][1] = equipinfo['model']
            removelist[2][1] += equipinfo['name']
            lowest[2] = equipinfo['level']
            continue
        if equipinfo['type_id'] == 4 and equipinfo['level'] >= needlevel and equipinfo['level'] < lowest[3]:
            removelist[3][0] = equipinfo['eid']
            removelist[3][1] = equipinfo['model']
            removelist[3][1] += equipinfo['name']
            lowest[3] = equipinfo['level']
            continue
    part_msg = '\n自动为您消耗了女友身上或装备仓库中，满足升rank条件的较差装备：\n'
    for i in removelist:
        part_msg += f'{i[1]} '
        CE._add_equip(gid, uid, i[0], -1)
    
    score_counter._reduce_score(gid, uid, rank_score)
    CE._up_rank(gid,uid,cid)
    c = chara.fromid(cid)
    msg = f'{part_msg}\n您花费了{rank_score}金币为{c.name}提升了rank，当前rank等级为：{new_rank}级，女友战斗力大大提升！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['战力榜','女友战力榜','战力排行榜'])
async def girl_power_rank(bot, ev: CQEvent):
    ranking_list = get_power_rank(ev.group_id)
    msg = '本群女友战力排行榜(仅展示rank>0的)：\n'
    if len(ranking_list)>0:
        rank = 1
        for girl in ranking_list:
            if rank<=10:
                user_card_dict = await get_user_card_dict(bot, ev.group_id)
                rank1,power,uid,cid = girl
                user_card = uid2card(uid, user_card_dict)
                c = chara.fromid(cid)
                msg += f'第{rank}名: {user_card}的 {c.name}(rank{rank1})，战斗力{power}点\n'
            rank = rank+1
    else:
        msg += '暂无女友上榜'
    await bot.send(ev, msg)