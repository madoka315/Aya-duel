# -*- coding: utf-8 -*-
"""战斗：绑定代表女友 / rank / 战力榜"""
from hoshino.typing import CQEvent
from .. import chara
from .. import sv
from ..core.constants import MAX_RANK, RANK_LIST
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import get_noblename, get_power_rank, get_rank_favor_need, get_user_card_dict, uid2card


@sv.on_fullmatch(['战斗系统帮助', '战斗帮助'])
async def combat_help(bot, ev: CQEvent):
    msg = '''
╔                                        ╗  
             战斗系统帮助
1. 绑定女友+角色名
2. 查看绑定
3. 我的女友+角色名   (查看战力等信息)
4. rank等级表        (查看rank提升需求)
5. 升级rank+角色名
6. 战力排行榜
7. 巡逻              (每天3次，绑定的女友出战)
8. 出刀              (周本，战力最高的5人出战)
9. 周本状态 / 伤害排行
10. 赛马报名
╔                                        ╗
战力计算器：战力 = 等级 + 好感 + rank
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
    CE = CECounter()
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    owner = duel._get_card_owner(gid, cid)
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid != owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法绑定哦。'
        await bot.send(ev, msg)
        return
    CE._add_guaji(gid, uid, cid)
    msg = f"女友{c.name}绑定成功，成为您的代表\n决斗胜利后{c.name}可以获得经验值，巡逻也会优先由她出战\n{nvmes}"
    await bot.send(ev, msg, at_sender=True)


@sv.on_fullmatch(['查看绑定', '查看战斗女友'])
async def get_bangdin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    CE = CECounter()
    duel = DuelCounter()
    cid = CE._get_guaji(gid, uid)
    if cid == 0:
        msg = '您尚未绑定任何角色，发送 绑定女友+角色名 设一位代表吧。'
        await bot.finish(ev, msg)
    owner = duel._get_card_owner(gid, cid)
    c = chara.fromid(cid)
    if uid != owner:
        msg = f'您绑定了：{c.name}，但她已不在您身边，请重新绑定您的女友。'
        await bot.finish(ev, msg)
    nvmes = c.icon.cqcode
    msg = f"您当前绑定的代表女友是：{c.name}，每位贵族只能绑定一位女友参战哦~\n{nvmes}"
    await bot.send(ev, msg, at_sender=True)


@sv.on_fullmatch(['女友rank等级表', 'rank表', 'rank等级表'])
async def rank_list(bot, ev: CQEvent):
    msg = '女友rank等级需求表：\n'
    rank = 1
    while rank <= MAX_RANK:
        rankInfo = RANK_LIST[rank]
        noblename = get_noblename(min(rank, 12))
        favor_need = get_rank_favor_need(rank)
        msg += f'"R{rank}": 需求贵族≥{noblename}、好感≥{favor_need}，消耗{rankInfo}金币，战力+{rank * 200}\n'
        rank += 1
    await bot.send(ev, msg)


@sv.on_prefix(['升级rank', 'rank升级', '提升rank'])
async def up_rank(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    if len(args) != 1:
        await bot.finish(ev, '请输入 rank升级+女友名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)
    rank = CE._get_rank(gid, uid, cid)
    if rank >= MAX_RANK:
        await bot.finish(ev, '该女友rank已升至满级，无法继续升级啦。', at_sender=True)
    new_rank = rank + 1
    level = duel._get_level(gid, uid)
    if new_rank > level:
        await bot.finish(ev, '您的贵族等级不足，请发送[升级贵族]提升您的等级吧。', at_sender=True)
    favor = duel._get_favor(gid, uid, cid) or 0
    need_favor = get_rank_favor_need(new_rank)
    if favor < need_favor:
        await bot.finish(ev, f'升级rank需要好感≥{need_favor}哦，{name}当前好感只有{favor}。', at_sender=True)
    rank_score = RANK_LIST[int(new_rank)]
    score_counter = ScoreCounter2()
    myscore = score_counter._get_score(gid, uid)
    if myscore < rank_score:
        await bot.finish(ev, f'升级rank所需金币不足！\n由{rank}级升至{new_rank}级需要：{rank_score}个，您当前剩余：{myscore}个', at_sender=True)

    score_counter._reduce_score(gid, uid, rank_score)
    CE._up_rank(gid, uid, cid)
    c = chara.fromid(cid)
    msg = f'您花费了{rank_score}金币为{c.name}提升了rank，当前rank等级为：{new_rank}级，战力提升{200}点！'
    await bot.send(ev, msg, at_sender=True)


@sv.on_fullmatch(['战力榜', '女友战力榜', '战力排行榜'])
async def girl_power_rank(bot, ev: CQEvent):
    ranking_list = get_power_rank(ev.group_id)
    msg = '本群女友战力排行榜(仅展示rank>0的)：\n'
    if len(ranking_list) > 0:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        rank = 1
        for girl in ranking_list:
            if rank <= 10:
                rank1, power, uid, cid = girl
                user_card = uid2card(uid, user_card_dict)
                c = chara.fromid(cid)
                msg += f'第{rank}名: {user_card}的 {c.name}(rank{rank1})，战斗力{power}点\n'
            rank = rank + 1
    else:
        msg += '暂无女友上榜'
    await bot.send(ev, msg)
