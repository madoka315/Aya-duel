# -*- coding: utf-8 -*-
"""战斗：周本（原会战）——全群共享血量，每人每天 1 次出刀，自动取最强 5 人"""
from datetime import datetime
from hoshino.typing import CQEvent
import json
import os
import pytz
import random
from .. import chara
from .. import sv
from ..core.constants import FILE_PATH, WEEKLY_BASE_HP, WEEKLY_DAILY_LIMIT, WEEKLY_DMG_MAX, WEEKLY_DMG_MIN, WEEKLY_EXP, WEEKLY_FAVOR, WEEKLY_GOLD_DIV, WEEKLY_GOLD_MAX, WEEKLY_HP_PER_NOBLE, WEEKLY_KILL_FAVOR, WEEKLY_KILL_GOLD, WEEKLY_TEAM_SIZE
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import add_exp, get_boss_icon, get_card_ce
from ..core.state import daily_weekly_limiter


def get_period():
    """按 ISO 周取周期编号，如 2026 年第 44 周 = 202644"""
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    iso = now.isocalendar()
    return int(iso[0]) * 100 + int(iso[1])


def load_bosses():
    """读取 bossinfo.json，按 bossid 去重，返回 [{bossid, name, fenshu}]"""
    with open(os.path.join(FILE_PATH, 'bossinfo.json'), 'r', encoding='UTF-8') as fa:
        bosslist = json.load(fa, strict=False)
    bosses = {}
    for x in bosslist:
        for j in bosslist[x]['bosslist']:
            boss = bosslist[x]['bosslist'][j]
            bosses[int(boss['bossid'])] = {
                'bossid': int(boss['bossid']),
                'name': boss['name'],
                'fenshu': boss.get('fenshu', 1),
            }
    return [bosses[k] for k in sorted(bosses)]


def load_boss(period):
    bosses = load_bosses()
    if not bosses:
        return {'bossid': 1, 'name': '神秘之影', 'fenshu': 1}
    return bosses[period % len(bosses)]


def weekly_hp(gid):
    duel = DuelCounter()
    noble_num = len(duel._get_uid_list(gid) or [])
    return max(WEEKLY_BASE_HP, noble_num * WEEKLY_HP_PER_NOBLE)


def get_state(gid):
    """返回 (period, boss, hp, max_hp)，首次进入自动开新周目"""
    CE = CECounter()
    period = get_period()
    max_hp = weekly_hp(gid)
    bossid, hp = CE._get_weeklystate(gid, period)
    if bossid == 0:
        boss = load_boss(period)
        hp = max_hp
        CE._set_weeklystate(gid, period, boss['bossid'], hp)
        return period, boss, hp, max_hp
    bosses = {b['bossid']: b for b in load_bosses()}
    boss = bosses.get(bossid, {'bossid': bossid, 'name': '神秘之影', 'fenshu': 1})
    return period, boss, hp, max_hp


def top_girls(gid, uid, num):
    """取战力最高的 num 名女友"""
    duel = DuelCounter()
    cidlist = duel._get_cards(gid, uid)
    ranked = sorted(cidlist, key=lambda c: get_card_ce(gid, uid, c), reverse=True)
    return ranked[:num]


@sv.on_fullmatch(['出刀', '周本出刀'])
async def weekly_fight(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。', at_sender=True)
    if not duel._get_cards(gid, uid):
        await bot.finish(ev, '您还没有女友，先发送 贵族舞会 招募一位吧。', at_sender=True)
    if not daily_weekly_limiter.check((gid, uid)):
        await bot.finish(ev, f'今天已经出过刀了哦，每人每天 {WEEKLY_DAILY_LIMIT} 次，明天再来吧。', at_sender=True)

    period, boss, hp, max_hp = get_state(gid)
    if hp <= 0:
        await bot.finish(ev, f'本周的{boss["name"]}已经被击败了，下周一会有新的对手。', at_sender=True)

    daily_weekly_limiter.increase((gid, uid))
    team = top_girls(gid, uid, WEEKLY_TEAM_SIZE)
    team_ce = sum(get_card_ce(gid, uid, cid) for cid in team)
    dmg = int(team_ce * random.uniform(WEEKLY_DMG_MIN, WEEKLY_DMG_MAX) * boss.get('fenshu', 1))
    applied = min(dmg, hp)
    new_hp = hp - applied
    CE._add_weeklyfight(gid, uid, period, applied)
    CE._up_weekly_hp(gid, period, new_hp)

    gold = min(WEEKLY_GOLD_MAX, applied // WEEKLY_GOLD_DIV)
    score_counter._add_score(gid, uid, gold)
    names = []
    for cid in team:
        c = chara.fromid(cid)
        names.append(c.name)
        duel._add_favor(gid, uid, cid, WEEKLY_FAVOR)
        add_exp(gid, uid, cid, WEEKLY_EXP)

    msg = (f"您率领{'、'.join(names)}（合计战力{team_ce}）出刀\n"
           f"对{boss['name']}造成了{applied}点伤害，获得金币{gold}\n"
           f"出战女友好感+{WEEKLY_FAVOR}，经验+{WEEKLY_EXP}\n"
           f"周本剩余血量：{max(0, new_hp)}/{max_hp}")

    if new_hp <= 0:
        msg += f"\n\n🎉 本周的{boss['name']}被击败了！"
        score_counter = ScoreCounter2()
        for pid in CE._get_weekly_participants(gid, period):
            score_counter._add_score(gid, pid, WEEKLY_KILL_GOLD)
            pcards = DuelCounter()._get_cards(gid, pid)
            if pcards:
                lucky = random.choice(pcards)
                DuelCounter()._add_favor(gid, pid, lucky, WEEKLY_KILL_FAVOR)
        msg += f"\n全体参与成员每人获得{WEEKLY_KILL_GOLD}金币与一名女友+{WEEKLY_KILL_FAVOR}好感。"
    await bot.send(ev, msg)


@sv.on_rex(r'^(周本状态|boss战状态|周本)$')
async def weekly_status(bot, ev: CQEvent):
    gid = ev.group_id
    CE = CECounter()
    period, boss, hp, max_hp = get_state(gid)
    total_dmg, people = CE._get_weekly_total(gid, period)
    icon = get_boss_icon(boss['name'])
    if hp <= 0:
        msg = (f"本周对手：{boss['name']}\n已在本周被击败（参与 {people} 人，累计伤害 {total_dmg}）\n"
               f"下周一 0 点刷新新的对手。{icon}")
    else:
        msg = (f"本周对手：{boss['name']}\n剩余血量：{hp}/{max_hp}\n已参与：{people} 人，累计伤害 {total_dmg}\n"
               f"每人每天可出刀 1 次（发送 出刀）{icon}")
    await bot.send(ev, msg)


@sv.on_fullmatch(['伤害排行', '周本排行'])
async def weekly_rank(bot, ev: CQEvent):
    gid = ev.group_id
    CE = CECounter()
    period = get_period()
    ranking = CE._get_weekly_rank(gid, period, 10)
    if not ranking:
        await bot.finish(ev, '本周还没有人出刀哦。')
    msg = '本周伤害排行：\n'
    for i, (uid, dmg) in enumerate(ranking):
        msg += f'{i + 1}. [CQ:at,qq={uid}] {dmg}点\n'
    await bot.send(ev, msg)
