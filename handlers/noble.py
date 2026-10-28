# -*- coding: utf-8 -*-
"""贵族决斗：贵族创建/签到/查询/升级/加冕/婚礼/分手"""
from PIL import Image
from hoshino.typing import CQEvent
from io import BytesIO
import base64
import copy
import os
import random
from .. import chara
from .. import sv
from ..core.constants import Addgirlfail, Addgirlsuccess, BREAK_UP_SWITCH, FORWARD_QQ, FULLCARD_PATH, GIFT_DICT, LEVEL_MAX, Login100, Login200, Login300, Login600, NEED_favor, RECRUIT_DAILY_LIMIT, RECRUIT_PITY, SHANGXIAN_NUM, TRUE_LOVE_FAVOR, WAREHOUSE_NUM
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.dlc import dlc_switch, dlcdict, dlcdict2
from ..core.rules import concat_pic, count_true_love, get_favor_need, get_girlnum_total, get_newgirl_list, get_noblename, get_noblescore, get_prestige_need, get_recruit_cost, get_recruit_fail_rate, get_user_card
from ..core.state import add_recruit_fail_count, clear_recruit_fail_count, daily_recruit_limiter, daily_sign_limiter, duel_judger, get_recruit_fail_count



@sv.on_fullmatch(['本群贵族状态','查询本群贵族','本群贵族'])
async def group_noble_status(bot, ev: CQEvent):
    gid = ev.group_id
    duel = DuelCounter()
    newgirllist = get_newgirl_list(gid)
    newgirlnum = len(newgirllist)
    l1_num = duel._get_level_num(gid,1)
    l2_num = duel._get_level_num(gid,2)
    l3_num = duel._get_level_num(gid,3)
    l4_num = duel._get_level_num(gid,4)
    l5_num = duel._get_level_num(gid,5)
    l6_num = duel._get_level_num(gid,6)
    l7_num = duel._get_level_num(gid,7)
    dlctext=''
    for dlc in dict(dlcdict, **dlcdict2).keys():
        if gid in dlc_switch[dlc]:
            dlctext += f'{dlc},'
    msg=f'''
╔                          ╗
         本群贵族
      
  皇帝：{l7_num}名
  国王：{l6_num}名
  公爵：{l5_num}名
  侯爵：{l4_num}名
  伯爵：{l3_num}名
  子爵：{l2_num}名
  男爵：{l1_num}名
  已开启DLC:
  {dlctext}
  还有{newgirlnum}名单身女友 
╚                          ╝
'''
    await bot.send(ev, msg)



@sv.on_fullmatch('贵族签到')
async def noblelogin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    guid = gid, uid
    if not daily_sign_limiter.check(guid):
        await bot.send(ev, '今天已经签到过了哦，明天再来吧。', at_sender=True)
        return
    duel = DuelCounter()
    
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
   #根据概率随机获得收益。 
    score_counter = ScoreCounter2()
    daily_sign_limiter.increase(guid)    
    loginnum_ = ['1','2', '3', '4']  
    r_ = [0.3, 0.4, 0.2, 0.1]  
    sum_ = 0
    ran = random.random()
    for num, r in zip(loginnum_, r_):
        sum_ += r
        if ran < sum_ :break
    Bonus = {'1':[100,Login100],
             '2':[200,Login200],
             '3':[300,Login300],    
             '4':[600,Login600]
            }             
    score1 = Bonus[num][0]
    text1 = random.choice(Bonus[num][1])
    
   #根据爵位的每日固定收入（皇帝以上封顶，防止新等级放大通胀）
    level = duel._get_level(gid, uid)
    score2 = 50*min(level,10)
    scoresum = score1+score2
    score_counter._add_score(gid, uid, scoresum)
    noblename = get_noblename(level)
    score = score_counter._get_score(gid, uid)
    msg = f'\n{text1}\n签到成功！您领取了：\n\n{score1}金币(随机)和\n{score2}金币({noblename}爵位)'
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)
    
    if cidnum > 0:
        cid = random.choice(cidlist)
        c = chara.fromid(cid)
        mes = c.icon.cqcode
        path = os.path.join(FULLCARD_PATH,f'{cid}31.png')
        if  os.path.exists(path):
            img = Image.open(path)
            bio = BytesIO()
            img.save(bio, format='PNG')
            base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
            mes = f"[CQ:image,file={base64_str}]"
        msg += f'\n\n今天向您请安的是\n{c.name}{mes}'
    if random.randint(0,1):
        select_gift = random.choice(list(GIFT_DICT.keys()))
        gfid = GIFT_DICT[select_gift]
        duel._add_gift(gid,uid,gfid)
        msg += f'\n随机获得了礼物[{select_gift}]'
    else:
        CE = CECounter()
        exp_bottle = random.choice([500,1000,1000,1800,1800,1800,3000,6666])
        CE._add_exp_chizi(gid, uid, exp_bottle)
        msg += f'\n随机获得了经验药剂({exp_bottle}型)，已加入您的经验池'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('创建贵族')
async def add_noble(bot, ev: CQEvent):
    try:
        gid = ev.group_id
        uid = ev.user_id
        duel = DuelCounter()
        if duel._get_level(gid, uid) != 0:
            msg = '您已经在本群创建过贵族了，请发送 查询贵族 查询。'
            await bot.send(ev, msg, at_sender=True)
            return
        
       #判定本群女友是否已空，如果空则分配一个复制人可可萝。
        newgirllist = get_newgirl_list(gid)
        if len(newgirllist) == 0:
            cid = 9999
            c = chara.fromid(1059)
            girlmsg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}'
        else:
            cid = random.choice(newgirllist)
            c = chara.fromid(cid)
            girlmsg = f'为您分配的初始女友为：{c.name}{c.icon.cqcode}'
        duel._add_card(gid, uid, cid)
        duel._set_level(gid, uid, 1)
        msg = f'\n创建贵族成功！\n您的初始爵位是男爵\n可以拥有3名女友。\n{girlmsg}'
        await bot.send(ev, msg, at_sender=True)        
            

    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_prefix(['查询贵族', '贵族查询', '我的贵族'])
async def inquire_noble(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    try:
        id = int(ev.message[0].data['qq'])
    except Exception:
        id = ev.user_id
    name = await get_user_card(bot, id)
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, id) == 0 and id ==uid:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    elif duel._get_level(gid, id) == 0 and id != uid:
        msg = '对方还未在本群创建过贵族。'
        await bot.send(ev, msg, at_sender=True)
        return
    level = duel._get_level(gid, id)
    noblename = get_noblename(level)
    girlnum = get_girlnum_total(gid, id)
    score = score_counter._get_score(gid, id)
    charalist = []

    cidlist = duel._get_cards(gid, id)
    cidnum = len(cidlist)
    Winnum = duel._get_WLCWIN(gid,id)
    Losenum = duel._get_WLCLOSE(gid,id)
    ADMITnum = duel._get_ADMIT(gid,id)
    if Losenum == 0:
        winprobability = 100
    else:
        winprobability = round((Winnum / (Winnum+Losenum))*100 ,2)
    if Winnum == 0:
        winprobability = 0
    if cidnum == 0:
        msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  您的胜场{Winnum}负场{Losenum}
  认输了{ADMITnum}次
  胜率为{winprobability}%
  您共可拥有{girlnum}名女友
  您目前没有女友。
  发送[贵族舞会]
  可以招募女友哦。
  
╚                          ╝
'''
        data = {
            "type":"node",
            "data":{
                "name":f'{name}的贵族信息',
                "uin":f'{FORWARD_QQ}',
                "content":msg
            }
        }
        await bot.send_group_forward_msg(group_id=ev.group_id, messages=data)

    else:
        shuzi_flag=0
        nv_names=''
        for cid in cidlist:
           #替换复制人可可萝
            if cid == 9999:
                cid = 1059
            charalist.append(chara.Chara(cid, 0, 0))
            c = chara.fromid(cid)
            shuzi_flag=shuzi_flag+1
            nv_names=nv_names+c.name+'|'
            if shuzi_flag==6:
                nv_names=nv_names+'\n'
                shuzi_flag=0
            
       #制图部分，六个一行
        num = copy.deepcopy(cidnum)
        position = 6
        if num <= 6:
            res = chara.gen_team_pic(charalist, star_slot_verbose=False)
        else:
            num -= 6
            res = chara.gen_team_pic(charalist[0:position], star_slot_verbose=False)
            while(num > 0):
                if num>=6:
                    res1 = chara.gen_team_pic(charalist[position:position+6], star_slot_verbose=False)
                else: 
                    res1 = chara.gen_team_pic(charalist[position:], star_slot_verbose=False)
                res = concat_pic([res, res1])
                position +=6
                num -= 6
            

        bio = BytesIO()
        res.save(bio, format='PNG')
        base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
        mes = f"[CQ:image,file={base64_str}]"
        
       #判断是否开启声望
        prestige = score_counter._get_prestige(gid,id)
        if prestige == None:
            partmsg = '未开启声望系统'
        else:
            partmsg = f'您的声望为{prestige}点'
        
        
        
        
        
        msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的胜场{Winnum}负场{Losenum}
  认输了{ADMITnum}次
  胜率为{winprobability}%
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}   
╚                          ╝
'''
       #判断有无皇后
        queen = duel._search_queen(gid,id)
        if queen != 0:
            c = chara.fromid(queen)
            
            msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的胜场{Winnum}负场{Losenum}
  认输了{ADMITnum}次
  胜率为{winprobability}%
  您的皇后是{c.name}
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}  
    
╚                          ╝
'''


        data = {
            "type":"node",
            "data":{
                "name":f'{name}的贵族信息',
                "uin":f'{FORWARD_QQ}',
                "content":msg
            }
        }
        await bot.send_group_forward_msg(group_id=ev.group_id, messages=data)


@sv.on_fullmatch(['招募女友', '贵族舞会'])
async def girl_recruit(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(gid):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return        

    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)

        await bot.send(ev, msg, at_sender=True)
        return
    else:
       # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_total(gid, uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        if cidnum >= girlnum:
            msg = '您的女友已经满了哦，快点发送[升级贵族]进行升级吧。'
            await bot.send(ev, msg, at_sender=True)
            return
        guid = gid, uid
        if not daily_recruit_limiter.check(guid):
            msg = f'今天已经参加过{RECRUIT_DAILY_LIMIT}次贵族舞会了哦，明天再来吧。'
            await bot.send(ev, msg, at_sender=True)
            return
        cost = get_recruit_cost(level, cidnum)
        score = score_counter._get_score(gid, uid)
        if score < cost:
            msg = f'您的金币不足{cost}哦。'
            await bot.send(ev, msg, at_sender=True)
            return
        newgirllist = get_newgirl_list(gid)
       # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                daily_recruit_limiter.increase(guid)
                score_counter._reduce_score(gid, uid, cost)
                cid = 9999
                c = chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        daily_recruit_limiter.increase(guid)
        score_counter._reduce_score(gid, uid, cost)

       # 招募女友失败：连续失败RECRUIT_PITY-1次后下一次必成
        if get_recruit_fail_count(gid, uid) < RECRUIT_PITY - 1 and random.random() < get_recruit_fail_rate(level):
            add_recruit_fail_count(gid, uid)
            losetext = random.choice(Addgirlfail)
            msg = f'\n{losetext}\n您花费了{cost}金币，但是没有约到新的女友。'
            await bot.send(ev, msg, at_sender=True)
            return

       # 招募女友成功
        clear_recruit_fail_count(gid, uid)
        cid = random.choice(newgirllist)
        duel._add_card(gid, uid, cid)
        c = chara.fromid(cid)
        wintext = random.choice(Addgirlsuccess)
        mes = c.icon.cqcode
        path = os.path.join(FULLCARD_PATH,f'{cid}31.png')
        if  os.path.exists(path):
            img = Image.open(path)
            bio = BytesIO()
            img.save(bio, format='PNG')
            base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
            mes = f"[CQ:image,file={base64_str}]"

        
        msg = f'\n{wintext}\n招募女友成功！\n您花费了{cost}金币\n新招募的女友为：{c.name}{mes}'

        await bot.send(ev, msg, at_sender=True)


@sv.on_fullmatch(['升级爵位', '升级贵族','贵族升级'])
async def noble_upgrade(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    score = score_counter._get_score(gid, uid)
    level = duel._get_level(gid, uid)
    noblename = get_noblename(level)
    girlnum = get_girlnum_total(gid, uid)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)

    if duel_judger.get_on_off_status(gid):
        msg = '现在正在决斗中哦，请决斗后再升级爵位吧。'
        await bot.send(ev, msg, at_sender=True)
        return  
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level == 9:
        msg = f'您已经是国王了， 需要通过声望加冕称帝哦。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level >= LEVEL_MAX:
        msg = f'您已经是本群的{get_noblename(LEVEL_MAX)}， 已经无法提升等级了。'
        await bot.send(ev, msg, at_sender=True)
        return


    if cidnum < girlnum:
        msg = f'您的女友没满哦。\n需要达到{girlnum}名女友\n您现在有{cidnum}名。'
        await bot.send(ev, msg, at_sender=True)
        return
    needscore = get_noblescore(level + 1)
    futurename = get_noblename(level + 1)
    needfavor = get_favor_need(level + 1)
    needprestige = get_prestige_need(level + 1)

    if needfavor:
        true_love = count_true_love(gid, uid)
        if true_love < needfavor:
            msg = f'升级到{futurename}需要{needfavor}名挚爱女友(好感>={TRUE_LOVE_FAVOR})，您现在有{true_love}名。'
            await bot.send(ev, msg, at_sender=True)
            return
    if needprestige:
        prestige = score_counter._get_prestige(gid, uid)
        if prestige is None:
            msg = f'升级到{futurename}需要{needprestige}声望，请先发送[开启声望系统]。'
            await bot.send(ev, msg, at_sender=True)
            return
        if prestige < needprestige:
            msg = f'您的声望不足哦。\n升级到{futurename}需要{needprestige}声望，您现在有{prestige}。'
            await bot.send(ev, msg, at_sender=True)
            return
    if score < needscore:
        msg = f'您的金币不足哦。\n升级到{futurename}需要{needscore}金币'
        await bot.send(ev, msg, at_sender=True)
        return
    score_counter._reduce_score(gid, uid, needscore)
    if needprestige:
        score_counter._reduce_prestige(gid, uid, needprestige)
    duel._add_level(gid, uid)
    newlevel = duel._get_level(gid, uid)
    newnoblename = get_noblename(newlevel)
    newgirlnum = get_girlnum_total(gid, uid)
    msg = f'花费了{needscore}金币'
    if needprestige:
        msg += f'和{needprestige}声望'
    msg += f'\n您成功由{noblename}升到了{newnoblename}\n可以拥有{newgirlnum}名女友了哦。'
    await bot.send(ev, msg, at_sender=True)

#购买女友上限（移植自上游0.7）
@sv.on_fullmatch(['购买上限', '增加上限','增加女友上限','购买女友上限'])
async def add_warehouse(bot, ev: CQEvent):
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    gid = ev.group_id
    uid = ev.user_id
    level = duel._get_level(gid, uid)
    current_score = score_counter._get_score(gid, uid)
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来购买上限吧。'
        await bot.finish(ev, msg, at_sender=True)
    if level < 9:
        await bot.finish(ev, '只有国王以上才能增加女友上限哦。', at_sender=True)
    if current_score < SHANGXIAN_NUM:
        msg = f'增加女友上限需要消耗{SHANGXIAN_NUM}金币，您的金币不足哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        housenum = duel._get_warehouse(gid, uid)
        if housenum >= WAREHOUSE_NUM:
            msg = f'您已增加{WAREHOUSE_NUM}次上限，无法继续增加了哦。'
            await bot.finish(ev, msg, at_sender=True)
        duel._add_warehouse(gid, uid, 1)
        score_counter._reduce_score(gid, uid, SHANGXIAN_NUM)
        last_score = current_score - SHANGXIAN_NUM
        myhouse = get_girlnum_total(gid, uid)
        msg = f'您消耗了{SHANGXIAN_NUM}金币，增加了1个女友上限，目前剩余{last_score}金币，女友上限为{myhouse}名'
        await bot.send(ev, msg, at_sender=True)


@sv.on_prefix('分手')
async def breakup(bot, ev: CQEvent):
    if BREAK_UP_SWITCH == True:
        args = ev.message.extract_plain_text().split()
        gid = ev.group_id
        uid = ev.user_id
        duel = DuelCounter()
        level = duel._get_level(gid, uid)
        if level == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        if not args:
            await bot.finish(ev, '请输入分手+pcr角色名。', at_sender=True)
        name = args[0]
        cid = chara.name2id(name)
        if cid == 1000:
            await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
        score_counter = ScoreCounter2()
        needscore = level*100
        score = score_counter._get_score(gid, uid)
        cidlist = duel._get_cards(gid, uid)
        if cid not in cidlist:
            await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
       #检测是否是皇后
        queen = duel._search_queen(gid,uid)
        if cid==queen:
            await bot.finish(ev, '不可以和您的皇后分手哦。', at_sender=True)
        if score < needscore:
            msg = f'您的爵位分手一位女友需要{needscore}金币哦。\n分手不易，做好准备再来吧。'
            await bot.finish(ev, msg, at_sender=True)
        if duel_judger.get_on_off_accept_status(gid):
            msg = '现在正在决斗中哦，不能与女友分手。'
            await bot.finish(ev, msg, at_sender=True)
        score_counter._reduce_score(gid, uid, needscore)
        duel._delete_card(gid, uid, cid)
        c = chara.fromid(cid)
        if random.randint(0,1):
            rproperty = needscore+random.randint(0,200)
            score_counter._add_score(gid, uid, rproperty)
            msg = f'\n“真正离开的那次，关门声最小。”\n你和{c.name}分手了。失去了{needscore}金币分手费。但分割得财产{rproperty}金币。\n{c.icon.cqcode}'
        else:
            msg = f'\n“真正离开的那次，关门声最小。”\n你和{c.name}分手了。失去了{needscore}金币分手费。\n{c.icon.cqcode}'
        await bot.send(ev, msg, at_sender=True)
     


#国王以上声望部分。

@sv.on_fullmatch('开启声望系统')
async def open_prestige(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if prestige != None:
        await bot.finish(ev, '您已经开启了声望系统哦。', at_sender=True)    
    if level != 6:
        await bot.finish(ev, '只有国王才可以开启声望系统哦。', at_sender=True)    
    score_counter._set_prestige(gid,uid,0)
    msg = '成功开启声望系统！国王殿下，向着成为皇帝的目标进发吧。'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('声望系统帮助')
async def prestige_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             声望系统帮助
国王后可开启：开启声望系统
1. 查询声望
2. 加冕仪式  (20000金币+15000声望+6位挚爱)
3. 皇室婚礼+角色名  (3000金币+3000声望，皇帝限一次)
4. 用金币兑换声望
决斗胜+200 / 负-100；皇后不会因决斗被抢
╚                                        ╝
 '''  
    await bot.send(ev, msg)

@sv.on_fullmatch('查询声望')
async def inquire_prestige(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    msg = f'您的声望为{prestige}点。'    
    await bot.send(ev, msg, at_sender=True)    
        
@sv.on_fullmatch(['加冕称帝','加冕仪式'])
async def be_emperor(bot, ev: CQEvent): 
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()  
    prestige = score_counter._get_prestige(gid,uid)
    
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    if level!=9:
        await bot.finish(ev, '只有国王才能进行加冕仪式哦。', at_sender=True)
  
    needfavor = get_favor_need(10)
    true_love = count_true_love(gid, uid)
    if true_love < needfavor:
        await bot.finish(ev, f'加冕仪式需要{needfavor}名挚爱女友(好感>={TRUE_LOVE_FAVOR})，您现在有{true_love}名。', at_sender=True)
    if prestige < 15000: 
        await bot.finish(ev, '加冕仪式需要15000声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 20000:
        await bot.finish(ev, '加冕仪式需要20000金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid,uid,20000)
    score_counter._reduce_prestige(gid,uid,15000)
    duel._set_level(gid, uid, 10)
    msg = '\n礼炮鸣响，教皇领唱“感恩赞美歌”。“皇帝万岁！”\n在民众的欢呼声中，你加冕为了皇帝。\n花费了15000点声望，20000金币。'
    await bot.send(ev, msg, at_sender=True)
        
    
@sv.on_prefix('皇室婚礼')
async def marry_queen(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()  
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)    
    if level < 10:
        await bot.finish(ev, '只有皇帝以上才可以举办皇室婚礼哦。', at_sender=True)  
    if duel._search_queen(gid,uid)!=0:
        await bot.finish(ev, '皇帝只可以举办一次皇室婚礼哦。', at_sender=True)
    if not args:
        await bot.finish(ev, '请输入皇室婚礼+pcr角色名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)        
    if cid not in cidlist:
        await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)        
    if prestige < 3000: 
        await bot.finish(ev, '皇室婚礼需要3000声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 3000:
        await bot.finish(ev, '皇室婚礼需要3000金币，您的金币不足哦。', at_sender=True)
    favor = duel._get_favor(gid,uid,cid)
    if favor < NEED_favor:
        await bot.finish(ev, f'举办婚礼的女友需要达到{NEED_favor}好感，您的好感不足哦。', at_sender=True)       
    score_counter._reduce_prestige(gid,uid,3000)
    score_counter._reduce_score(gid,uid,3000)    
    duel._set_queen_owner(gid,cid,uid)
    c = chara.fromid(cid)
    msg = f'繁杂的皇室礼仪过后\n\n{c.name}与[CQ:at,qq={uid}]\n\n正式踏上了婚礼的殿堂\n成为了他的皇后。\n让我们为他们表示祝贺！\n皇后不会因决斗被抢走了哦。\n{c.icon.cqcode}'
    await bot.send(ev, msg)