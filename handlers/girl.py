# -*- coding: utf-8 -*-
"""贵族决斗：招募/查询/好感/约会/礼物/神秘商店"""
from hoshino import priv
from hoshino.typing import CQEvent
import asyncio
import random
from .. import chara
from .. import sv
from ..core.constants import DATE_EXTRA_COST, DATE_EXTRA_LIMIT, Date10, Date15, Date20, Date5, GIFTCHOICE_DICT, GIFT_DAILY_LIMIT, GIFT_DICT, GIFT_PER_GIRL_DAILY, SHOP_LIMIT, WAIT_TIME_CHANGE
from ..core.db.ce import CECounter
from ..core.db.duel import DuelCounter
from ..core.db.score import ScoreCounter2
from ..core.rules import _gen_shop, check_gift, get_card_ce, get_equip_info_id, get_gift_price, get_noblename, get_relationship
from ..core.state import daily_SHOP_limiter, daily_date_extra_limiter, daily_date_limiter, daily_gift_limiter, daily_gift_per_girl_limiter, duel_judger, gift_change




@sv.on_prefix(['查女友', '查询女友', '查看女友'])
async def search_girl(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    if not args:
        await bot.send(ev, '请输入查女友+pcr角色名。', at_sender=True)
        return
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    owner = duel._get_card_owner(gid, cid)
    c = chara.fromid(cid)
   #判断是否是皇后。
    if duel._get_queen_owner(gid,cid) !=0 :
        owner = duel._get_queen_owner(gid,cid)
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的皇后哦。{c.icon.cqcode}', at_sender=True)

    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。', at_sender=True)
        return
    else:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦。{c.icon.cqcode}'
        await bot.send(ev, msg)

#查名字（移植自上游0.7，按女友序号反查昵称）
@sv.on_prefix(['查姓名', '女友姓名','女友名字','查名字','查昵称'])
async def get_girlname(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入查名字+女友序号(序号即查询贵族中女友排在第几位)。', at_sender=True)
    num = args[0]
    if not num.isdigit():
        await bot.finish(ev, '请输入查名字+女友序号(序号即查询贵族中女友排在第几位)。', at_sender=True)
    num_int = int(num)
    cidlist = duel._get_cards(gid, uid)
    girlnum = len(cidlist)
    if num_int > girlnum:
        await bot.finish(ev, f'你所输入的女友序号{num_int}大于您的女友数{girlnum}名', at_sender=True)
    cid = cidlist[num_int-1]
    if cid == 9999:
        cid = 1059
    namelist = chara.CHARA_NAME[cid]
    namemsg = ''
    for name in namelist:
        namemsg += f'{name},'
    namemsg = namemsg[:-1]
    msg = f'\n您的第{num_int}名女友的昵称为:\n\n{namemsg}'
    await bot.send(ev, msg, at_sender=True)



@sv.on_prefix(['查好感','查询好感'])
async def girl_story(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入查好感+女友名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)

    if duel._get_favor(gid,uid,cid)== None:
        duel._set_favor(gid,uid,cid,0)
    favor= duel._get_favor(gid,uid,cid)
    relationship,text = get_relationship(favor)
    c = chara.fromid(cid)    
    msg = f'\n{c.name}对你的好感是{favor}\n你们的关系是{relationship}\n“{text}”\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['每日约会','女友约会', '贵族约会'])
async def daily_date(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入贵族约会+女友名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    guid = gid ,uid
    score_counter = ScoreCounter2()
    cost_msg = ''
    if daily_date_limiter.check(guid):
        loginnum_ = ['1','2', '3', '4']  
        r_ = [0.2, 0.4, 0.35, 0.05]  
        sum_ = 0
        ran = random.random()
        for num, r in zip(loginnum_, r_):
            sum_ += r
            if ran < sum_ :break
        Bonus = {'1':[5,Date5],
                 '2':[10,Date10],
                 '3':[15,Date15],    
                 '4':[20,Date20]
                }             
        favor = Bonus[num][0]
        text = random.choice(Bonus[num][1])
        daily_date_limiter.increase(guid)
    else:
       #免费约会用完后，可花金币再约会DATE_EXTRA_LIMIT次
        if not daily_date_extra_limiter.check(guid):
            await bot.finish(ev, f'今天已经约会过{1+DATE_EXTRA_LIMIT}次了哦，明天再来吧。', at_sender=True)
        if score_counter._get_score(gid, uid) < DATE_EXTRA_COST:
            await bot.finish(ev, f'今天的免费约会已经用过了，额外约会需要{DATE_EXTRA_COST}金币，您的金币不足哦。', at_sender=True)
        score_counter._reduce_score(gid, uid, DATE_EXTRA_COST)
        daily_date_extra_limiter.increase(guid)
        favor = random.randint(6,10)
        text = random.choice(Date10)
        cost_msg = f'（花费{DATE_EXTRA_COST}金币）'
    duel._add_favor(gid,uid,cid,favor)
    c = chara.fromid(cid)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    msg = f'\n\n{text}\n\n你和{c.name}的好感上升了{favor}点{cost_msg}\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['送礼物','送礼','赠送礼物'])
async def gift_send(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，礼物交换结束再来送礼物吧。")    
    if len(args)!=2:
        await bot.finish(ev, '请输入 送礼物+女友名+礼物名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    gift = args[1]
    if gift not in GIFT_DICT.keys():
        await bot.finish(ev, '请输入正确的礼物名。', at_sender=True)
    gfid = GIFT_DICT[gift]
    if duel._get_gift_num(gid,uid,gfid)==0:
        await bot.finish(ev, '你的这件礼物的库存不足哦。', at_sender=True)
    guidg = gid, uid, cid
    if not daily_gift_per_girl_limiter.check(guidg):
        await bot.finish(ev, f'{chara.fromid(cid).name}今天已经收过{GIFT_PER_GIRL_DAILY}件礼物了哦，明天再来吧。', at_sender=True)
    daily_gift_per_girl_limiter.increase(guidg)
    duel._reduce_gift(gid,uid,gfid)
    favor,text = check_gift(cid,gfid)
    duel._add_favor(gid,uid,cid,favor)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    c = chara.fromid(cid)
    msg = f'\n{c.name}:“{text}”\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)    

@sv.on_fullmatch(['抽礼物','买礼物','购买礼物'])
async def gift_buy(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    guid = gid ,uid
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买礼物吧。'
        await bot.finish(ev, msg, at_sender=True)
    if not daily_gift_limiter.check(guid):
        await bot.finish(ev, f'今天购买礼物已经超过{GIFT_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)     
    select_gift = random.choice(list(GIFT_DICT.keys()))
    gfid = GIFT_DICT[select_gift]
    while(gfid == 10):
        select_gift = random.choice(list(GIFT_DICT.keys()))
        gfid = GIFT_DICT[select_gift]
    price = get_gift_price(gfid)
    score = score_counter._get_score(gid, uid)
    if score < price:
        await bot.finish(ev, f'这个礼物需要{price}金币，您的金币不足哦。', at_sender=True) 
    duel._add_gift(gid,uid,gfid)
    msg = f'\n您花费了{price}金币，\n买到了[{select_gift}]哦，\n欢迎下次惠顾。'
    score_counter._reduce_score(gid,uid,price)
    daily_gift_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)    

@sv.on_rex(r'^买(\d+)(个|份)礼物$')
async def gift_buy_num(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    match = ev['match']
    score_counter = ScoreCounter2()
    guid = gid,uid
    num = int(match.group(1))
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买礼物吧。'
        await bot.finish(ev, msg, at_sender=True)
    if num > (GIFT_DAILY_LIMIT - daily_gift_limiter.checks(guid)):
        await bot.finish(ev, f'今天购买礼物的次数不足哦，您还可以购买{GIFT_DAILY_LIMIT - daily_gift_limiter.checks(guid)}次。', at_sender=True)
    n = num
    giftmsg = ''
    total = 0
    giftids = []
    while(n):
        select_gift = random.choice(list(GIFT_DICT.keys()))
        gfid = GIFT_DICT[select_gift]
        while(gfid == 10):
            select_gift = random.choice(list(GIFT_DICT.keys()))
            gfid = GIFT_DICT[select_gift]
        giftmsg += f'{select_gift} '
        total += get_gift_price(gfid)
        giftids.append(gfid)
        n -= 1
    score = score_counter._get_score(gid, uid)
    if score < total:
        await bot.finish(ev, f'购买{num}份礼物需要{total}金币，您的金币不足哦。', at_sender=True) 
    for gfid in giftids:
        duel._add_gift(gid,uid,gfid)
    msg = f'\n您花费了{total}金币，\n买到了[{giftmsg}]哦，\n欢迎下次惠顾。'
    score_counter._reduce_score(gid,uid,total)
    daily_gift_limiter.increase2(guid,num)
    await bot.send(ev, msg, at_sender=True)   

@sv.on_fullmatch(['礼物仓库','查询礼物','礼物列表'])
async def my_gift(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    msg = f'\n您的礼物仓库如下:'
    giftmsg =''
    for gift in GIFT_DICT.keys():
        gfid = GIFT_DICT[gift]
        num = duel._get_gift_num(gid,uid,gfid)
        if num!=0:
       #补空格方便对齐
            length = len(gift)
            msg_part = '    '*(4-length)
            giftmsg+=f'\n{gift}{msg_part}: {num}件'
    if giftmsg == '':
        await bot.finish(ev, '您现在没有礼物哦，快去发送 买礼物 购买吧。', at_sender=True)        
    msg+=giftmsg
    await bot.send(ev, msg, at_sender=True)         

@sv.on_rex(f'^用(.*)(与|和|跟)(.*)交换(.*)$')
async def change_gift(bot, ev: CQEvent):
    gid = ev.group_id    
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，请勿重复使用指令。")
    gift_change.turn_on_giftchange(gid)
    id1 = ev.user_id
    match = ev['match']
    try:
        id2 = int(ev.message[1].data['qq'])
    except Exception:
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, '参数格式错误')
    if id2 == id1:
        await bot.send(ev, "不能和自己交换礼物！", at_sender=True)
        gift_change.turn_off_giftchange(ev.group_id)
        return             
    gift1 = match.group(1)
    gift2 = match.group(4)
    if gift1 not in GIFT_DICT.keys():
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'礼物1不存在。')
    if gift2 not in GIFT_DICT.keys():
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'礼物2不存在。')        
    gfid1 = GIFT_DICT[gift1]
    gfid2 = GIFT_DICT[gift2]
    if gfid2 == gfid1:
        await bot.send(ev, "不能交换相同的礼物！", at_sender=True)
        gift_change.turn_off_giftchange(ev.group_id)
        return           

    if duel._get_gift_num(gid,id1,gfid1)==0:
        gift_change.turn_off_giftchange(ev.group_id)    
        await bot.finish(ev, f'[CQ:at,qq={id1}]\n您的{gift1}的库存不足哦。')    
    if duel._get_gift_num(gid,id2,gfid2)==0:
        gift_change.turn_off_giftchange(ev.group_id)    
        await bot.finish(ev, f'[CQ:at,qq={id2}]\n您的{gift2}的库存不足哦。')  
    level2 = duel._get_level(gid, id2)
    noblename = get_noblename(level2)
    gift_change.turn_on_waitchange(gid)
    gift_change.set_changeid(gid,id2)
    gift_change.turn_off_accept_giftchange(gid)    
    msg = f'[CQ:at,qq={id2}]\n尊敬的{noblename}您好：\n\n[CQ:at,qq={id1}]试图用[{gift1}]交换您的礼物[{gift2}]。\n\n请在{WAIT_TIME_CHANGE}秒内[接受交换/拒绝交换]。'
    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME_CHANGE)   
    gift_change.turn_off_waitchange(gid)
    if gift_change.get_isaccept_giftchange(gid) is False:
        msg = '\n礼物交换被拒绝。'
        gift_change.init_changeid(gid)
        gift_change.turn_off_giftchange(gid)
        await bot.finish(ev, msg, at_sender=True)    
    duel._reduce_gift(gid,id1,gfid1)
    duel._add_gift(gid,id1,gfid2)    
    duel._reduce_gift(gid,id2,gfid2)
    duel._add_gift(gid,id2,gfid1)     
    msg = f'\n礼物交换成功！\n您使用[{gift1}]交换了\n[CQ:at,qq={id2}]的[{gift2}]。' 
    gift_change.init_changeid(gid)
    gift_change.turn_off_giftchange(gid)
    await bot.finish(ev, msg, at_sender=True)    



@sv.on_fullmatch('接受交换')
async def giftchangeaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if gift_change.get_on_off_waitchange_status(gid):
        if ev.user_id == gift_change.get_changeid(gid):
            msg = '\n礼物交换接受成功，请耐心等待礼物交换结束。'
            await bot.send(ev, msg, at_sender=True)
            gift_change.turn_off_waitchange(gid)
            gift_change.turn_on_accept_giftchange(gid)



@sv.on_fullmatch('拒绝交换')
async def giftchangerefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if gift_change.get_on_off_waitchange_status(gid):
        if ev.user_id == gift_change.get_changeid(gid):
            msg = '\n礼物交换拒绝成功，请耐心等待礼物交换结束。'
            await bot.send(ev, msg, at_sender=True)
            gift_change.turn_off_waitchange(gid)
            gift_change.turn_off_accept_giftchange(gid)



@sv.on_prefix(['购买情报','买情报'])
async def info_buy(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买情报吧。'
        await bot.finish(ev, msg, at_sender=True)    
    if not args:
        await bot.finish(ev, '请输入买情报+女友名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 500:
        await bot.finish(ev, '购买女友情报需要500金币，您的金币不足哦。', at_sender=True)    
    score_counter._reduce_score(gid,uid,500)
    last_num = cid%10
    like = ''
    normal = ''
    dislike = ''
    for gift in GIFT_DICT.keys():
        if GIFT_DICT[gift]==last_num:
            favorite = gift
            continue
        num1 = last_num%3
        num2 = GIFT_DICT[gift]%3
        choicelist = GIFTCHOICE_DICT[num1]

        if num2 == choicelist[0]:
            like+=f'{gift}\n'
            continue
        if num2 == choicelist[1]:
            normal+=f'{gift}\n'
            continue
        if num2 == choicelist[2]:
            dislike+=f'{gift}\n'
            continue    
    c = chara.fromid(cid)       
    msg = f'\n花费了500金币，您买到了以下情报：\n{c.name}特别喜欢的礼物是:\n公主之心\n{c.name}最喜欢的礼物是:\n{favorite}\n喜欢的礼物是:\n{like}一般喜欢的礼物是:\n{normal}不喜欢的礼物是:\n{dislike}{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)  

@sv.on_fullmatch(['好感系统帮助','礼物系统帮助','好感帮助','礼物帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             好感系统帮助
1. 查好感+女友名
2. 贵族约会+女友名(1天限1次)
3. 买[x份]礼物(300金币，一天限5次）
4. 送礼+女友名+礼物
   批量送礼+数量+女友名+礼物
5. 用xx与@qq交换xx
例: 用热牛奶与@南桐交换书
6. 买情报+女友名(500金币，可了解女友喜好)
7. 礼物仓库(查询礼物仓库)
8. 好感列表
9. 神秘商店
注:
通过约会或者送礼可以提升好感
决斗输掉某女友，不足50好感会被抢走
╚                                        ╝
 '''  
    await bot.send(ev, msg)


@sv.on_fullmatch(['好感列表','女友好感列表'])
async def get_favorlist(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter() 
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    cidlist = duel._get_cards(gid, uid)
    if len(cidlist)==0:
        await bot.finish(ev, '您现在还没有女友哦。', at_sender=True)
    favorlist = []
    for cid in cidlist:
        favor = duel._get_favor(gid,uid,cid)
        if favor !=0 and favor!=None:
            favorlist.append({"cid":cid,"favor":favor})
    if len(favorlist)==0:
        await bot.finish(ev, '您的女友好感全部为0哦。', at_sender=True)        
    rows_by_favor = sorted(favorlist, key=lambda r: r['favor'],reverse=True)
    msg = '\n您好感0以上的女友的前10名如下所示:\n'
    num = min(len(rows_by_favor),10)
    for i in range(0,num):
        cid = rows_by_favor[i]["cid"]
        favor = rows_by_favor[i]["favor"]
        c = chara.fromid(cid)
        msg+=f'{c.name}:{favor}点\n'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('重置礼物交换')
async def init_change(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置礼物交换哦。', at_sender=True)
    gift_change.turn_off_giftchange(ev.group_id)
    msg = '已重置本群礼物交换状态！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['神秘商店','今日商店'])
async def shop_view(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来看看吧。'
        await bot.finish(ev, msg, at_sender=True)    
    shop = _gen_shop(gid, uid)
    msg = f'现在神秘商店在出售这些物品\n'
    for shopid in sorted(shop):
        shopname, needgold = shop[shopid]
        msg += f'{shopid}：{shopname} {needgold}金币\n'
    msg += f'发送购买物品+物品编号来购买，神秘商店每小时刷新！每人每天限购{SHOP_LIMIT}次哦\n注意：每个人的商店内容不同哦！\n'
    await bot.send(ev, msg, at_sender=True)  
     
@sv.on_prefix(['购买物品'])
async def shop_buy(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    guid = gid,uid
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if not daily_SHOP_limiter.check(guid):
        await bot.finish(ev, '您今日购买神秘商店商品的次数已达上限喔，明天再来吧！', at_sender=True)
    if len(args)!=1:
        await bot.finish(ev, '请输入 购买物品+物品编号 中间用空格隔开。', at_sender=True)
    try:
        shopid = int(args[0])
    except ValueError:
        await bot.finish(ev, '请输入正确的物品编号。', at_sender=True)
    shop = _gen_shop(gid, uid)
    if shopid not in shop:
        await bot.finish(ev, '请输入正确的物品编号。', at_sender=True)
    shopname, needgold = shop[shopid]
    score = score_counter._get_score(gid, uid)
    if score < needgold:
        await bot.finish(ev, f'购买需要{needgold}金币，您的金币不足哦。', at_sender=True)
    duel._add_gift(gid,uid,GIFT_DICT[shopname])
    daily_SHOP_limiter.increase(guid)
    score_counter._reduce_score(gid,uid,needgold)
    await bot.finish(ev, f'成功购买了{shopname},花费了{needgold}金币。', at_sender=True)    
 
@sv.on_prefix(['批量送礼'])
async def gift_send_batch(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，礼物交换结束再来送礼物吧。")    
    if len(args)!=3:
        await bot.finish(ev, '请输入 批量送礼+礼物数量+女友名+礼物名 中间用空格隔开。', at_sender=True)
    num = int(args[0])
    if num <= 0:
        await bot.finish(ev, "数量输入不正确哦") 
    name = args[1]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    gift = args[2]
    if gift not in GIFT_DICT.keys():
        await bot.finish(ev, '请输入正确的礼物名。', at_sender=True)
    gfid = GIFT_DICT[gift]
    if gfid > 10:
        await bot.finish(ev, '这个物品不能作为礼物哦。', at_sender=True)
    if duel._get_gift_num(gid,uid,gfid) < num:
        await bot.finish(ev, '你的这件礼物的库存不足哦。', at_sender=True)
   #每个女友每天最多收GIFT_PER_GIRL_DAILY件
    guidg = gid, uid, cid
    remaining = GIFT_PER_GIRL_DAILY - daily_gift_per_girl_limiter.checks(guidg)
    if remaining <= 0:
        await bot.finish(ev, f'{chara.fromid(cid).name}今天已经收过{GIFT_PER_GIRL_DAILY}件礼物了哦，明天再来吧。', at_sender=True)
    if num > remaining:
        await bot.finish(ev, f'{chara.fromid(cid).name}今天还能收{remaining}件礼物，请减少数量哦。', at_sender=True)
    x = num
    favor,text = check_gift(cid,gfid)
    while(x):
        duel._reduce_gift(gid,uid,gfid)
        duel._add_favor(gid,uid,cid,favor)
        x -= 1
    daily_gift_per_girl_limiter.increase(guidg, num)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    c = chara.fromid(cid)
    msg = f'\n{c.name}:“{text}”\n\n你和{c.name}的好感上升了{favor*num}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)    

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