import asyncio
import base64
import os
import random
import sqlite3
import math
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from hoshino import Service, priv
from . import chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json
from . import *

@sv.on_prefix(['女友信息','我的女友'])
async def my_fashion_info(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    if not args:
        await bot.send(ev, '请输入我的女友+pcr角色名。', at_sender=True)
        return
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    c = chara.fromid(cid)
    nvmes = c.icon.cqcode
    lh_msg = ''
    up_icon=''
    jishu=0
    up_name=''
    owner = duel._get_card_owner(gid, cid)
    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    if uid!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您无法查询哦。'
        await bot.send(ev, msg)
        return
    if uid==owner:
        queen_msg=''
        if duel._get_queen_owner(gid,cid) !=0:
            queen_msg=f'现在是您的妻子\n'
        if duel._get_favor(gid,uid,cid)== None:
            duel._set_favor(gid,uid,cid,0)
        favor= duel._get_favor(gid,uid,cid)
        relationship,text = get_relationship(favor)
        if up_icon:
            nvmes=up_icon
        up_msg=''
        
        CE = CECounter()
        equip_list = ''
        equip_msg = ''
        dreeslist = CE._get_dress_list(gid, uid, cid)
        for eid in dreeslist:
            equipinfo = get_equip_info_id(eid)
            if equipinfo:
                equip_list = equip_list + f"\n{equipinfo['type']}:{equipinfo['name']}({equipinfo['model']})"
        if equip_list:
            equip_msg = f"\n目前穿戴的装备为:{equip_list}"
        else:
            equip_msg = '目前没有穿戴任何装备'
        rank = CE._get_rank(gid,uid,cid)
        level = CE._get_card_level(gid, uid, cid)
        card_exp = CE._get_card_exp(gid,uid,cid)
        card_ce = get_card_ce(gid,uid,cid)
        msg = f'\n{c.name}{queen_msg}\nRANK：{rank}|等级：{level}|经验：{card_exp}|战力：{card_ce}\n{equip_msg}\n对你的好感是{favor}\n你们的关系是{relationship}\n“{text}”{up_msg}{nvmes}{lh_msg}'
    await bot.send(ev, msg, at_sender=True)  