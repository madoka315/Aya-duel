# -*- coding: utf-8 -*-
"""战斗：巡逻（原副本）——1 键、自动出战、每天 3 次"""
from hoshino.typing import CQEvent
import math
import random
from .. import chara
from .. import sv
from ..core.constants import PATROL_DAILY_LIMIT, PATROL_EXP, PATROL_FAIL_RATE, PATROL_FAVOR, PATROL_GOLD_BASE, PATROL_GOLD_MAX, PATROL_GOLD_PER_LEVEL, PATROL_WIN_K, PATROL_WIN_MAX, PATROL_WIN_MIN
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import add_exp, get_card_ce, get_patrol_stage
from ..core.state import daily_patrol_limiter


PATROL_STAGE_NAME = {
    1: '男爵领', 2: '子爵领', 3: '伯爵领', 4: '侯爵领', 5: '公爵领', 6: '大公领',
    7: '亲王领', 8: '王储林地', 9: '王都近郊', 10: '皇家庭园',
    11: '圣王圣域', 12: '神帝边境',
}


def pick_representative(gid, uid, cidlist):
    """出战女友：优先取绑定的代表，否则取战力最高者"""
    CE = CECounter()
    guaji = CE._get_guaji(gid, uid)
    if guaji and guaji in cidlist:
        return guaji
    return max(cidlist, key=lambda c: get_card_ce(gid, uid, c))


@sv.on_fullmatch(['巡逻', '巡查'])
async def patrol(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    CE = CECounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if not cidlist:
        await bot.finish(ev, '您还没有女友，先发送 贵族舞会 招募一位吧。', at_sender=True)
    if not daily_patrol_limiter.check((gid, uid)):
        await bot.finish(ev, f'今天的巡逻次数已经超过上限（{PATROL_DAILY_LIMIT}次）了哦，明天再来吧。', at_sender=True)

    daily_patrol_limiter.increase((gid, uid))
    level = duel._get_level(gid, uid)
    cid = pick_representative(gid, uid, cidlist)
    c = chara.fromid(cid)
    card_ce = get_card_ce(gid, uid, cid)
    stage_ce = get_patrol_stage(level)
    win_rate = min(PATROL_WIN_MAX, max(PATROL_WIN_MIN, PATROL_WIN_MIN + card_ce / stage_ce * PATROL_WIN_K))

    is_win = random.uniform(1, 100) <= win_rate
    ratio = 1 if is_win else PATROL_FAIL_RATE
    gold = int(min(PATROL_GOLD_MAX, PATROL_GOLD_BASE + level * PATROL_GOLD_PER_LEVEL) * ratio)
    favor = math.ceil(PATROL_FAVOR * ratio)
    exp = int(PATROL_EXP * ratio)

    duel._add_favor(gid, uid, cid, favor)
    level_msg = add_exp(gid, uid, cid, exp)[2]
    if gold > 0:
        score_counter._add_score(gid, uid, gold)

    head = f"您的代表{c.name}（战力{card_ce}）前往{PATROL_STAGE_NAME.get(level, '边境')}巡逻\n"
    if is_win:
        result = f"巡逻顺利，击退了沿路的魔物。\n"
    else:
        result = f"巡逻途中遭遇强敌，只得且战且退。\n"
    msg = (head + result
           + f"获得金币{gold}，{c.name}好感+{favor}，经验+{exp}{level_msg}\n"
           + f"今日剩余巡逻次数：{PATROL_DAILY_LIMIT - daily_patrol_limiter.checks((gid, uid))}\n"
           + c.icon.cqcode)
    await bot.send(ev, msg, at_sender=True)
