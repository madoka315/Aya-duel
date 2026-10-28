# -*- coding: utf-8 -*-
"""贵族决斗：等级、战力、装备、商店等业务规则"""
from PIL import Image
from datetime import datetime
from io import BytesIO
import base64
import json
import math
import os
import pytz
import random
from .. import chara
from .constants import BLACKLIST_ID, CARD_LEVEL_MAX, FILE_PATH, GIFTCHOICE_DICT, GIFT_DICT, GIFT_PRICE, Gift1, Gift10, Gift2, Gift5, LEVEL_COST_DICT, LEVEL_FAVOR_NEED, LEVEL_GIRL_NEED, LEVEL_PRESTIGE_NEED, RELATIONSHIP_DICT, RECRUIT_BASE_COST, RECRUIT_COST_STEP, RECRUIT_FAIL_RATE, TRUE_LOVE_FAVOR
from .db.ce import CECounter
from .db.duel import DuelCounter
from .dlc import get_dlc_blacklist




# 生成没被约过的角色列表
def get_newgirl_list(gid):
    chara_id_list = list(chara.CHARA_NAME.keys())
    duel = DuelCounter()
    old_list = duel._get_card_list(gid)
    dlc_blacklist = get_dlc_blacklist(gid)
    new_list = []
    for card in chara_id_list:
        if card not in BLACKLIST_ID and card not in old_list and card not in dlc_blacklist:
            new_list.append(card)
    return new_list


# 取爵位名
def get_noblename(level: int):
    namedict = {
        "1": "男爵",
        "2": "子爵",
        "3": "伯爵",
        "4": "侯爵",
        "5": "公爵",
        "6": "大公",
        "7": "亲王",
        "8": "王储",
        "9": "国王",
        "10": "皇帝",
        "11": "圣王",
        "12": "神帝"
    }
    return namedict[str(level)]


# 返回爵位对应的女友数
def get_girlnum(level: int):
    numdict = LEVEL_GIRL_NEED
    return numdict[str(level)]


# 返回含购买上限加成的女友数上限（移植自上游0.7 购买上限功能）
def get_girlnum_total(gid, uid):
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    if level == 0:
        return 0
    return get_girlnum(level) + duel._get_warehouse(gid, uid)


# 返回升级到爵位所需要的金币数
def get_noblescore(level: int):
    numdict = LEVEL_COST_DICT
    return numdict[str(level)]


# 返回升级到爵位所需要的声望（未配置的等级为0）
def get_prestige_need(level: int):
    return LEVEL_PRESTIGE_NEED.get(str(level), 0)


# 返回升级到爵位所需要的挚爱女友数
def get_favor_need(level: int):
    return LEVEL_FAVOR_NEED.get(str(level), 0)


# 统计挚爱（好感>=TRUE_LOVE_FAVOR）女友数量
def count_true_love(gid, uid):
    duel = DuelCounter()
    num = 0
    for cid in duel._get_cards(gid, uid):
        if (duel._get_favor(gid, uid, cid) or 0) >= TRUE_LOVE_FAVOR:
            num += 1
    return num


# 单次招募花费：随爵位与已有女友数递增
def get_recruit_cost(level, girl_count):
    base = RECRUIT_BASE_COST.get(level, 600)
    step = RECRUIT_COST_STEP.get(level, 20)
    return base + step * girl_count


# 招募失败率：爵位越高越稳
def get_recruit_fail_rate(level):
    return RECRUIT_FAIL_RATE.get(level, 0.12)


# 礼物售价（公主之心10不售卖，兜底按300算）
def get_gift_price(giftid):
    return GIFT_PRICE.get(giftid, 300)

# 判断当前女友数是否大于于爵位上限
def girl_outlimit(gid,uid):
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    girlnum = get_girlnum_total(gid, uid)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist) 
    if cidnum > girlnum:
        return True
    else: 
        return False
        

        
#魔改图片拼接 
def concat_pic(pics, border=0):
    num = len(pics)
    w= pics[0].size[0]
    h_sum = 0
    for pic in pics:
        h_sum += pic.size[1]
    des = Image.new('RGBA', (w, h_sum + (num-1) * border), (255, 255, 255, 255))
    h = 0
    for i, pic in enumerate(pics):
        des.paste(pic, (0, (h + i*border)), pic)
        h += pic.size[1]        
    return des

#增加角色经验
def add_exp(gid,uid,cid,exp):
    CE = CECounter()
    now_level = CE._get_card_level(gid, uid, cid)
    level_flag = 0
    need_exp = (now_level+1)*100
    exp_info = CE._get_card_exp(gid, uid, cid)
    now_exp = exp_info + exp
    if now_level>=CARD_LEVEL_MAX:
        level_flag = 1
        last_exp = now_exp
        now_exp = 0
    while now_exp>=need_exp:
        now_level = now_level+1
        now_exp = now_exp-need_exp
        need_exp = (now_level+1)*100 
        if now_level>=CARD_LEVEL_MAX:
            level_flag = 1
            last_exp = now_exp
            now_exp = 0
            break
    if level_flag == 1:
        CE._add_card_exp(gid, uid, cid, now_level, now_exp)
        CE._add_exp_chizi(gid, uid, last_exp)
        msg = f"\n目前等级为{now_level}，由于超出等级上限，{last_exp}点经验加入经验池"
        return [1,last_exp,msg]
    else:
        CE._add_card_exp(gid, uid, cid, now_level, now_exp)
        msg = f"\n目前等级为{now_level}"
        return [0,now_level,msg]

#随机获得一件装备并返回获得信息
def add_equip_info(gid,uid,level,down_list):
    CE = CECounter()
    # 加载装备列表
    equiplist={}
    with open(os.path.join(FILE_PATH,'equipment.json'),'r',encoding='UTF-8') as fa:
        equiplist = json.load(fa, strict=False)  
    equiplistinfo = []
    for equiplevel in equiplist:
        if str(level) == str(equiplist[equiplevel]['level']):
            equiplistinfo = equiplist[equiplevel]
            break
    equipid = random.sample(down_list,1)
    equipinfo = []
    for eid in equiplistinfo['e_list']:
        #print(equipid[0])
        #print(equiplistinfo['e_list'][eid]['eid'])
        if str(equipid[0]) == str(equiplistinfo['e_list'][eid]['eid']):
            equipinfo = equiplistinfo['e_list'][eid]
            equipinfo['model'] = equiplistinfo['model']
            CE._add_equip(gid, uid, equipid[0], 1)
            break
    return equipinfo

#根据装备名称获取装备信息
def get_equip_info_name(ename):
    equiplist={}
    with open(os.path.join(FILE_PATH,'equipment.json'),'r',encoding='UTF-8') as fa:
        equiplist = json.load(fa, strict=False)  
    equipinfo = []
    fand_flag = 0
    for i in equiplist:
        if fand_flag == 1:
            break
        for j in equiplist[i]['e_list']:
            if str(ename) == str(equiplist[i]['e_list'][j]['name']):
                equipinfo = equiplist[i]['e_list'][j]
                equipinfo['model'] = equiplist[i]['model']
                fand_flag = 1
                break
    return equipinfo

#抽卡
def get_gecha_equip(gid, uid, gechanum, xnum, dnum, gechainfo):
    equip_list = ''
    CE = CECounter()
    xingchenlist={
        1:1,
        2:1,
        3:2,
        4:5,
        5:10,
        6:20,
    }
    get_xcz = 0
    for i in range(gechanum):
        xnum = xnum + 1
        dnum = dnum + 1
        #获取本次抽卡类型
        if dnum == int(gechainfo['up_num']):
            #抽大保底
            charinfo = gechainfo['dgecha']
        elif xnum == 10:
            #抽10连小保底
            charinfo = gechainfo['xgecha']
        else:
            #普通抽卡
            charinfo = gechainfo['gecha']
        
        equip_type_run = int(math.floor( random.uniform(1,100) ))
        get_equip_quality = 1
        z_equip_quality = 0
        for gechalevel in charinfo['quality']:
            z_equip_quality = z_equip_quality + charinfo['quality'][gechalevel]
            if z_equip_quality>=equip_type_run:
                get_equip_quality = int(gechalevel)
                break
        down_list=[]
        for equip_down in charinfo['equip']:
            if int(get_equip_quality) == int(equip_down):
                down_list = charinfo['equip'][equip_down]
        if get_equip_quality >= 4:
            xnum = 0
            dnum = 0
        elif get_equip_quality == 3:
            xnum = 0
        #随机获得一个品质的装备
        equip_info = add_equip_info(gid,uid,get_equip_quality,down_list)
        get_xc = xingchenlist[get_equip_quality]
        get_xcz = get_xcz + get_xc
        #print(equip_info)
        equip_list = equip_list + f"\n{equip_info['model']}品质{equip_info['type']}:{equip_info['name']}"
    now_num = CE._add_xingchen_num(gid, uid, get_xcz)
    CE._add_gecha_num(gid, uid, xnum, dnum)
    msg = f"{equip_list}\n您总共获得了{get_xcz}星尘，目前星尘数量为{now_num}个\n300个星尘可以兑换本期UP的UR装备哦"
    return msg



#获取蛋池信息
def get_gecha_info(gechaname):
    gechalist={}
    with open(os.path.join(FILE_PATH,'equipgecha.json'),'r',encoding='UTF-8') as fa:
        gechalist = json.load(fa, strict=False)  
    gechainfo = []
    for gecha in gechalist:
        if str(gechaname) == str(gechalist[gecha]['name']):
            gechainfo = gechalist[gecha]
            break
    return gechainfo

#返回boss图片
def get_boss_icon(bossname):
    PIC_PATH = os.path.join(FILE_PATH,'boss')
    path = os.path.join(PIC_PATH,f'{bossname}.JPG')
    mes = ''
    if  os.path.exists(path):
        img = Image.open(path)
        bio = BytesIO()
        img.save(bio, format='JPEG')
        base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
        mes = f"[CQ:image,file={base64_str}]"   
    return mes

def get_nextbossinfo(zhoumu,bossid,shijieflag):
    bosslist={}
    with open(os.path.join(FILE_PATH,'bossinfo.json'),'r',encoding='UTF-8') as fa:
        bosslist = json.load(fa, strict=False)  
    bossinfo = []
    for x in bosslist:
        if zhoumu in bosslist[x]['zhoumu']:
            for j in bosslist[x]['bosslist']:
                if str(bossid) == str(bosslist[x]['bosslist'][j]['bossid']):
                    bossinfo=bosslist[x]['bosslist'][j]
                    bossinfo['zhoumu'] = zhoumu
                    bossinfo['icon'] = get_boss_icon(bosslist[x]['bosslist'][j]['name'])
                    if shijieflag == 1:
                        bossinfo['hp'] = bossinfo['hp']*10
                    break
    return bossinfo

#获取当前群的boss状态
def get_boss_info(gid):
    CE = CECounter()
    bosslist={}
    with open(os.path.join(FILE_PATH,'bossinfo.json'),'r',encoding='UTF-8') as fa:
        bosslist = json.load(fa, strict=False)  
    bossinfo = []
    #此处写数据库查询boss信息
    #print('群id:'+str(gid))
    nowinfo=CE._get_bossinfo(gid)
    #print(nowinfo)
    for x in bosslist:
        if nowinfo[0] in bosslist[x]['zhoumu']:
            for j in bosslist[x]['bosslist']:
                if str(nowinfo[1]) == str(bosslist[x]['bosslist'][j]['bossid']):
                    bossinfo=bosslist[x]['bosslist'][j]
                    bossinfo['zhoumu'] = nowinfo[0]
                    bossinfo['icon'] = get_boss_icon(bosslist[x]['bosslist'][j]['name'])
                    if nowinfo[2]>0:
                        bossinfo['hp'] = nowinfo[2]
                    else:
                        if gid == 999:
                            bossinfo['hp'] = bossinfo['hp']*10
                    
                    break
    return bossinfo
    
#根据装备id获取装备信息
def get_equip_info_id(eid):
    equiplist={}
    with open(os.path.join(FILE_PATH,'equipment.json'),'r',encoding='UTF-8') as fa:
        equiplist = json.load(fa, strict=False)  
    equipinfo = []
    fand_flag = 0
    for i in equiplist:
        if fand_flag == 1:
            break
        for j in equiplist[i]['e_list']:
            if str(eid) == str(equiplist[i]['e_list'][j]['eid']):
                equipinfo = equiplist[i]['e_list'][j]
                equipinfo['model'] = equiplist[i]['model']
                fand_flag = 1
                break
    return equipinfo
    
#查询单角色战力
def get_card_ce(gid,uid,cid):
    duel = DuelCounter()
    CE = CECounter()
    #获取角色时装穿戴信息
    #获取角色等级
    level_info = CE._get_card_level(gid, uid, cid)
    level_ce = level_info*50
    #获取角色穿戴装备列表
    equip_ce = 0
    dreeslist = CE._get_dress_list(gid, uid, cid)
    for eid in dreeslist:
        equipinfo = get_equip_info_id(eid)
        if equipinfo:
            equip_ce = equip_ce + equipinfo['add_ce']
    #获取角色好感信息
    favor= duel._get_favor(gid,uid,cid)
    #计算角色好感战力加成
    favor_ce = math.ceil(favor/500*200)
    #计算角色rank战力加成
    rank = CE._get_rank(gid, uid, cid)
    card_ce=math.ceil((100+level_ce+favor_ce+equip_ce)*(1+rank/10))
    return card_ce

#获取战力排行榜
def get_power_rank(gid):
    duel = DuelCounter()
    CE = CECounter()
    girls = CE._get_cards_byrank(gid,20)
    if len(girls)>0:
        data = sorted(girls,key=lambda cus:cus[1],reverse=True)
        new_data = []
        for girl_data in data:
            gid1, rank, uid, cid = girl_data
            gpower = get_card_ce(gid1,uid,cid)
            new_data.append((rank,gpower,uid,cid))
        rankData = sorted(new_data,key=lambda cus:cus[1],reverse=True)
        return rankData
    else:
        return []

#返回副本信息
def get_dun_info(dunname):
    # 加载副本列表
    dungeonlist={}
    with open(os.path.join(FILE_PATH,'dungeon.json'),'r',encoding='UTF-8') as fa:
        dungeonlist = json.load(fa, strict=False)  
    dungeoninfo = []
    findnum = 0
    for dungeon in dungeonlist:
        if str(dunname) == str(dungeonlist[dungeon]['name']):
            dungeoninfo = dungeonlist[dungeon]
            findnum = 1
            break
    if findnum==1:
        return dungeoninfo
    else:
        return ''

async def get_user_card(bot, user_id):
    name = await bot.get_stranger_info(user_id=user_id)
    return name['nickname']

#返回好感对应的关系和文本
def get_relationship(favor):
    for relation in RELATIONSHIP_DICT.keys():
        if favor >= relation:
            relationship = RELATIONSHIP_DICT[relation]
    return relationship[0],relationship[1]

#根据角色id和礼物id，返回增加的好感和文本

def check_gift(cid,giftid):
    lastnum = cid%10
    if giftid == 10:
        favor = 20
        text = random.choice(Gift10)
        return favor, text
    if lastnum == giftid:
        favor = 10
        text = random.choice(Gift10)
        return favor, text
    num1=lastnum%3
    num2=giftid%3
    choicelist = GIFTCHOICE_DICT[num1]

    if num2 == choicelist[0]:
        favor = 5
        text = random.choice(Gift5)
        return favor, text
    if num2 == choicelist[1]:
        favor = 2
        text = random.choice(Gift2)
        return favor, text        
    if num2 == choicelist[2]:
        favor = 1
        text = random.choice(Gift1)
        return favor, text

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d        

def _gen_shop(gid, uid):
    """按 群+人+小时+日+月 生成神秘商店，返回{编号: (礼物名, 价格)}"""
    nows = datetime.now(pytz.timezone('Asia/Shanghai'))
    seed = gid+uid+nows.hour+nows.day+nows.month
    rng = random.Random(seed)
    num1 = rng.randint(0,2)
    num2 = rng.randint(3,5)
    num3 = rng.randint(6,8)
    num4 = rng.randint(9,10)
    num5 = rng.randint(5,10)
    id2gift = {giftid: giftname for giftname, giftid in GIFT_DICT.items()}
    shop = {
        1: (id2gift[num1], rng.randint(1,10)*200),
        2: (id2gift[num2], rng.randint(2,10)*200),
        3: (id2gift[num3], rng.randint(3,10)*200),
    }
    if num4 < 10:
        shop[4] = (id2gift[num4], rng.randint(4,10)*200)
    else:
        shop[4] = (id2gift[num4], rng.randint(4,10)*400)
   #5号位为限定的公主之心，仅在抽到10时上架
    if num5 == 10:
        shop[5] = (id2gift[10], 1000+rng.randint(5,10)*200)
    return shop

def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]