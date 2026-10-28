# -*- coding: utf-8 -*-
"""贵族决斗：赛马场（女友参赛，押中第一名固定 4.5 倍）"""
from hoshino.typing import CQEvent
import asyncio
import random
from .. import chara
from .. import sv
from ..core.constants import RACE_BET_MAX, RACE_BET_MIN, RACE_DAILY_LIMIT, RACE_MAX_HORSE, RACE_PAYOUT, RACE_SEGMENTS, RACE_SEG_TIME, RACE_SIGNUP_TIME, RACE_WIN_FAVOR
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import get_card_ce
from ..core.state import daily_race_limiter, horse_race


def _npc_fill(horses):
    """不足 6 匹时用 NPC 补位，战力取场内均值 ±20%"""
    if not horses:
        return
    avg = sum(h['ce'] for h in horses) / len(horses)
    while len(horses) < RACE_MAX_HORSE:
        no = len(horses) + 1
        horses.append({
            'no': no, 'uid': 0, 'cid': 0,
            'ce': int(avg * random.uniform(0.8, 1.2)),
            'name': f'路人骑手{no}', 'speed': 0, 'pos': 0,
        })


async def _race_loop(bot, gid):
    try:
        # 报名期：最多 RACE_SIGNUP_TIME 秒，满员提前开跑
        for _ in range(RACE_SIGNUP_TIME):
            await asyncio.sleep(1)
            room = horse_race.get(gid)
            if room is None or room['phase'] == 'closing':
                break
        room = horse_race.get(gid)
        if room is None:
            return
        if not room['horses']:
            room['task'] = None
            horse_race.remove(gid)
            await bot.send_group_msg(group_id=gid, message='赛马场因无人报名而关闭。')
            return
        room['phase'] = 'running'
        horses = room['horses']
        _npc_fill(horses)
        for h in horses:
            h['steps'] = [h['ce'] * random.uniform(0.7, 1.3) for _ in range(RACE_SEGMENTS)]
            h['pos'] = 0

        await bot.send_group_msg(group_id=gid, message='🏁 鸣枪！赛马开始！')
        for seg in range(RACE_SEGMENTS):
            for h in horses:
                h['pos'] += h['steps'][seg]
            ranking = sorted(horses, key=lambda x: x['pos'], reverse=True)
            text = f'🏇 第{seg + 1}/{RACE_SEGMENTS}段：' + '  '.join(
                f"{r['no']}号{r['name']}" for r in ranking[:3])
            await bot.send_group_msg(group_id=gid, message=text)
            if seg < RACE_SEGMENTS - 1:
                await asyncio.sleep(RACE_SEG_TIME)

        ranking = sorted(horses, key=lambda x: x['pos'], reverse=True)
        winner = ranking[0]
        medal = ['🥇', '🥈', '🥉']
        result = '最终名次：\n'
        for i, r in enumerate(ranking[:3]):
            result += f"{medal[i]}{r['no']}号 {r['name']}（战力{r['ce']}）\n"

        score_counter = ScoreCounter2()
        bet_lines = ''
        for uid in room['bets']:
            no, amount = room['bets'][uid]
            if no == winner['no']:
                back = int(amount * RACE_PAYOUT)
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
            msg += '金币结算：\n' + bet_lines
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
           f"押中第一名返还{RACE_PAYOUT}倍，{RACE_SIGNUP_TIME}秒后开跑。{c.icon.cqcode}")
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
    await bot.send(ev, f'押{no}号{amount}金币成功，若该马夺冠将获得{int(amount * RACE_PAYOUT)}金币。', at_sender=True)


@sv.on_rex(r'^(赛马场|赛马场帮助|查看赛马)$')
async def race_info(bot, ev: CQEvent):
    gid = ev.group_id
    room = horse_race.get(gid)
    msg = ('赛马场：\n'
           '1. 赛马报名(+女友名)  用您的女友参赛，每天3局\n'
           f'2. 押马N号X金币        押中第一名返还{RACE_PAYOUT}倍，每人每局1注\n'
           f'3. 满{RACE_MAX_HORSE}匹或{RACE_SIGNUP_TIME}秒后开跑，不足的由路人骑手补位\n')
    if room is not None and room['phase'] == 'signup':
        roster = '\n'.join(f"{h['no']}号 {h['name']}（战力{h['ce']}）" for h in room['horses'])
        msg += f'\n当前报名中：\n{roster}'
    elif room is not None:
        msg += '\n当前正在开跑，等结算后再报名吧。'
    else:
        msg += '\n当前没有进行中的比赛，发送 赛马报名 开一局吧。'
    await bot.send(ev, msg)
