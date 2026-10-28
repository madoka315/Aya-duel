# -*- coding: utf-8 -*-
"""贵族决斗：赛马场（女友参赛、无 NPC、2 人起跑、押中第一名按场次人数定倍率）"""
from hoshino.typing import CQEvent
import asyncio
import random
from .. import chara
from .. import sv
from ..core.constants import RACE_BET_MAX, RACE_BET_MIN, RACE_CE_WEIGHT, RACE_DAILY_LIMIT, RACE_MAX_HORSE, RACE_MIN_HORSE, RACE_PAYOUT_EV, RACE_SEGMENTS, RACE_SEG_TIME, RACE_SIGNUP_TIME, RACE_WIN_FAVOR
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import get_card_ce
from ..core.state import daily_race_limiter, horse_race


SEG_TITLES = ['起跑', '第一弯道', '长直道', '最后冲刺', '终点线']
STUMBLE = ['踩到水坑踉跄了一下', '被旁边的马挤到了外道', '起步慢了半拍', '被扬起的尘土迷了眼']
SURGE = ['突然发力冲了上来', '在弯道内侧抢到了好位置', '像是听到了看台的呼喊，加速了']


def payout_mult(horse_num):
    """押中第一名的返还倍率：场次人数 × 0.75（恒抽水 25%）"""
    return round(max(RACE_MIN_HORSE, horse_num) * RACE_PAYOUT_EV, 2)


def _mid(result):
    if isinstance(result, dict):
        return result.get('message_id')
    return None


async def _recall(bot, mid):
    """撤回上一条播报（NapCat delete_msg），失败不影响流程"""
    if not mid:
        return
    try:
        await bot.delete_msg(message_id=mid)
    except Exception:
        pass


def _refund_bets(gid, room):
    score_counter = ScoreCounter2()
    for uid in room['bets']:
        amount = room['bets'][uid][1]
        score_counter._add_score(gid, uid, amount)


async def _race_loop(bot, gid):
    last_mid = None
    try:
        for _ in range(RACE_SIGNUP_TIME):
            await asyncio.sleep(1)
            room = horse_race.get(gid)
            if room is None:
                return
            if len(room['horses']) >= RACE_MAX_HORSE:
                break
        room = horse_race.get(gid)
        if room is None:
            return

        horses = room['horses']
        if len(horses) < RACE_MIN_HORSE:
            _refund_bets(gid, room)
            room['task'] = None
            horse_race.remove(gid)
            await bot.send_group_msg(
                group_id=gid,
                message=f'本局赛马只有{len(horses)}人报名，不足{RACE_MIN_HORSE}人，比赛取消，押注已全额退还。')
            return

        room['phase'] = 'running'
        max_ce = max(h['ce'] for h in horses) or 1
        for h in horses:
            h['pos'] = 0.0
            h['boost'] = 0.9 + RACE_CE_WEIGHT * (h['ce'] / max_ce)
        track = RACE_SEGMENTS * 1.1

        prev_leader = None
        for seg in range(RACE_SEGMENTS):
            for h in horses:
                h['pos'] += h['boost'] * random.uniform(0.55, 1.65)

            event = ''
            if random.random() < 0.4:
                target = random.choice(horses)
                if random.random() < 0.5:
                    target['pos'] = max(0.0, target['pos'] - random.uniform(0.4, 0.9))
                    event = f"\n💥 {target['no']}号{target['name']}{random.choice(STUMBLE)}！"
                else:
                    target['pos'] += random.uniform(0.4, 0.9)
                    event = f"\n⚡ {target['no']}号{target['name']}{random.choice(SURGE)}！"

            ranking = sorted(horses, key=lambda x: x['pos'], reverse=True)
            leader = ranking[0]
            lines = []
            for i, h in enumerate(ranking[:3]):
                pct = min(100, int(h['pos'] / track * 100))
                mark = ' ▲' if i == 0 else ''
                lines.append(f"{i + 1}. {h['no']}号 {h['name']} {pct}%{mark}")
            if prev_leader is not None and leader['no'] != prev_leader:
                event += f"\n🔄 {leader['no']}号{leader['name']}抢到了第一！"
            prev_leader = leader['no']

            text = f"🏇 第{seg + 1}/{RACE_SEGMENTS}段 · {SEG_TITLES[seg]}\n" + '\n'.join(lines) + event
            await _recall(bot, last_mid)
            last_mid = _mid(await bot.send_group_msg(group_id=gid, message=text))
            if seg < RACE_SEGMENTS - 1:
                await asyncio.sleep(RACE_SEG_TIME)

        ranking = sorted(horses, key=lambda x: x['pos'], reverse=True)
        winner = ranking[0]
        medal = ['🥇', '🥈', '🥉']
        result = '🏁 比赛结束！最终名次：\n'
        for i, h in enumerate(ranking):
            prefix = medal[i] if i < 3 else f'{i + 1}.'
            result += f"{prefix} {h['no']}号 {h['name']}（战力{h['ce']}）\n"

        mult = payout_mult(len(horses))
        score_counter = ScoreCounter2()
        bet_lines = ''
        for uid in room['bets']:
            no, amount = room['bets'][uid]
            if no == winner['no']:
                back = int(amount * mult)
                score_counter._add_score(gid, uid, back)
                bet_lines += f'[CQ:at,qq={uid}]押中{no}号，获得{back}金币\n'
            else:
                bet_lines += f'[CQ:at,qq={uid}]押{no}号，未中\n'

        award_msg = ''
        if winner['uid'] and winner['cid']:
            duel = DuelCounter()
            if winner['cid'] in duel._get_cards(gid, winner['uid']):
                duel._add_favor(gid, winner['uid'], winner['cid'], RACE_WIN_FAVOR)
                award_msg = f"[CQ:at,qq={winner['uid']}]的{winner['name']}夺冠，好感+{RACE_WIN_FAVOR}\n"

        msg = result + award_msg
        if bet_lines:
            msg += f'金币结算（{len(horses)}匹，赔率{mult}倍）：\n' + bet_lines
        await _recall(bot, last_mid)
        await bot.send_group_msg(group_id=gid, message=msg)
    except asyncio.CancelledError:
        pass
    finally:
        room = horse_race.get(gid)
        if room is not None and room.get('phase') != 'signup':
            room['task'] = None
            horse_race.remove(gid)


@sv.on_prefix(['赛马报名', '报名赛马'])
async def race_signup(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)
    if not cidlist:
        await bot.finish(ev, '您还没有女友，先发送 贵族舞会 招募一位吧。', at_sender=True)
    if not daily_race_limiter.check((gid, uid)):
        await bot.finish(ev, f'今天的赛马次数已经超过上限（{RACE_DAILY_LIMIT}局）了哦，明天再来吧。', at_sender=True)

    room = horse_race.get(gid)
    if room is not None and room['phase'] != 'signup':
        await bot.finish(ev, '本群正在开跑哦，等这一局结算完再报名吧。', at_sender=True)

    args = ev.message.extract_plain_text().strip().split()
    if args:
        cid = chara.name2id(args[0])
        if cid == 1000 or cid not in cidlist:
            await bot.finish(ev, '请选择您身边的女友参赛哦。', at_sender=True)
    else:
        cid = max(cidlist, key=lambda c: get_card_ce(gid, uid, c))

    if room is None:
        room = horse_race.new_room(gid)
        room['task'] = asyncio.create_task(_race_loop(bot, gid))

    c = chara.fromid(cid)
    card_ce = get_card_ce(gid, uid, cid)
    no = horse_race.add_horse(gid, uid, cid, card_ce, c.name)
    if no == 'dup':
        await bot.finish(ev, '您已经有一匹马在赛道上了哦。', at_sender=True)
    daily_race_limiter.increase((gid, uid))

    roster = '\n'.join(f"{h['no']}号 {h['name']}（战力{h['ce']}）" for h in room['horses'])
    if len(room['horses']) >= RACE_MAX_HORSE:
        room['phase'] = 'closing'
    msg = (f"{no}号 {c.name}（战力{card_ce}）报名成功！\n"
           f"当前参赛：\n{roster}\n"
           f"下注：押马1号100金币（{RACE_BET_MIN}~{RACE_BET_MAX}金币，每人1注）\n"
           f"满{RACE_MIN_HORSE}人开跑，{RACE_SIGNUP_TIME}秒后截止；押中第一名按开跑人数返还（{RACE_PAYOUT_EV}×人数）{c.icon.cqcode}")
    await bot.send(ev, msg, at_sender=True)


@sv.on_rex(r'^押马(\d+)号(\d+)(金币|币)$')
async def race_bet(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    room = horse_race.get(gid)
    if room is None or room['phase'] != 'signup':
        await bot.finish(ev, '现在没有正在报名的赛马哦，发送 赛马报名 开一局吧。', at_sender=True)
    match = ev['match']
    no = int(match.group(1))
    amount = int(match.group(2))
    if not any(h['no'] == no for h in room['horses']):
        await bot.finish(ev, f'没有{no}号这匹马哦。', at_sender=True)
    if amount < RACE_BET_MIN or amount > RACE_BET_MAX:
        await bot.finish(ev, f'单注请控制在{RACE_BET_MIN}~{RACE_BET_MAX}金币之间。', at_sender=True)
    if uid in room['bets']:
        await bot.finish(ev, '您这一局已经下过注了。', at_sender=True)
    score_counter = ScoreCounter2()
    if not score_counter._judge_score(gid, uid, amount):
        await bot.finish(ev, '您的金币不足。', at_sender=True)
    score_counter._reduce_score(gid, uid, amount)
    room['bets'][uid] = (no, amount)
    await bot.send(ev, f'押{no}号{amount}金币成功（已扣款）。押中第一名按开跑人数返还，当前{len(room["horses"])}匹。', at_sender=True)


@sv.on_rex(r'^(赛马场|赛马场帮助|查看赛马)$')
async def race_info(bot, ev: CQEvent):
    gid = ev.group_id
    room = horse_race.get(gid)
    msg = ('赛马场：\n'
           '1. 赛马报名(+女友名)  用您的女友参赛，每天3局\n'
           f'2. 押马N号X金币        每人每局1注，{RACE_BET_MIN}~{RACE_BET_MAX}金币\n'
           f'3. 满{RACE_MIN_HORSE}人开跑（最多{RACE_MAX_HORSE}匹），{RACE_SIGNUP_TIME}秒截止\n'
           f'4. 押中第一名返还「开跑人数 × {RACE_PAYOUT_EV}」倍（2人1.5倍、4人3倍、6人4.5倍）\n')
    if room is not None and room['phase'] == 'signup':
        roster = '\n'.join(f"{h['no']}号 {h['name']}（战力{h['ce']}）" for h in room['horses'])
        msg += f'\n当前报名中：\n{roster}'
    elif room is not None:
        msg += '\n当前正在开跑，等结算后再报名吧。'
    else:
        msg += '\n当前没有进行中的比赛，发送 赛马报名 开一局吧。'
    await bot.send(ev, msg)
