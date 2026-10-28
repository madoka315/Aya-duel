# -*- coding: utf-8 -*-
"""贵族决斗：管理指令"""
from hoshino import priv
from hoshino.typing import CQEvent
from .. import sv
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.state import daily_Remake_limiter


        
#注意会清空此人的角色以及贵族等级，只用做必要时删库用。 
@sv.on_prefix('重置角色')
async def reset_chara(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置角色功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置角色+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        cidlist = duel._get_cards(gid, id)
        for cid in cidlist:
            duel._delete_card(gid, id, cid)
        queen = duel._search_queen(gid,id)
        duel._delete_queen_owner(gid,queen)
        duel._set_level(gid, id, 0)    
        await bot.finish(ev, f'已清空用户{id}的女友和贵族等级。', at_sender=True)

@sv.on_prefix('确认重开')
async def reset_CK(bot, ev: CQEvent):
        gid = ev.group_id
        uid = ev.user_id
        guid = (gid,uid)
        if not daily_Remake_limiter.check(guid):
            await bot.send(ev, '一天最多重开一次！', at_sender=True)
            return
        duel = DuelCounter()
        score_counter = ScoreCounter2()
        prestige = score_counter._get_prestige(gid,uid)
        if prestige == None:
            await bot.finish(ev, '您尚未开启声望系统，人生还很长，无法重开！')
        if prestige < 0:
            await bot.finish(ev, '您现在身败名裂（声望为负），无法重开！', at_sender=True)
        if duel._get_level(gid, uid) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        cidlist = duel._get_cards(gid, uid)
        for cid in cidlist:
            duel._delete_card(gid, uid, cid)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, uid)
        score_counter._reduce_score(gid, uid,current_score)
        queen = duel._search_queen(gid,uid)
        duel._delete_queen_owner(gid,queen)
        duel._set_level(gid, uid, 0) 
        score_counter._set_prestige(gid,uid,0)  
        daily_Remake_limiter.increase(guid)  
        duel._WLC_Remake(gid,uid)
        i = 0
        while(i<=10):
            while(duel._get_gift_num(gid,uid,i)!=0):
                duel._reduce_gift(gid,uid,i)
            i += 1 
        await bot.finish(ev, f'已清空您的女友和贵族等级，金币等。', at_sender=True)