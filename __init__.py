import asyncio
import base64
import os
import random
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from hoshino import Service, priv
from hoshino.modules.priconne import _pcr_data_duel
from hoshino.modules.priconne import chara_duel as chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json
import pytz
import nonebot
import hoshino
from nonebot import on_command, on_request
from nonebot import get_bot
from .CECounter import *

sv = Service('贵族决斗', enable_on_default=False)
DUEL_DB_PATH = os.path.expanduser('~/.hoshino/pcr_duel.db')
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')

FORWARD_QQ = 794275021
FORWARD_QNAME = 'PCR-DUEL-Aya'

BLACKLIST_ID = [1000, 1072, 4031, 9000, 1069, 1073,1067,1907,1910,1913,1914,1916,1917,1919,9601,9602,9603,9604]# 黑名单ID
WAIT_TIME = 30# 对战接受等待时间
WAIT_TIME_jy = 30#交易接受等待时间
DUEL_SUPPORT_TIME = 30# 赌钱等待时间
DB_PATH = os.path.expanduser("~/.hoshino/pcr_duel.db")
SIGN_DAILY_LIMIT = 1 # 机器人每天签到的次数
DUEL_DAILY_LIMIT = 10#每个人每日发起决斗上限
DUN_DAILY_LIMIT = 6 #每个人每日副本上限
BOSS_DAILY_LIMIT = 3 #会战与世界boss次数
EQUIP_DAILY_LIMIT = 5 #副本商城兑换次数
SW_DAILY_LIMIT = 5000#金币兑换声望限制
G2DUN_LIMIT = 10000
ALLOWANCE_DAILY_LIMIT = 10
RESET_HOUR = 0 # 每日使用次数的重置时间，0代表凌晨0点，1代表凌晨1点，以此类推
GACHA_COST = 300 # 抽老婆需求
SHANGXIAN_NUM = 1000 #增加女友上限所需金币
WAREHOUSE_NUM = 20 #仓库增加上限次数
CARD_LEVEL_MAX = 100 #女友等级上限
GECHA_DUNDCORE = 50#抽武器所需副本币
ZERO_GET_AMOUNT = 50 # 没钱补给量
WIN_NUM = 1#下注获胜赢得的倍率
WIN_EXP = 100 #决斗胜利获得经验
BREAK_UP_SWITCH = True#分手系统开关
Remake_LIMIT = 1
Zhuan_Low_LIMIT = 100
#礼物部分
DATE_DAILY_LIMIT = 1#每天女友约会次数上限
GIFT_DAILY_LIMIT = 5#每日购买礼物次数上限 
SHOP_LIMIT = 2#神秘商店次数
WAIT_TIME_CHANGE = 30#礼物交换等待时间
#第一名妻子部分
NEED_favor = 200#成为妻子所需要的好感，为0表示关闭
favor_reduce_NEED = 50#当好感度高于多少时，输扣好感度
favor_reduce = 10#当输掉女友时，损失的好感度
FILE_PATH = os.path.dirname(__file__)#用于加载dlcjson
FULLCARD_PATH = os.path.join(FILE_PATH, 'fullcard')
LEVEL_GIRL_NEED = {
        "1": 3,
        "2": 5,
        "3": 7,
        "4": 10,
        "5": 15,
        "6": 20,
        "7": 30
    }# 升级所需要的老婆，格式为["等级“: 需求]
LEVEL_COST_DICT = {
        "1": 0,
        "2": 100,
        "3": 300,
        "4": 500,
        "5": 1000,
        "6": 2000
    }# 升级所需要的钱钱，格式为["等级“: 需求]

RELATIONSHIP_DICT = {
        0:["初见","浣花溪上见卿卿，脸波明，黛眉轻。"],
        30:["相识","有美一人，清扬婉兮。邂逅相遇，适我愿兮。"],
        60:["熟悉","夕阳谁唤下楼梯，一握香荑。回头忍笑阶前立，总无语，也依依。"],
        100:["朋友","锦幄初温，兽烟不断，相对坐调笙。"],
        150:["朦胧","和羞走，倚门回首，却把青梅嗅。"],
        200:["喜欢","夜月一帘幽梦，春风十里柔情。"],
        300:["依恋","愿我如星君如月，夜夜流光相皎洁。"],
        500:["挚爱","江山看不尽，最美镜中人。"]
    }       

GIFT_DICT = {
        "玩偶"    :0,
        "礼服"    :1,
        "歌剧门票":2,
        "水晶球"  :3,
        "耳环"    :4,
        "发饰"    :5,
        "小裙子"  :6,
        "热牛奶"  :7,
        "书"      :8,
        "鲜花"    :9,
        "公主之心" :10
    }  

GIFTCHOICE_DICT={
        0:[0,2,1],
        1:[1,0,2],
        2:[2,1,0],
}    

MAX_RANK = 10 #最大rank等级
RANK_LIST = {
    1: 300,
    2: 600,
    3: 900,
    4: 1200,
    5: 1700,
    6: 2200,
    7: 2700,
    8: 3500,
    9: 4500,
    10: 6000,
}# rank升级要求，格式为["rank":金币]


Gift10=[
    "这个真的可以送给我吗，谢谢(害羞的低下了头)。",
    "你是专门为我准备的吗，你怎么知道我喜欢这个呀，谢谢你！",
    "啊，我最喜欢这个，真的谢谢你。"
]

Gift5=[
    "谢谢送我这个，我很开心。",
    "这个我很喜欢，谢谢。",
    "你的礼物我都很喜欢哦，谢谢。"
]

Gift2=[
    "送我的吗，谢谢你。",
    "谢谢你的礼物。",
    "为我准备了礼物吗，谢谢。"    
]

Gift1=[
    "不用为我特意准备礼物啦，不过还是谢谢你哦。",
    "嗯，谢谢。",
    "嗯，我收下了，谢谢你。"
]
Addgirlfail = [
    '你参加了一场贵族舞会，热闹的舞会场今天竟然没人同你跳舞。',
    '你邀请到了心仪的女友跳舞，可是跳舞时却踩掉了她的鞋，她生气的离开了。',
    '你为这次舞会准备了很久，结果一不小心在桌子上睡着了，醒来时只看到了过期的邀请函。',
    '你参加了一场贵族舞会，可是舞会上只有一名男性向你一直眨眼。',
    '你准备参加一场贵族舞会，可惜因为忘记穿礼服，被拦在了门外。',
    '你沉浸在舞会的美食之中，忘了此行的目的。',
    '你本准备参加舞会，却被会长拉去出了一晚上刀。',
    '舞会上你和另一个贵族发生了争吵，你一拳打破了他的鼻子，两人都被请出了舞会。',
    '舞会上你很快约到了一名女伴跳舞，但是她不是你喜欢的类型。',
    '你约到了一位心仪的女伴，但是她拒绝了与你回家，说想再给你一个考验。',
    '你和另一位贵族同时看中了一个女孩，但是在三人交谈时，你渐渐的失去了话题。'
]
Addgirlsuccess = [
    '你参加了一场贵族舞会，你优雅的舞姿让每位年轻女孩都望向了你。',
    '你参加了一场贵族舞会，你的帅气使你成为了舞会的宠儿。',
    '你在舞会门口就遇到了一位女孩，你挽着她的手走进了舞会。',
    '你在舞会的闲聊中无意中谈到了自己显赫的家室，你成为了舞会的宠儿。',
    '没有人比你更懂舞会，每一个女孩都为你的风度倾倒。',
    '舞会上你没有约到女伴，但是舞会后却有个女孩偷偷跟着你回了家。',
    '舞会上你和另一个贵族发生了争吵，一位女孩站出来为你撑腰，你第一次的注意到了这个可爱的女孩。',
    '你强壮的体魄让女孩们赞叹不已，她们纷纷来问你是不是一位军官。',
    '你擅长在舞会上温柔地对待每一个人，女孩们也向你投来了爱意。',
    '一个可爱的女孩一直在舞会上望着你，你犹豫了一会，向她发出了邀请。'
  
]

Login100 =[
    '今天是练习击剑的一天，不过你感觉你的剑法毫无提升。',
    '优雅的贵族从不晚起，可是你今天一直睡到了中午。',
    '今天你点了一份豪华的午餐却忘记了带钱，窘迫的你毫无贵族的姿态。',
    '今天你在路上看上了别人的女友，却没有鼓起勇气向他决斗。',
    '今天你十分抑郁，因为发现自己最近上升的只有体重。'

]

Login200 =[
    '今天是练习击剑的一天，你感觉到了你的剑法有所提升。',
    '早起的你站在镜子前许久，天底下竟然有人可以这么帅气。',
    '今天你搞到了一瓶不错的红酒，你的酒窖又多了一件存货。',
    '今天巡视领地时，一个小孩子崇拜地望着你，你感觉十分开心。',
    '今天一个朋友送你一张音乐会的门票，你打算邀请你的女友同去。',
    '今天一位国王的女友在路上向你抛媚眼，也许这就是个人魅力吧。'
    
]


Login300 =[
    '今天是练习击剑的一天，你感觉到了你的剑法大有长进。',
    '今天你救下了一个落水的小孩，他的家人说什么也要你收下一份心意。',
    '今天你巡视领地时，听到几个小女孩说想长大嫁给帅气的领主，你心里高兴极了。',
    '今天你打猎时猎到了一只鹿，你骄傲的把鹿角加入了收藏。',
    '今天你得到了一匹不错的马，说不定可以送去比赛。'
    
]

Login600 =[
    '今天是练习击剑的一天，你觉得自己已经可谓是当世剑圣。',
    '今天你因为领地治理有方，获得了皇帝的嘉奖。',
    '今天你的一位叔叔去世了，无儿无女的他，留给了你一大笔遗产。',
    '今天你在比武大会上获得了优胜，获得了全场的喝彩。',
    '今天你名下的马夺得了赛马的冠军，你感到无比的自豪。'
      
]
Date5 =[
    '你比约会的时间晚到了十分钟，嘟着嘴的她看起来不太满意。',
    '一向善于言辞的你，今天的约会却不时冷场，她看起来不是很开心。',
    '今天的约会上你频频打哈欠，被她瞪了好几次，早知道昨晚不该晚睡的。',
    '“为您旁边的这个姐姐买朵花吧。”你们被卖花的男孩拦下，你本想买花却发现自己忘记了带钱，她看起来不是很开心。'
]

Date10 =[
    '你带她去熟悉的餐厅吃饭，她觉得今天过得很开心。',
    '你带她去看了一场马术表演，并约她找机会一起骑马出去，她愉快的答应了。',
    '“为您旁边的这个姐姐买朵花吧。”你们被卖花的男孩拦下，你买了一束花还给了小孩一笔小费，你的女友看起来很开心。',
    '你邀请她去看一场歌剧，歌剧中她不时微笑，看起来十分开心。'
]

Date15 =[
    '你和她一同骑马出行，两个人一同去了很多地方，度过了愉快的一天。',
    '你新定做了一件最新款的礼服，约会中她称赞你比往常更加帅气。',
    '你邀请她共赴一场宴会，宴会上你们无所不谈，彼此间的了解增加了。',
    '你邀请她去看一场歌剧，歌剧中她一直轻轻地握着你的手。'  
]

Date20 =[
    '你邀请她共赴一场宴会，宴会中她亲吻了你的脸颊后，害羞的低下了头，这必然是你和她难忘的一天。',
    '约会中你们被一群暴民劫路，你为了保护她手臂受了伤。之后她心疼的抱住了你，并为你包扎了伤口。',
    '你邀请她去看你的赛马比赛，你骑着爱马轻松了夺取了第一名，冲过终点后，你大声地向着看台喊出了她的名字，她红着脸低下了头。',
    '你和她共同参加了一场盛大的舞会，两人的舞步轻盈而优雅，被评为了舞会第一名，上台时你注视着微笑的她，觉得她今天真是美极了。'
]
#帮助中猜角色猜头像获胜加金币为个人魔改，如果不魔改可以删掉这两行描述。
@sv.on_fullmatch(['贵族决斗帮助','贵族帮助','贵族指令'])
async def duel_help(bot, ev: CQEvent):
    msg='''
╔                                       ╗    
        贵族决斗相关指令

   1.贵族签到(每日一次)
   2.查询贵族
   3.本群贵族
   4.贵族决斗+艾特
   5.领金币/查金币
   6.贵族舞会(招募女友)
   7.查女友+角色名
   8.升级贵族
   9.重置金币+qq (限群主)
   10.重置角色+qq (限群主) 
   11.重置决斗/重置礼物交换
   (限管理，卡住时用)
   12.分手+角色名(需分手费)
   13.为@qq转账xxx金币
   14.用xxx金币与@qq交易女友+角色名
       (交易需10%手续费)
   15.确认重开(删号重来)
   16.声望排行/胜场排行/女友排行
   17.武器列表(更换决斗武器)
   18.查询本群不决斗惩罚
   19.用金币兑换声望
   20.神秘商店
   21.购买上限(限国王以上)
   22.查名字+女友序号
   
  一个女友只属于一位群友；皇帝可迎娶正妻
  可以从签到、决斗、小游戏等途径入手金币
  从决斗、兑换等途径获取声望
  
  其他帮助：
  →声望系统帮助
  (声望系统国王可开)
  →好感系统帮助
  →dlc帮助
  →战斗系统帮助(女友战斗力相关)
  →副本系统帮助(副本战相关)
  →会战系统帮助(boss战相关)
  →抽卡系统帮助(女友装备相关)
╚                                        ╝
'''  
    data = {
            "type":"node",
            "data":{
                "name":f'贵族查询',
                "uin":f'{FORWARD_QQ}',
                "content":msg
            }
    }
    gid = ev.group_id
    await bot.send_group_forward_msg(group_id=gid, messages=data)
#加载DLC部分代码
#这里记录每个dlc的列表范围

blhxlist = range(6000,6506)
yozilist = range(1523,1544)
genshinlist = range(7001,7033)
collelist = range(4001,4639)
koilist = range(7100,7104)
cloverlist = range(7300,7307)
fgolist = range(8001,8301)
amairolist = range(1300,1304)
nekoparalist = range(9110,9116)
pjsklist = range(9400,9460)
bangdreamlist = range(1601,1636)
mrfzlist = range(5001,5180)

#这里记录dlc名字和对应列表
#已退休DLC（million/sakukoi/majsoul/noraneko/umamusume/punishing/vtuber/mangekyou/tsubakioka）
#相关代码、数据与持有记录已于2026-10-28彻底移除，勿再添加。
dlcdict = {
        'blhx':blhxlist,
        'yozi':yozilist,
        'genshin':genshinlist,
        'kancolle':collelist,
        'koikake':koilist,
        'cloverdays':cloverlist,
        'fgo':fgolist,
        'amairochoco':amairolist,
        'nekopara':nekoparalist,
        'pjsk':pjsklist,
        'bangdream':bangdreamlist,
        'mrfz':mrfzlist
        }

dlcdict2 = {
        }


#这里记录每个dlc的介绍
dlcintro = {
        'blhx':'碧蓝航线手游角色包。',
        'yozi':'柚子社部分角色包。',
        'genshin':'原神角色包。',
        'kancolle':'舰队collection角色包',
        'koikake':'恋×シンアイ彼女角色包',
        'cloverdays':'Clover Days角色包',
        'fgo':'FGO手游角色包',
        'amairochoco':'巧克甜恋角色包',
        'nekopara':'Nekopara角色包',
        'pjsk':'啤酒烧烤角色包',
        'bangdream':'BanG Dream!手游角色包',
        'mrfz':'明日方舟手游角色包'
        }




# 这个字典保存保存每个DLC开启的群列表，pcr默认一直开启。
dlc_switch={}

with open(os.path.join(FILE_PATH,'dlc_config.json'),'r',encoding='UTF-8') as f:
    dlc_switch = json.load(f, strict=False)
def save_dlc_switch():
    with open(os.path.join(FILE_PATH,'dlc_config.json'),'w',encoding='UTF-8') as f:
        json.dump(dlc_switch,f,ensure_ascii=False)



@sv.on_prefix(['加载dlc','加载DLC','开启dlc','开启DLC'])
async def add_dlc(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有管理员才能加载dlc哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>= 2:
        await bot.finish(ev, '指令格式错误。', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入加载dlc+dlc名。', at_sender=True)
    dlcname = args[0]
    if dlcname not in dict(dlcdict, **dlcdict2).keys():
        print(dlcname,dlcdict2.keys())
        await bot.finish(ev, 'DLC名填写错误。', at_sender=True)        

    if gid in dlc_switch[dlcname]:
        await bot.finish(ev, '本群已开启此dlc哦。', at_sender=True)
    dlc_switch[dlcname].append(gid)
    save_dlc_switch()
    await bot.finish(ev, f'加载dlc {dlcname}  成功!', at_sender=True)
        
    

@sv.on_prefix(['卸载dlc','卸载DLC','关闭dlc','关闭DLC'])
async def delete_dlc(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有管理员才能卸载dlc哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>= 2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入卸载dlc+dlc名。', at_sender=True)
    dlcname = args[0]
    if dlcname not in dict(dlcdict, **dlcdict2).keys():
        await bot.finish(ev, 'DLC名填写错误', at_sender=True)        

    if gid not in dlc_switch[dlcname]:
        await bot.finish(ev, '本群没有开启此dlc哦。', at_sender=True)
    dlc_switch[dlcname].remove(gid)
    save_dlc_switch()
    await bot.finish(ev, f'卸载dlc {dlcname}  成功!', at_sender=True)
    


@sv.on_fullmatch(['dlc列表','DLC列表','dlc介绍','DLC介绍'])
async def intro_dlc(bot, ev: CQEvent):
    msg = '可用DLC列表：\n\n'
    i=1
    for dlc in dlcdict.keys():
        msg+=f'{i}.{dlc}:\n'
        intro = dlcintro[dlc]
        msg+=f'介绍:{intro}\n'
        num = len(dlcdict[dlc])
        msg+=f'共有{num}名角色\n'
        i+=1
    msg+= '发送 加载\卸载dlc+dlc名\n可加载\卸载dlc\n卸载的dlc不会被抽到，但是角色仍留在玩家仓库，可以被抢走。'    
        
    data ={
             "type": "node",
             "data": {
                 "name": f'DLC介绍',
                 "uin": f'{FORWARD_QQ}',
                 "content": msg
             }
             }
    await bot.send_group_forward_msg(group_id=ev.group_id, messages=data)

@sv.on_fullmatch(['dlc帮助','DLC帮助','dlc指令','DLC指令'])
async def help_dlc(bot, ev: CQEvent):
    msg = '''
╔                                 ╗
         DLC帮助
      
  1.加载\卸载dlc+dlc名
  2.dlc列表(查看介绍)
  
  卸载的dlc不会被抽到
  但是角色仍留在仓库
  可以被他人抢走
  
╚                                 ╝    
'''
    await bot.finish(ev, msg)




#取得该群未开启的dlc所形成的黑名单
def get_dlc_blacklist(gid):

    dlc_blacklist=[]
    for dlc in dlcdict.keys():
        if gid not in dlc_switch[dlc]:
            dlc_blacklist += dlcdict[dlc]
    for dlc in dlcdict2.keys():
        if gid not in dlc_switch[dlc]:
            dlc_blacklist += dlcdict2[dlc]
    return dlc_blacklist

#检查有没有没加到json里的dlc
def check_dlc():
    for dlc in dict(dlcdict, **dlcdict2).keys():
        if dlc not in dlc_switch.keys():
            dlc_switch[dlc]=[]
    save_dlc_switch()
            
check_dlc()






# noinspection SqlResolve
class RecordDAO:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS limiter"
                "(key TEXT NOT NULL, num INT NOT NULL, date INT, PRIMARY KEY(key))"
            )

    def exist_check(self, key):
        try:
            key = str(key)
            with self.connect() as conn:
                conn.execute("INSERT INTO limiter (key,num,date) VALUES (?, 0,-1)", (key,), )
            return
        except:
            return

    def get_num(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def clear_key(self, key):
        key = str(key)
        self.exist_check(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=0 WHERE key=?", (key,), )
        return

    def increment_key(self, key, num):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=num+? WHERE key=?", (num, key,))
        return

    def get_date(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT date FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def set_date(self, date, key):
        print(date)
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?", (date, key,), )
        return


db = RecordDAO(DB_PATH)


class DailyAmountLimiter(DailyNumberLimiter):
    def __init__(self, types, max_num, reset_hour):
        super().__init__(max_num)
        self.reset_hour = reset_hour
        self.type = types

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < self.max)

    def checks(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return db.get_num(key)

    def check10(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < 10)

    def get_num(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        return db.get_num(key)

    def increase(self, key, num=1):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.increment_key(key, num)

    def increase2(self, key, num):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.increment_key(key, num)

    def reset(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.clear_key(key)


daily_sign_limiter = DailyAmountLimiter("sign", SIGN_DAILY_LIMIT, RESET_HOUR)
daily_date_limiter = DailyAmountLimiter("date", DATE_DAILY_LIMIT, RESET_HOUR)
daily_gift_limiter = DailyAmountLimiter("gift", GIFT_DAILY_LIMIT, RESET_HOUR)
daily_duel_limiter = DailyAmountLimiter("duel", DUEL_DAILY_LIMIT, RESET_HOUR)
daily_Remake_limiter = DailyAmountLimiter("Remake", Remake_LIMIT, RESET_HOUR)
daily_GOLDTOSW_limiter = DailyAmountLimiter("sw", SW_DAILY_LIMIT, RESET_HOUR)
daily_GOLDTODUN_limiter = DailyAmountLimiter("goldToDun", G2DUN_LIMIT, RESET_HOUR)
daily_allowance_limiter = DailyAmountLimiter("allowance", ALLOWANCE_DAILY_LIMIT, RESET_HOUR)
daily_SHOP_limiter = DailyAmountLimiter("shop", SHOP_LIMIT, RESET_HOUR)
daily_dun_limiter = DailyAmountLimiter("dun", DUN_DAILY_LIMIT, RESET_HOUR)
daily_boss_limiter = DailyAmountLimiter("boss", BOSS_DAILY_LIMIT, RESET_HOUR)
daily_equip_limiter = DailyAmountLimiter("equip", EQUIP_DAILY_LIMIT, RESET_HOUR)
# 用于与赛跑金币互通
class ScoreCounter2:
    def __init__(self):
        os.makedirs(os.path.dirname(SCORE_DB_PATH), exist_ok=True)
        self._create_table()
        self._create_pres_table()
    def _connect(self):
        return sqlite3.connect(SCORE_DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SCORECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           SCORE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _add_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score + score))
            conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _reduce_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score - score))
                conn.commit()
            else:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, 0))
                conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _get_score(self, gid, uid):
        try:
            r = self._connect().execute("SELECT SCORE FROM SCORECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')

   # 判断金币是否足够下注
    def _judge_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                return 1
            else:
                return 0
        except Exception as e:
            raise Exception(str(e))

   #记录国王声望数据
    def _create_pres_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS PRESTIGECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           PRESTIGE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _set_prestige(self, gid, uid, prestige):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )

    def _get_prestige(self, gid, uid):
        try:
            r = self._connect().execute("SELECT PRESTIGE FROM PRESTIGECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return None if r is None else r[0]
        except:
            raise Exception('查找声望发生错误')

    def _add_prestige(self, gid, uid, num):
        prestige = self._get_prestige(gid, uid)
        prestige += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )

    def _reduce_prestige(self, gid, uid, num):
        prestige = self._get_prestige(gid, uid)
        prestige -= num
        prestige = max(prestige,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )





   
# 记录贵族相关数据

class DuelCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DUEL_DB_PATH), exist_ok=True)
        self._create_charatable()
        self._create_uidtable()
        self._create_leveltable()
        self._create_queentable()
        self._create_weapon()
        self._create_WLC()
        self._create_bantable()
        self._create_DayDuel()
        self._create_favortable()
        self._create_gifttable()
        self._create_SWITCH2()
        self._create_warehousetable()
    def _connect(self):
        return sqlite3.connect(DUEL_DB_PATH)

    def _create_charatable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS CHARATABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建角色表发生错误')

    def _create_uidtable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS UIDTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except:
            raise Exception('创建UID表发生错误')

    def _create_leveltable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS LEVELTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           LEVEL           INT    NOT NULL,
                           
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建UID表发生错误')

    def _get_card_owner(self, gid, cid):
        try:
            r = self._connect().execute("SELECT UID FROM CHARATABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找角色归属发生错误')

    def _set_card_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO CHARATABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_card_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM CHARATABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )


# 查询已被邀请的女友列表

    def _get_card_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM CHARATABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}

    def _get_level(self, gid, uid):
        try:
            r = self._connect().execute("SELECT LEVEL FROM LEVELTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找等级发生错误')

    def _get_cards(self, gid, uid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT CID, NUM FROM UIDTABLE WHERE GID=? AND UID=? AND NUM>0", (gid, uid)
            ).fetchall()
        return [c[0] for c in r] if r else {}

    def _get_card_num(self, gid, uid, cid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT NUM FROM UIDTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)
            ).fetchone()
            return r[0] if r else 0

    def _add_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        if cid !=9999:
            self._set_card_owner(gid, cid, uid)
            self._set_favor(gid,uid,cid,0)

    def _delete_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        self._delete_card_owner(gid, cid)
        self._delete_favor(gid,uid,cid)

    def _add_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _reduce_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _set_level(self, gid, uid, level):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )
    def _get_level_num(self, gid, level):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT COUNT(UID) FROM LEVELTABLE WHERE GID=? AND LEVEL=? ", (gid, level)
            ).fetchone()
            return r[0] if r else 0    



#皇后部分

    def _create_queentable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS QUEENTABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建皇后表发生错误')

    def _get_queen_owner(self, gid, cid):
        try:
            r = self._connect().execute("SELECT UID FROM QUEENTABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找皇后归属发生错误')

    def _set_queen_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO QUEENTABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_queen_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM QUEENTABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )
    def _get_queen_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM QUEENTABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}
#查询某人的皇后，无则返回0
    def _search_queen(self,gid,uid):
        try:
            r = self._connect().execute("SELECT CID FROM QUEENTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找皇后发生错误')
#购买女友上限部分（移植自上游0.7）
    def _create_warehousetable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WAREHOUSE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建仓库上限表发生错误')

    def _get_warehouse(self, gid, uid):
        try:
            r = self._connect().execute("SELECT NUM FROM WAREHOUSE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找上限发生错误')

    def _add_warehouse(self, gid, uid, num):
        housenum = self._get_warehouse(gid, uid)
        housenum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WAREHOUSE (GID, UID, NUM) VALUES (?, ?, ?)",
                (gid, uid, housenum),
            )
#好感度部分
    def _create_favortable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS FAVORTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           FAVOR           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except:
            raise Exception('创建好感表发生错误')


    def _set_favor(self, gid, uid, cid, favor):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _get_favor(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT FAVOR FROM FAVORTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找好感发生错误')

    def _add_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        if favor == None:
            favor = 0
        favor += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _reduce_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        favor -= num
        favor = max(favor,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _delete_favor(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM FAVORTABLE  WHERE GID=? AND UID=? AND CID=?",
                (gid, uid, cid),
            )
#礼物仓库部分

    def _create_gifttable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GIFTTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           GFID             INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, GFID));''')
        except:
            raise Exception('创建礼物表发生错误')

    def _get_gift_num(self, gid, uid, gfid):
        try:
            r = self._connect().execute("SELECT NUM FROM GIFTTABLE WHERE GID=? AND UID=? AND GFID=?", (gid, uid, gfid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找礼物发生错误')

    def _add_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        if giftnum == None:
            giftnum = 0
        giftnum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            )    

    def _reduce_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        giftnum -= num
        giftnum = max(giftnum,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            ) 
#群惩罚开关部分
    def _create_SWITCH2(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SWITCHCF
                          (GID             INT    NOT NULL,
                           NUM             INT    NULL,
                           PRIMARY KEY(GID));''')
        except:
            raise Exception('创建开关表发生错误')
            
    def _get_SWITCH2(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT NUM FROM SWITCHCF WHERE GID=?", (gid,)).fetchone()
            return 0 if r is None else r[0]
            
    def _set_SWITCH2(self, gid, num):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO SWITCHCF (GID, NUM) VALUES (?, ?)",
                (gid, num),
            )
#武器部分
    def _create_weapon(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WEAPON
                          (GID             INT    NOT NULL,
                           WEAPON           INT    NOT NULL,
                           PRIMARY KEY(GID));''')
        except:
            raise Exception('创建武器表发生错误')
            
    def _get_weapon(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT WEAPON FROM WEAPON WHERE GID=?", (gid,)).fetchone()
            return 6 if r is None else r[0]
    
    def _set_weapon(self, gid, weapon):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WEAPON (GID, WEAPON) VALUES (?, ?)",
                (gid, weapon),
            )
#封号部分
    def _create_bantable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS BANID
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           BANNUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建BAN表发生错误')
    
    def _get_BAN(self,gid,uid):
        with self._connect() as conn:
            r = conn.execute("SELECT BANNUM FROM BANID WHERE GID=? AND UID=?", (gid,uid)).fetchone()
            return 0 if r is None else r[0]
            
    def _reduce_BAN(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO BANID (GID, UID, BANNUM) VALUES (?, ?, ?)",
                (gid, uid, 0),
            )

    def _set_BAN(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO BANID (GID, UID, BANNUM) VALUES (?, ?, ?)",
                (gid, uid, 1),
            )
#胜负场部分
    def _create_WLC(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WLC
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           WIN             INT    NOT NULL,
                           LOST            INT    NOT NULL,
                           ADMIT           INT    NOT NULL,
                           PRIMARY KEY(GID,UID));''')
        except:
            raise Exception('创建胜负表发生错误')
            
    def _get_WLCWIN(self, gid, uid):
        try:
            r = self._connect().execute("SELECT WIN FROM WLC WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找胜场发生错误')
    
    def _get_WLCLOSE(self, gid, uid):
        try:
            r = self._connect().execute("SELECT LOST FROM WLC WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找负场发生错误')
    
    def _get_ADMIT(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ADMIT FROM WLC WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找认输场发生错误')
    
    def _add_Win(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, WIN+1, LOSE, ADMIT))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
            
    def _chat_Win(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, 999, LOSE, ADMIT))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
            
    def _add_Lose(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, WIN, LOSE+1, ADMIT))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
    
    def _add_ADMIT(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, WIN, LOSE, ADMIT+1))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
            
    def _WLC_Remake(self, gid, uid):
        try:
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, 0, 0, 0))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
            
#每日不决斗扣除女友部分
    def _get_gid_list(self):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT DISTINCT(GID) FROM LEVELTABLE").fetchall()
            return [g[0] for g in r] if r else {}
    
    def _get_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM LEVELTABLE WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')
            
    def _create_DayDuel(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS DAYDUEL
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           DALIY            INT    NOT NULL,
                           TOTAL           INT    NOT NULL,
                           PRIMARY KEY(GID,UID));''')
        except:
            raise Exception('创建每日决斗表发生错误')
            
    def _DALIY_add(self, gid, uid):
        try:
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO DAYDUEL (GID,UID,DALIY,TOTAL) \
                                VALUES (?,?,?,?)", (gid, uid, 1, 0))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
            
    def _get_DALIY(self, gid, uid):
        try:
            r = self._connect().execute("SELECT DALIY FROM DAYDUEL WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找决斗场次发生错误')
    
    def _get_TOTAL(self, gid, uid):
        try:
            r = self._connect().execute("SELECT TOTAL FROM DAYDUEL WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找未决斗天数发生错误')
            
    def _DALIY_SET(self, gid, uid):
        try:
            TOTAL = self._get_TOTAL(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO DAYDUEL (GID,UID,DALIY,TOTAL) \
                                VALUES (?,?,?,?)", (gid, uid, 0, TOTAL))
            conn.commit()
        except:
            raise Exception('更新表发生错误')
            
    def _TOTAL_ADD(self, gid, uid):
        try:
            TOTAL = self._get_TOTAL(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO DAYDUEL (GID,UID,DALIY,TOTAL) \
                                VALUES (?,?,?,?)", (gid, uid, 0, TOTAL + 1))
            conn.commit()
        except:
            raise Exception('更新表发生错误')




# 记录决斗和下注数据


class DuelJudger:
    def __init__(self):
        self.on = {}
        self.accept_on = {}
        self.support_on = {}
        self.fire_on = {}
        self.deadnum = {}
        self.support = {}
        self.turn = {}
        self.duelid = {}
        self.isaccept = {}
        self.hasfired_on = {}

    def set_support(self, gid):
        self.support[gid] = {}

    def get_support(self, gid):
        return self.support[gid] if self.support.get(gid) is not None else 0

    def add_support(self, gid, uid, id, score):
        self.support[gid][uid] = [id, score]

    def get_support_id(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][0]
        else:
            return 0

    def get_support_score(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][1]
        else:
            return 0

   # 五个开关：决斗，接受，下注， 开枪, 是否已经开枪

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def turn_on(self, gid):
        self.on[gid] = True

    def turn_off(self, gid):
        self.on[gid] = False

    def get_on_off_accept_status(self, gid):
        return self.accept_on[gid] if self.accept_on.get(gid) is not None else False

    def turn_on_accept(self, gid):
        self.accept_on[gid] = True

    def turn_off_accept(self, gid):
        self.accept_on[gid] = False

    def get_on_off_support_status(self, gid):
        return self.support_on[gid] if self.support_on.get(gid) is not None else False

    def turn_on_support(self, gid):
        self.support_on[gid] = True

    def turn_off_support(self, gid):
        self.support_on[gid] = False

    def get_on_off_fire_status(self, gid):
        return self.fire_on[gid] if self.fire_on.get(gid) is not None else False

    def turn_on_fire(self, gid):
        self.fire_on[gid] = True

    def turn_off_fire(self, gid):
        self.fire_on[gid] = False

    def get_on_off_hasfired_status(self, gid):
        return self.hasfired_on[gid] if self.hasfired_on.get(gid) is not None else False

    def turn_on_hasfired(self, gid):
        self.hasfired_on[gid] = True

    def turn_off_hasfired(self, gid):
        self.hasfired_on[gid] = False

   # 记录决斗者id
    def init_duelid(self, gid):
        self.duelid[gid] = []

    def set_duelid(self, gid, id1, id2):
        self.duelid[gid] = [id1, id2]

    def get_duelid(self, gid):
        return self.duelid[gid] if self.accept_on.get(gid) is not None else [0, 0]
        
   # 查询一个决斗者是1号还是2号
    def get_duelnum(self, gid, uid):
        return self.duelid[gid].index(uid) + 1

   # 记录由谁开枪
    def init_turn(self, gid):
        self.turn[gid] = 1

    def get_turn(self, gid):
        return self.turn[gid] if self.turn[gid] is not None else 0

    def change_turn(self, gid):
        if self.get_turn(gid) == 1:
            self.turn[gid] = 2
            return 2
        else:
            self.turn[gid] = 1
            return 1

   # 记录子弹位置
    def init_deadnum(self, gid):
        self.deadnum[gid] = None

    def set_deadnum(self, gid, num):
        self.deadnum[gid] = num

    def get_deadnum(self, gid):
        return self.deadnum[gid] if self.deadnum[gid] is not None else False

   # 记录是否接受
    def init_isaccept(self, gid):
        self.isaccept[gid] = False

    def on_isaccept(self, gid):
        self.isaccept[gid] = True

    def off_isaccept(self, gid):
        self.isaccept[gid] = False

    def get_isaccept(self, gid):
        return self.isaccept[gid] if self.isaccept[gid] is not None else False

class GiftChange:
    def __init__(self):    
        self.giftchange_on={}
        self.waitchange={}
        self.isaccept = {}
        self.changeid = {}

#礼物交换开关
    def get_on_off_giftchange_status(self, gid):
        return self.giftchange_on[gid] if self.giftchange_on.get(gid) is not None else False

    def turn_on_giftchange(self, gid):
        self.giftchange_on[gid] = True

    def turn_off_giftchange(self, gid):
        self.giftchange_on[gid] = False
   #礼物交换发起开关   
    def get_on_off_waitchange_status(self, gid):
        return self.waitchange[gid] if self.waitchange.get(gid) is not None else False

    def turn_on_waitchange(self, gid):
        self.waitchange[gid] = True

    def turn_off_waitchange(self, gid):
        self.waitchange[gid] = False
   #礼物交换是否接受开关
    def turn_on_accept_giftchange(self, gid):
        self.isaccept[gid] = True

    def turn_off_accept_giftchange(self, gid):
        self.isaccept[gid] = False

    def get_isaccept_giftchange(self, gid):
        return self.isaccept[gid] if self.isaccept[gid] is not None else False
   #记录礼物交换请求接收者id
    def init_changeid(self, gid):
        self.changeid[gid] = []

    def set_changeid(self, gid, id2):
        self.changeid[gid] = id2

    def get_changeid(self, gid):
        return self.changeid[gid] if self.changeid.get(gid) is not None else 0




duel_judger = DuelJudger()
gift_change = GiftChange()

class NvYouJiaoYi:
    def __init__(self):
        self.jiaoyion = {}
        self.jiaoyiflag = {}
        self.jiaoyiid = {}
        self.jiaoyiname = {}
        self.jiaoyi_on = {}
        
    def get_jiaoyi_on_off_status(self, gid):
        return self.jiaoyion[gid] if self.jiaoyion.get(gid) is not None else False
   # 记录群交易开关
    def turn_jiaoyion(self, gid):
        self.jiaoyion[gid] = True

    def turn_jiaoyioff(self, gid):
        self.jiaoyion[gid] = False
    
   # 记录群交易是否接受开关
    def turn_on_jiaoyi(self, gid):
        self.jiaoyi_on[gid] = True

    def turn_off_jiaoyi(self, gid):
        self.jiaoyi_on[gid] = False
    
   # 记录交易者id
    def init_jiaoyiid(self, gid):
        self.jiaoyiid[gid] = []

    def set_jiaoyiid(self, gid, id1, id2, cid):
        self.jiaoyiid[gid] = [id1, id2, cid]

    def get_jiaoyiid(self, gid):
        return self.jiaoyiid[gid] if self.jiaoyi_on.get(gid) is not None else [0, 0, 0]
   # 记录是否接受交易
    def init_jiaoyiflag(self, gid):
        self.jiaoyiflag[gid] = False

    def on_jiaoyiflag(self, gid):
        self.jiaoyiflag[gid] = True

    def off_jiaoyiflag(self, gid):
        self.jiaoyiflag[gid] = False

    def get_jiaoyiflag(self, gid):
        return self.jiaoyiflag[gid] if self.jiaoyiflag[gid] is not None else False
        
        
duel_jiaoyier = NvYouJiaoYi()


# 随机生成一个pcr角色id，应该已经被替代了。
def get_pcr_id():
    chara_id_list = list(_pcr_data_duel.CHARA_NAME.keys())
    while True:
        random.shuffle(chara_id_list)
        if chara_id_list[0] not in BLACKLIST_ID: break
    return chara_id_list[0]


# 生成没被约过的角色列表
def get_newgirl_list(gid):
    chara_id_list = list(_pcr_data_duel.CHARA_NAME.keys())
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
        "6": "国王",
        "7": "皇帝"
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

@sv.on_rex(f'^用(\d+)金币与(.*)交易女友(.*)$')
async def nobleduel(bot, ev: CQEvent):
    if duel_jiaoyier.get_jiaoyi_on_off_status(ev.group_id):
        await bot.send(ev, "此轮交易还没结束，请勿重复使用指令。")
        return
    gid = ev.group_id
    match = ev['match']
    try:
        id2 = int(match.group(2))
    except ValueError:
        id2 = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
        
    name = str(match.group(3))
    num = int(match.group(1))
    id1 = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    level2 = duel._get_level(gid, id2)
    if level2 == 0:
        await bot.send(ev, '对方未创建贵族哦，让ta发送[创建贵族]吧')
        return
    noblename = get_noblename(level2)
    is_overtime = 0
    num2 = 1000
    score = score_counter._get_score(gid, id1)
    prestige = score_counter._get_prestige(gid,id1)
    if score < num:
        msg = f'您的金币不足{num}，无法交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return
    if prestige == None:
        await bot.send(ev, f'您未开启声望系统，无法交易哦', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    elif prestige < num2:
        msg = f'您的声望不足{num2}，无法交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return         
    if id2 == id1:
        await bot.send(ev, "不能和自己交易！", at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return 
    if girl_outlimit(gid,id1):
        await bot.send(ev, "您的女友超过了爵位上限，无法进行交易哦！", at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return 
    
    if duel._get_level(gid, id1) == 0:
        msg = f'[CQ:at,qq={id1}]交易发起者还未在创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id1) == {}:
        msg = f'[CQ:at,qq={id1}]您没有女友，不能参与交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return

    if duel._get_level(gid, id2) == 0:
        msg = f'[CQ:at,qq={id2}]被交易者还未在本群创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id2) == {}:
        msg = f'[CQ:at,qq={id2}]您没有女友，不能参与交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
        
    if not name:
        await bot.send(ev, '请输入查女友+pcr角色名。', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    owner = duel._get_card_owner(gid, cid)
    c = chara.fromid(cid)
   #判断是否是妻子。
    if duel._get_queen_owner(gid,cid) !=0 :
        owner = duel._get_queen_owner(gid,cid)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的妻子，无法交易哦。', at_sender=True)

    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    if id2!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您需要与此人进行交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
    duel_jiaoyier.turn_jiaoyion(gid)
    duel_jiaoyier.init_jiaoyiflag(gid)
    duel_jiaoyier.set_jiaoyiid(gid, id1, id2, cid)
    duel_jiaoyier.turn_on_jiaoyi(gid)
    msg = f'[CQ:at,qq={id2}]尊敬的{noblename}您好\n[CQ:at,qq={id1}]试图以{num}金币的价格购买您的女友{c.name}，请在{WAIT_TIME_jy}秒内[接受交易/拒绝交易]，女友交易需要收10%手续费哦。'
    await bot.send(ev, msg)
    
    await asyncio.sleep(WAIT_TIME_jy)
    duel_jiaoyier.turn_off_jiaoyi(gid)
    if duel_jiaoyier.get_jiaoyiflag(gid) is False:
        msg = '交易被拒绝。'
        duel_jiaoyier.turn_jiaoyioff(gid)
        await bot.send(ev, msg, at_sender=True)
        return
        
    duel = DuelCounter()
    get_num=int(num*0.9)
    score_counter._add_score(gid, id2, get_num)
    score = score_counter._get_score(gid, id2)
    
    score_counter._reduce_score(gid, id1, num)
    scoreyou = score_counter._get_score(gid, id1)
    duel._delete_card(gid, id2, cid)
    duel._add_card(gid, id1, cid)
    duel_jiaoyier.turn_jiaoyioff(gid)
    mes = c.icon.cqcode
    score_counter._reduce_prestige(gid,id1,num2)
    msg = f'[CQ:at,qq={id1}]以{num}金币的价格购买了[CQ:at,qq={id2}]的女友{c.name}，交易成功\n[CQ:at,qq={id1}]您失去了{num}金币，{num2}声望，剩余{scoreyou}金币\n[CQ:at,qq={id2}]扣除10%手续费，您能得到了{get_num}金币，剩余{score}金币。{mes}'
    await bot.send(ev, msg)


@sv.on_fullmatch('接受交易')
async def duelaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_jiaoyier.get_jiaoyi_on_off_status(gid):
        if ev.user_id == duel_jiaoyier.get_jiaoyiid(gid)[1]:
            gid = ev.group_id
            msg = '交易接受成功，请耐心等待交易开始。'
            await bot.send(ev, msg, at_sender=True)
            duel_jiaoyier.turn_off_jiaoyi(gid)
            duel_jiaoyier.on_jiaoyiflag(gid)
        else:
            print('不是被交易者')
    else:
        print('现在不在交易期间')


@sv.on_fullmatch('重置交易')
async def init_duel(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置交易哦。', at_sender=True)
    duel_jiaoyier.turn_jiaoyioff(ev.group_id)
    msg = '已重置本群交易状态！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('拒绝交易')
async def duelrefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_jiaoyier.get_jiaoyi_on_off_status(gid):
        if ev.user_id == duel_jiaoyier.get_jiaoyiid(gid)[1]:
            gid = ev.group_id
            msg = '您已拒绝女友交易。'
            await bot.send(ev, msg, at_sender=True)
            duel_jiaoyier.turn_off_jiaoyi(gid)
            duel_jiaoyier.off_jiaoyiflag(gid)



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
    
   #根据爵位的每日固定收入
    level = duel._get_level(gid, uid)
    score2 = 50*level
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

async def get_user_card(bot, user_id):
    name = await bot.get_stranger_info(user_id=user_id)
    return name['nickname']

@sv.on_prefix(['查询贵族', '贵族查询', '我的贵族'])
async def inquire_noble(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    try:
        id = int(ev.message[0].data['qq'])
    except:
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
async def add_girl(bot, ev: CQEvent):
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
        score = score_counter._get_score(gid, uid)
        if score < GACHA_COST:
            msg = f'您的金币不足{GACHA_COST}哦。'
            await bot.send(ev, msg, at_sender=True)
            return
        newgirllist = get_newgirl_list(gid)
       # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                score_counter._reduce_score(gid, uid, GACHA_COST)
                cid = 9999
                c = chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        score_counter._reduce_score(gid, uid, GACHA_COST)

       # 招募女友失败
        if random.random() < 0.2:
            losetext = random.choice(Addgirlfail)
            msg = f'\n{losetext}\n您花费了{GACHA_COST}金币，但是没有约到新的女友。'
            await bot.send(ev, msg, at_sender=True)
            return

       # 招募女友成功
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

        
        msg = f'\n{wintext}\n招募女友成功！\n您花费了{GACHA_COST}金币\n新招募的女友为：{c.name}{mes}'

        await bot.send(ev, msg, at_sender=True)


@sv.on_fullmatch(['升级爵位', '升级贵族','贵族升级'])
async def add_girl(bot, ev: CQEvent):
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

    if level == 6:
        msg = f'您已经是国王了， 需要通过声望加冕称帝哦。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level == 7:
        msg = f'您是本群的皇帝， 已经无法提升等级了。'
        await bot.send(ev, msg, at_sender=True)
        return


    if cidnum < girlnum:
        msg = f'您的女友没满哦。\n需要达到{girlnum}名女友\n您现在有{cidnum}名。'
        await bot.send(ev, msg, at_sender=True)
        return
    needscore = get_noblescore(level + 1)
    futurename = get_noblename(level + 1)

    if score < needscore:
        msg = f'您的金币不足哦。\n升级到{futurename}需要{needscore}金币'
        await bot.send(ev, msg, at_sender=True)
        return
    score_counter._reduce_score(gid, uid, needscore)
    duel._add_level(gid, uid)
    newlevel = duel._get_level(gid, uid)
    newnoblename = get_noblename(newlevel)
    newgirlnum = get_girlnum_total(gid, uid)
    msg = f'花费了{needscore}金币\n您成功由{noblename}升到了{newnoblename}\n可以拥有{newgirlnum}名女友了哦。'
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
    if level < 6:
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


@sv.on_prefix('贵族决斗')
async def nobleduel(bot, ev: CQEvent):
    if ev.message[0].type == 'at':
        id2 = int(ev.message[0].data['qq'])
    else:
        await bot.finish(ev, '参数格式错误, 请重试')
    if duel_judger.get_on_off_status(ev.group_id):
        await bot.send(ev, "此轮决斗还没结束，请勿重复使用指令。")
        return
        
    gid = ev.group_id
    duel_judger.turn_on(gid)
    id1 = ev.user_id
    duel = DuelCounter()
    is_overtime = 0
    if id2 == id1:
        await bot.send(ev, "不能和自己决斗！", at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return 

    if duel._get_level(gid, id1) == 0:
        msg = f'[CQ:at,qq={id1}]决斗发起者还未在创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id1) == {}:
        msg = f'[CQ:at,qq={id1}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return

    if duel._get_level(gid, id2) == 0:
        msg = f'[CQ:at,qq={id2}]被决斗者还未在本群创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id2) == {}:
        msg = f'[CQ:at,qq={id2}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
   #判定每日上限
    guid = gid ,id1
    if not daily_duel_limiter.check(guid):
        await bot.send(ev, '今天的决斗次数已经超过上限了哦，明天再来吧。', at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return
    



   # 判定双方的女友是否已经超过上限

   # 这里设定大于才会提醒，就是可以超上限1名，可以自己改成大于等于。
    if girl_outlimit(gid,id1):
        msg = f'[CQ:at,qq={id1}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    if girl_outlimit(gid,id2):
        msg = f'[CQ:at,qq={id2}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    duel_judger.init_isaccept(gid)
    duel_judger.set_duelid(gid, id1, id2)
    duel_judger.turn_on_accept(gid)
    msg = f'[CQ:at,qq={id2}]对方向您发起了优雅的贵族决斗，请在{WAIT_TIME}秒内[接受/拒绝]。'

    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME)
    duel_judger.turn_off_accept(gid)
    if duel_judger.get_isaccept(gid) is False:
        msg = '决斗被拒绝。'
        duel_judger.turn_off(gid)
        await bot.send(ev, msg, at_sender=True)
        return
    daily_duel_limiter.increase(guid)
    duel = DuelCounter()
    level1 = duel._get_level(gid, id1)
    noblename1 = get_noblename(level1)
    level2 = duel._get_level(gid, id2)
    noblename2 = get_noblename(level2)
    id1Win = duel._get_WLCWIN(gid,id1)
    id2Win = duel._get_WLCWIN(gid,id2)
    id1Lose = duel._get_WLCLOSE(gid,id1)
    id2Lose = duel._get_WLCLOSE(gid,id2)
    n = duel._get_weapon(gid)
    if n == 6:
        msg = '''目前本群启用的武器是俄罗斯左轮，弹匣量为6\n'''
    elif n == 2:
        msg = '''目前本群启用的武器是贝雷塔687，弹匣量为2\n'''
    elif n == 20:
        msg = '''目前本群启用的武器是Glock，弹匣量为20\n'''
    elif n == 12:
        msg = '''目前本群启用的武器是战术型沙漠之鹰，弹匣量为12\n'''
    elif n == 10:
        msg = '''目前本群启用的武器是巴雷特，弹匣量为10\n'''
    else:
        msg = f'目前本群启用的是自定义武器，弹匣量为{n}\n'
    msg += f'''对方接受了决斗！    
1号：[CQ:at,qq={id1}]
爵位为：{noblename1}
胜负场：{id1Win}/{id1Lose}
2号：[CQ:at,qq={id2}]
爵位为：{noblename2}
胜负场：{id2Win}/{id2Lose}
其他人请在{DUEL_SUPPORT_TIME}秒选择支持的对象。
[支持1/2号xxx金币]
[梭哈1/2号]'''

    await bot.send(ev, msg)
    duel_judger.turn_on_support(gid)
    await asyncio.sleep(DUEL_SUPPORT_TIME)
    duel_judger.turn_off_support(gid)
    x = duel._get_weapon(gid)
    deadnum = random.randint(1,x)
    duel_judger.set_deadnum(gid, deadnum)
    duel_judger.init_turn(gid)
    duel_judger.turn_on_fire(gid)
    duel_judger.turn_off_hasfired(gid)
    msg = f'支持环节结束，下面请决斗双方轮流[开枪]。\n[CQ:at,qq={id1}]先开枪，30秒未开枪自动认输'

    await bot.send(ev, msg)
    n = 1
    while (n <= duel._get_weapon(gid)):
        wait_n = 0
        while (wait_n < 30):
            if duel_judger.get_on_off_hasfired_status(gid):
                break

            wait_n += 1
            await asyncio.sleep(1)
        if wait_n >= 30:
           # 超时未开枪的胜负判定
            loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
            winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
            msg = f'[CQ:at,qq={loser}]\n你明智的选择了认输。'
            await bot.send(ev, msg)
            
           #记录本局为超时局。
            is_overtime = 1
            
            
            break
        else:
            if n == duel_judger.get_deadnum(gid):
               # 被子弹打到的胜负判定
                loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={loser}]\n砰！你死了。'
                await bot.send(ev, msg)
                break
            else:
                id = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                id2 = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={id}]\n砰！松了一口气，你并没有死。\n[CQ:at,qq={id2}]\n轮到你开枪了哦。'
                await bot.send(ev, msg)
                n += 1
                duel_judger.change_turn(gid)
                duel_judger.turn_off_hasfired(gid)
                duel_judger.turn_on_fire(gid)
    score_counter = ScoreCounter2()
    cidlist = duel._get_cards(gid, loser)
    selected_girl = random.choice(cidlist)
    queen = duel._search_queen(gid,loser)

    CE = CECounter()
    bangdinwin = CE._get_guaji(gid,winner)
    bangdinlose = CE._get_guaji(gid,loser)
    #判断决斗胜利者是否有绑定角色,有则增加经验值
    bd_msg=''
    if bangdinwin:
        bd_info = chara.fromid(bangdinwin)
        card_level=add_exp(gid,winner,bangdinwin,WIN_EXP)
        nvmes = bd_info.icon.cqcode
        bd_msg = f"\n您绑定的女友{bd_info.name}获得了{WIN_EXP}点经验，{card_level[2]}\n{nvmes}"
        
   #判定被输掉的是否是复制人可可萝，是则换成金币。
    if selected_girl==9999:
        score_counter._add_score(gid, winner, 300)
        c = chara.fromid(1059)
        duel._delete_card(gid, loser, selected_girl)
        msg = f'[CQ:at,qq={winner}]\n您赢得了神秘的可可萝，但是她微笑着消失了。\n本次决斗获得了300金币。'
        await bot.send(ev, msg)
        msg = f'[CQ:at,qq={loser}]\n您输掉了贵族决斗，被抢走了女友\n{c.name}，\n只要招募，她就还会来到你的身边哦。{c.icon.cqcode}'
        msg += '\n获得了安慰金50金币。'
        score_counter._add_score(gid, loser, 50)
        await bot.send(ev, msg)

   #判断被输掉的是否为皇后。    
    elif selected_girl==queen:
        score_counter._add_score(gid, winner, 300)
        msg = f'[CQ:at,qq={winner}]您赢得的角色为对方的皇后，\n您改为获得300金币。'
        await bot.send(ev, msg)
        score_counter._reduce_prestige(gid,loser,500)
        msg = f'[CQ:at,qq={loser}]您差点输掉了皇后，失去了500声望。'
        msg += '\n获得了安慰金50金币。'
        score_counter._add_score(gid, loser, 50)
        await bot.send(ev, msg)


    elif girl_outlimit(gid,winner):
        score_counter._add_score(gid, winner, 300)
        msg = f'[CQ:at,qq={winner}]您的女友超过了爵位上限，\n本次决斗获得了300金币。'
        c = chara.fromid(selected_girl)
       #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)
        if favor>=favor_reduce_NEED:
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了{favor_reduce}点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)            
        else:
            duel._delete_card(gid, loser, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗且对方超过了爵位上限，您的女友恢复了单身。\n{c.name}{c.icon.cqcode}'
            msg += '\n获得了安慰金50金币。'
            score_counter._add_score(gid, loser, 50)
            await bot.send(ev, msg)

    else:
        c = chara.fromid(selected_girl)
       #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)    
        if favor>=favor_reduce_NEED:
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了{favor_reduce}点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)      
            score_counter._add_score(gid, winner, 300)
            msg = f'[CQ:at,qq={winner}]您赢得了决斗，对方女友仍有一定好感。\n本次决斗获得了300金币。'
            await bot.send(ev, msg)  
        else:
            duel._delete_card(gid, loser, selected_girl)
            duel._add_card(gid, winner, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您被抢走了女友\n{c.name}{c.icon.cqcode}'
            msg += '\n获得了安慰金50金币。'
            score_counter._add_score(gid, loser, 50)
            await bot.send(ev, msg)
       #判断赢家的角色列表里是否有复制人可可萝。
        wincidlist = duel._get_cards(gid, winner)
        if 9999 in wincidlist:
            duel._delete_card(gid, winner, 9999)
            score_counter._add_score(gid, winner, 300)
            msg = f'[CQ:at,qq={winner}]\n“主人有了女友已经不再孤单了，我暂时离开了哦。”\n您赢得了{c.name},可可萝微笑着消失了。\n您获得了300金币。'
            await bot.send(ev, msg)
   #判断胜者败者是否需要增减声望
    winprestige = score_counter._get_prestige(gid,winner)
    if winprestige != None:
        if is_overtime == 1:
            score_counter._add_prestige(gid,winner,1)
            await bot.send(ev, f"[CQ:at,qq={winner}]本局为超时局，您的声望上升了1点。")
        else:
            score_counter._add_prestige(gid,winner,200)
            msg = f'[CQ:at,qq={winner}]决斗胜利使您的声望上升了200点。'
            await bot.send(ev, msg)
    loseprestige = score_counter._get_prestige(gid,loser)
    if loseprestige != None:
        score_counter._reduce_prestige(gid,loser,100)
        msg = f'[CQ:at,qq={loser}]决斗失败使您的声望下降了100点。'
        await bot.send(ev, msg)
    if bd_msg:
        await bot.send(ev, f'[CQ:at,qq={winner}]{bd_msg}')

   #判定败者是否掉爵位，皇帝不会因为决斗掉爵位。
    level_loser = duel._get_level(gid, loser)
    if level_loser > 1 and level_loser!=7:
        noblename_loser = get_noblename(level_loser)
        girlnum_loser = get_girlnum(level_loser - 1)
        cidlist_loser = duel._get_cards(gid, loser)
        cidnum_loser = len(cidlist_loser)
        if cidnum_loser < girlnum_loser:
            duel._reduce_level(gid, loser)
            reward = int(get_noblescore(level_loser)/2)
            score_counter._add_score(gid, loser, reward)
            new_noblename = get_noblename(level_loser - 1)
            msg = f'[CQ:at,qq={loser}]\n您的女友数为{cidnum_loser}名\n小于爵位需要的女友数{girlnum_loser}名\n您的爵位下降到了{new_noblename}\n获得掉段补偿金{reward}'
            await bot.send(ev, msg)
    duel._add_Lose(gid,loser)
   #结算下注金币，判定是否为超时局。
    if is_overtime == 1 and n !=duel._get_weapon(gid):
        msg = '本局为超时局，记为认输，不进行金币结算，支持的金币全部返还。'
        await bot.send(ev, msg)
        duel._add_ADMIT(gid,loser)
        duel_judger.set_support(ev.group_id)
        duel_judger.turn_off(ev.group_id)
        return
    
    support = duel_judger.get_support(gid)
    duel._add_Win(gid,winner)
    duel._DALIY_add(gid,loser)
    duel._DALIY_add(gid,winner)

    winuid = []
    supportmsg = '金币结算:\n'
    winmsg = get_noblename(level_loser)
    win_reward = level_loser*40+random.randint(0,20)
    score_counter._add_score(gid, winner, win_reward)
    supportmsg += f'(决斗 {winmsg} 获胜)[CQ:at,qq={winner}]+{win_reward}金币\n'
    winnum = duel_judger.get_duelnum(gid, winner)

    if support != 0:
        for uid in support:
            support_id = support[uid][0]
            support_score = support[uid][1]
            if support_id == winnum:
                winuid.append(uid)
               #这里是赢家获得的金币结算，可以自己修改倍率。
                winscore = support_score*WIN_NUM 
                score_counter._add_score(gid, uid, winscore)
                supportmsg += f'[CQ:at,qq={uid}]+{winscore}金币\n'
            else:
                score_counter._reduce_score(gid, uid, support_score)
                supportmsg += f'[CQ:at,qq={uid}]-{support_score}金币\n'
    await bot.send(ev, supportmsg)
    duel_judger.set_support(ev.group_id)
    duel_judger.turn_off(ev.group_id)
    return


@sv.on_fullmatch('接受')
async def duelaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '贵族决斗接受成功，请耐心等待决斗开始。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.on_isaccept(gid)
        else:
            print('不是被决斗者')
    else:
        print('现在不在决斗期间')


@sv.on_fullmatch('拒绝')
async def duelrefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '您已拒绝贵族决斗。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.off_isaccept(gid)


@sv.on_fullmatch('开枪')
async def duelfire(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_fire_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]:
            duel_judger.turn_on_hasfired(gid)
            duel_judger.turn_off_fire(gid)


@sv.on_rex(r'^支持(1|2)号(\d+)(金币|币)$')
async def on_input_duel_score(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            uid = ev.user_id

            match = ev['match']
            select_id = int(match.group(1))
            input_score = int(match.group(2))
            print(select_id, input_score)
            score_counter = ScoreCounter2()
           # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
           # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
           # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return

               # 检查金币是否足够下注
            if score_counter._judge_score(gid, uid, input_score) == 0:
                msg = '您的金币不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'支持{select_id}号成功。'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_rex(r'^梭哈(1|2)号$')
async def on_input_duel_score2(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            duel = DuelCounter()
            uid = ev.user_id
            score_counter = ScoreCounter2()
            match = ev['match']
            select_id = int(match.group(1))
            current_score = score_counter._get_score(gid, uid)
            input_score = current_score
            score_counter = ScoreCounter2()
           # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
           # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
           # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return
               # 检查金币是否足够下注
            if current_score == 0:
                msg = '您的金币为0，不能梭哈。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
                input_score =  int(1.5*current_score)
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'梭哈{select_id}号{current_score}金币成功，胜利时，将获得相对于平常值1.5倍的金币！'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

# 以下部分与赛跑的重合，有一个即可，两个插件都装建议注释掉。

@sv.on_prefix(['领金币', '领取金币'])
async def add_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id
        guid = gid,uid
        if not daily_allowance_limiter.check(guid):
            await bot.send(ev, '您今天已领取过10次了，明天才能领取哦', at_sender=True)
            return
        current_score = score_counter._get_score(gid, uid)
        if current_score == 0:
            score_counter._add_score(gid, uid, ZERO_GET_AMOUNT)
            daily_allowance_limiter.increase(guid)
            msg = f'您已领取{ZERO_GET_AMOUNT}金币'
            await bot.send(ev, msg, at_sender=True)
            return
        else:
            msg = '金币为0才能领取哦。'
            await bot.send(ev, msg, at_sender=True)
            return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_prefix(['查金币', '查询金币', '查看金币'])
async def get_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id

        current_score = score_counter._get_score(gid, uid)
        msg = f'您的金币为{current_score}'
        await bot.send(ev, msg, at_sender=True)
        return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_rex(f'^为(.*)充值(\d+)金币$')
async def cheat_score(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '只有机器人管理才能使用氪金功能哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    score_counter._add_score(gid, id, num)
    score = score_counter._get_score(gid, id)
    msg = f'已为[CQ:at,qq={id}]充值{num}金币。\n现在共有{score}金币。'
    await bot.send(ev, msg)


@sv.on_fullmatch('重置决斗')
async def init_duel(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置决斗哦。', at_sender=True)
    duel_judger.turn_off(ev.group_id)
    duel_judger.set_support(ev.group_id)
    msg = '已重置本群决斗状态！'
    await bot.send(ev, msg, at_sender=True)


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
    print(duel._get_queen_owner(gid,cid))
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
    namelist = _pcr_data_duel.CHARA_NAME[cid]
    namemsg = ''
    for name in namelist:
        namemsg += f'{name},'
    namemsg = namemsg[:-1]
    msg = f'\n您的第{num_int}名女友的昵称为:\n\n{namemsg}'
    await bot.send(ev, msg, at_sender=True)


#重置某一用户的金币，只用做必要时删库用。
@sv.on_prefix('重置金币')
async def reset_score(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置金币功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置金币+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, id,current_score)
        await bot.finish(ev, f'已清空用户{id}的金币。', at_sender=True)
        
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
成为国王后才可以开启声望系统
开启后可以通过决斗等方式获取声望
声望系统相关指令如下
1. 开启声望系统
2. 查询声望
3. 加冕仪式(需要10000声望，5000金币）
4. 皇室婚礼+角色名(需3000声望，3000金币)
5. 用金币兑换声望

决斗胜利+200声望
决斗失败-100声望
皇室婚礼需皇帝才能举办
每位皇帝只能举办一次
皇后不会因决斗被抢走

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
    if level!=6:
        await bot.finish(ev, '只有国王才能进行加冕仪式哦。', at_sender=True)
  
    if prestige < 10000: 
        await bot.finish(ev, '加冕仪式需要10000声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 5000:
        await bot.finish(ev, '加冕仪式需要5000金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid,uid,5000)
    score_counter._reduce_prestige(gid,uid,10000)
    duel._set_level(gid, uid, 7)
    msg = '\n礼炮鸣响，教皇领唱“感恩赞美歌”。“皇帝万岁！”\n在民众的欢呼声中，你加冕为了皇帝。\n花费了10000点声望，5000金币。'
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
    if level != 7:
        await bot.finish(ev, '只有皇帝才可以举办皇室婚礼哦。', at_sender=True)  
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

#返回好感对应的关系和文本
def get_relationship(favor):
    for relation in RELATIONSHIP_DICT.keys():
        if favor >= relation:
            relationship = RELATIONSHIP_DICT[relation]
    return relationship[0],relationship[1]



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
    if not daily_date_limiter.check(guid):
        await bot.finish(ev, '今天已经和女友约会过了哦，明天再来吧。', at_sender=True)

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
    duel._add_favor(gid,uid,cid,favor)
    c = chara.fromid(cid)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    msg = f'\n\n{text}\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    daily_date_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)

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

@sv.on_prefix(['送礼物','送礼','赠送礼物'])
async def give_gift(bot, ev: CQEvent):
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
    duel._reduce_gift(gid,uid,gfid)
    favor,text = check_gift(cid,gfid)
    duel._add_favor(gid,uid,cid,favor)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    c = chara.fromid(cid)
    msg = f'\n{c.name}:“{text}”\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)    

@sv.on_fullmatch(['抽礼物','买礼物','购买礼物'])
async def buy_gift(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    guid = gid ,uid
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买礼物吧。'
        await bot.finish(ev, msg, at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 300:
        await bot.finish(ev, '购买礼物需要300金币，您的金币不足哦。', at_sender=True) 
    if not daily_gift_limiter.check(guid):
        await bot.finish(ev, f'今天购买礼物已经超过{GIFT_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)     
    select_gift = random.choice(list(GIFT_DICT.keys()))
    gfid = GIFT_DICT[select_gift]
    while(gfid == 10):
        select_gift = random.choice(list(GIFT_DICT.keys()))
        gfid = GIFT_DICT[select_gift]
    duel._add_gift(gid,uid,gfid)
    msg = f'\n您花费了300金币，\n买到了[{select_gift}]哦，\n欢迎下次惠顾。'
    score_counter._reduce_score(gid,uid,300)
    daily_gift_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)    

@sv.on_rex(r'^买(\d+)(个|份)礼物$')
async def buy_gift(bot, ev: CQEvent):
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
    score = score_counter._get_score(gid, uid)
    if score < 300 * num:
        await bot.finish(ev, f'购买{num}份礼物需要{300*num}金币，您的金币不足哦。', at_sender=True) 
    if num > (GIFT_DAILY_LIMIT - daily_gift_limiter.checks(guid)):
        await bot.finish(ev, f'今天购买礼物的次数不足哦，您还可以购买{GIFT_DAILY_LIMIT - daily_gift_limiter.checks(guid)}次。', at_sender=True)
    n = num
    giftmsg = ''
    while(n):
        select_gift = random.choice(list(GIFT_DICT.keys()))
        gfid = GIFT_DICT[select_gift]
        while(gfid == 10):
            select_gift = random.choice(list(GIFT_DICT.keys()))
            gfid = GIFT_DICT[select_gift]
        giftmsg += f'{select_gift} '
        duel._add_gift(gid,uid,gfid)
        n -= 1
    msg = f'\n您花费了{300*num}金币，\n买到了[{giftmsg}]哦，\n欢迎下次惠顾。'
    score_counter._reduce_score(gid,uid,300*num)
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
    except:
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
async def buy_information(bot, ev: CQEvent):
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

@sv.on_fullmatch('用金币兑换声望')
async def cheat_intro(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    score_counter = ScoreCounter2()
    msg = '用法：[用x金币兑换声望]\n请注意：请不要输入非等倍的数字，不会找还零钱！随着本群贵族的总金币数增加，兑换比例也会增加！\n'
    user_card_dict = await get_user_card_dict(bot, gid)
    total_score = 0
    for uid in user_card_dict.keys():
        if uid != ev.self_id:
            total_score += score_counter._get_score(gid, uid)
    msg += f'当前所有人有金币{total_score}个，'
    if total_score < 20000:
        ritsu = 10
    elif total_score < 100000:
        up = int(str(total_score)[:1])
        ritsu = 10+up
    else:
        ritsu = 20
    msg += f'当前的金币:声望为{ritsu}:1。'
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^用(\d+)金币兑换声望$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    num = int(match.group(1))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    guid = gid, uid
    prestige = score_counter._get_prestige(gid,uid)   
    if num > SW_DAILY_LIMIT - daily_GOLDTOSW_limiter.checks(guid) :
        await bot.finish(ev, f'超出兑换最大限额！您今天还剩{SW_DAILY_LIMIT - daily_GOLDTOSW_limiter.checks(guid)}金币可以兑换！', at_sender=True) 
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还没有在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '您未开启声望系统哦！。', at_sender=True)   
    score = score_counter._get_score(gid, uid)
    pay_score=num
    user_card_dict = await get_user_card_dict(bot, gid)
    total_score = 0
    for uid in user_card_dict.keys():
        if uid != ev.self_id:
            total_score += score_counter._get_score(gid, uid)
    if total_score < 20000:
        ritsu = 10
        num2 = int(pay_score/ritsu)
    elif total_score < 100000:
        up = int(str(total_score)[:1])
        ritsu = 10+up
        num2 = int(pay_score/ritsu)
    else:
        ritsu = 20
        num2 = int(pay_score/ritsu)
    if pay_score > score:
        msg = f'您的金币只有{score}，无法兑换哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        uid = ev.user_id
        score_counter._reduce_score(gid, uid, pay_score)
        score_counter._add_prestige(gid,uid,num2)
        scoreyou = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        daily_GOLDTOSW_limiter.increase2(guid,num)
        msg = f'使用{num}金币兑换{num2}声望成功\n您的声望为{prestige}，金币剩余{scoreyou}。'
        await bot.send(ev, msg, at_sender=True)
   
@sv.on_rex(f'^为(.*)转账(\d+)金币$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if num < Zhuan_Low_LIMIT :
        await bot.finish(ev, f'低于转账最小限额！最少转出{Zhuan_Low_LIMIT}', at_sender=True)
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < num:
        msg = f'您的金币不足{num}哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._add_score(gid, id, num)
        score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, uid, num)
        scoreyou = score_counter._get_score(gid, uid)
        msg = f'已为[CQ:at,qq={id}]转账{num}金币。\n您的金币剩余{scoreyou}金币，对方金币剩余{score}金币。'
        await bot.send(ev, msg)

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d        

@sv.on_fullmatch(('声望排行榜', '声望排行'))
async def SW_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_prestige(gid, uid)
                if score_dict[user_card_dict[uid]] == None:
                   score_dict[user_card_dict[uid]] = 0
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决声望排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 声望: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))      

@sv.on_fullmatch(('胜场排行榜', '贵族胜场排行'))
async def SC_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        duel = DuelCounter() 
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = duel._get_WLCWIN(gid, uid)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 累计胜场: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))  

@sv.on_fullmatch(('女友排行榜', '女友排行'))
async def SW_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        duel = DuelCounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                cidlist = duel._get_cards(gid, uid)
                score_dict[user_card_dict[uid]] = cidnum = len(cidlist)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决女友数排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 女友数: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))     

@sv.on_fullmatch('开启本群不决斗惩罚')
async def ON_SWITCH2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您的权限不足！', at_sender=True)
    duel = DuelCounter()
    duel._set_SWITCH2(gid,1)
    await bot.finish(ev, '开启成功！', at_sender=True)

@sv.on_fullmatch('关闭本群不决斗惩罚')
async def OFF_SWITCH2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您的权限不足！', at_sender=True)
    duel = DuelCounter()
    duel._set_SWITCH2(gid,0)
    await bot.finish(ev, '关闭成功！', at_sender=True)

@sv.on_fullmatch('查询本群不决斗惩罚')
async def search_SWITCH2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    msg = '[开启本群不决斗惩罚]\n[关闭本群不决斗惩罚]\n开启后，每天5点当检测到本群贵族连续两天未决斗，将会发生女友跑路事件！\n'
    if duel._get_SWITCH2(gid) ==0:
        msg += '❗目前本群不决斗惩罚处于关闭状态！'
        await bot.finish(ev, msg, at_sender=True)
    else:
        msg += '❗目前本群不决斗惩罚处于开启状态！'
        await bot.finish(ev, msg, at_sender=True)
    
@sv.on_fullmatch('重置礼物交换')
async def init_change(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置礼物交换哦。', at_sender=True)
    gift_change.turn_off_giftchange(ev.group_id)
    msg = '已重置本群礼物交换状态！'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('武器列表')
async def weapon(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    n = duel._get_weapon(gid)
    if n == 6:
        msg = '''目前本群启用的武器是俄罗斯左轮，弹匣量为6'''
    elif n == 2:
        msg = '''目前本群启用的武器是贝雷塔687，弹匣量为2'''
    elif n == 20:
        msg = '''目前本群启用的武器是Glock，弹匣量为20'''
    elif n == 12:
        msg = '''目前本群启用的武器是战术型沙漠之鹰，弹匣量为12'''
    elif n == 10:
        msg = '''目前本群启用的武器是巴雷特，弹匣量为10'''
    else:
        msg = f'目前本群启用的是自定义武器，弹匣量为{n}'
    msg += '''
    [切换武器+武器名]
    可用的武器有
    1.俄罗斯左轮 6发 
    2.贝雷塔687  2发
    3.格洛克   20发
    4.战术型沙漠之鹰 12发
    5.巴雷特 10发
也可发送自定义武器装弹X发来定制自己的武器'''
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_rex(r'^切换武器(俄罗斯左轮|贝雷塔687|格洛克|战术型沙漠之鹰|巴雷特)$')
async def weaponchange(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = (ev['match'])
    weapon = (match.group(1))
    duel = DuelCounter()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，无法切换武器。'
        await bot.send(ev, msg, at_sender=True)
        return   
    if weapon == '俄罗斯左轮':
        msg = '已启用武器俄罗斯左轮，弹匣量为6'
        duel._set_weapon(gid,6)
    if weapon == '贝雷塔687':
        msg = '已启用武器贝雷塔687，弹匣量为2'
        duel._set_weapon(gid,2)
    if weapon == '格洛克':
        msg = '已启用武器格洛克，弹匣量为20'
        duel._set_weapon(gid,20)
    if weapon == '战术型沙漠之鹰':
        msg = '已启用武器战术型沙漠之鹰，弹匣量为12'
        duel._set_weapon(gid,12)
    if weapon == '巴雷特':
        msg = '已启用武器巴雷特，弹匣量为10'
        duel._set_weapon(gid,10)
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex(f'^自定义武器装弹(\d+)发$')
async def weaponchange2(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = (ev['match'])
    n = int(match.group(1))
    duel = DuelCounter()
    if n > 50:
        msg = '禁止浪费子弹'
        await bot.send(ev ,msg)
        return
    if n % 2 != 0:
        msg = '子弹数量必须是2的倍数喔！'
        await bot.send(ev, msg, at_sender=True)
        return 
    if n == 0:
        msg = '子弹数不能为0！'
        await bot.send(ev, msg, at_sender=True)
        return 
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，无法切换武器。'
        await bot.send(ev, msg, at_sender=True)
        return   
    duel._set_weapon(gid,n)
    msg = f'已启用自定义武器，弹匣量为{n}'
    await bot.send(ev, msg, at_sender=True)

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

@sv.on_fullmatch(['神秘商店','今日商店'])
async def buy_information(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来看看吧。'
        await bot.finish(ev, msg, at_sender=True)    
    nows = datetime.now(pytz.timezone('Asia/Shanghai'))
    month = nows.month
    day = nows.day
    hour = nows.hour
    seed = gid+uid+hour+day+month
    print(seed)
    random.seed(seed)
    num1 = random.randint(0,2)
    num2 = random.randint(3,5)
    num3 = random.randint(6,8)
    num4 = random.randint(9,10)
    num5 = random.randint(5,10)
    msg = f'现在神秘商店在出售这些物品\n'
    for gift in GIFT_DICT.keys():
        random.seed(seed)
        if GIFT_DICT[gift] == num1:
            shop1 = gift
            needgold = random.randint(1,10)*200
            msg += f'1：{shop1} {needgold}金币\n'
            num1 = -1
            continue
        if GIFT_DICT[gift] == num2:
            shop2 = gift
            needgold = random.randint(2,10)*200
            msg += f'2：{shop2} {needgold}金币\n'
            num2 = -1
            continue
        if GIFT_DICT[gift] == num3:
            shop3 = gift
            needgold = random.randint(3,10)*200
            msg += f'3：{shop3} {needgold}金币\n'
            num3 = -1
            continue
        if GIFT_DICT[gift] == num4:
            shop4 = gift
            if num4 <10:
                needgold = random.randint(4,10)*200
                msg += f'4：{shop4} {needgold}金币\n'
            else:
                needgold = random.randint(4,10)*400
                msg += f'4：{shop4} {needgold}金币\n'
            num4 = -1
            continue
        if GIFT_DICT[gift] == num5:
            shop5 = gift
            needgold = 1000+random.randint(5,10)*200
            msg += f'5：{shop5} {needgold}金币\n'
            num5 = -1
            continue
    msg += f'发送购买物品+物品编号来购买，神秘商店每小时刷新！每人每天限购{SHOP_LIMIT}次哦\n注意：每个人的商店内容不同哦！\n'
    await bot.send(ev, msg, at_sender=True)  
     
@sv.on_prefix(['购买物品'])
async def Shop(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    guid = gid,uid
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    score = score_counter._get_score(gid, uid)
    if not daily_SHOP_limiter.check(guid):
        await bot.finish(ev, '您今日购买神秘商店商品的次数已达上限喔，明天再来吧！', at_sender=True)
    nows = datetime.now(pytz.timezone('Asia/Shanghai'))
    month = nows.month
    day = nows.day
    hour = nows.hour
    seed = gid+uid+hour+day+month
    print(seed)
    random.seed(seed)
    num1 = random.randint(0,2)
    num2 = random.randint(3,5)
    num3 = random.randint(6,8)
    num4 = random.randint(9,10)
    num5 = random.randint(5,10)
    if not args:
        await bot.finish(ev, '请输入 购买物品+物品编号 中间用空格隔开。', at_sender=True)
    if len(args)!=1:
        await bot.finish(ev, '请输入 购买物品+物品编号 中间用空格隔开。', at_sender=True)
    shopid = int(args[0])
    if shopid > 5 or shopid <=0:
        await bot.finish(ev, '请输入正确的物品编号。', at_sender=True)
    if shopid == 5 and num5 < 10:
        await bot.finish(ev, '请输入正确的物品编号。', at_sender=True)    
    for gift in GIFT_DICT.keys():
        if GIFT_DICT[gift] == num1:
            shop1 = gift
            num1 = -1
            continue
        if GIFT_DICT[gift] == num2:
            shop2 = gift
            num2 = -1
            continue
        if GIFT_DICT[gift] == num3:
            shop3 = gift
            num3 = -1
            continue
        if GIFT_DICT[gift] == num4:
            shop4 = gift
            num4 = -1
            continue
        if GIFT_DICT[gift] == num5:
            shop5 = gift
            num5 = -1
            continue
    random.seed(seed)
    if shopid == 1:
        needgold = random.randint(1,10)*200
        if score < needgold:
            await bot.finish(ev, f'购买需要{needgold}金币，您的金币不足哦。', at_sender=True)
        gfid = GIFT_DICT[shop1]
        score_counter._reduce_score(gid,uid,needgold)
        duel._add_gift(gid,uid,gfid)
        daily_SHOP_limiter.increase(guid)
        await bot.finish(ev, f'成功购买了{shop1},花费了{needgold}金币。', at_sender=True) 
    if shopid == 2:
        needgold = random.randint(2,10)*200
        if score < needgold:
            await bot.finish(ev, f'购买需要{needgold}金币，您的金币不足哦。', at_sender=True) 
        gfid = GIFT_DICT[shop2]
        duel._add_gift(gid,uid,gfid)
        daily_SHOP_limiter.increase(guid)
        score_counter._reduce_score(gid,uid,needgold)
        await bot.finish(ev, f'成功购买了{shop2},花费了{needgold}金币。', at_sender=True) 
    if shopid == 3:
        needgold = random.randint(3,10)*200
        if score < needgold:
            await bot.finish(ev, f'购买需要{needgold}金币，您的金币不足哦。', at_sender=True) 
        gfid = GIFT_DICT[shop3]
        duel._add_gift(gid,uid,gfid)
        daily_SHOP_limiter.increase(guid)
        score_counter._reduce_score(gid,uid,needgold)
        await bot.finish(ev, f'成功购买了{shop3},花费了{needgold}金币。', at_sender=True) 
    if shopid == 4:
        gfid = GIFT_DICT[shop4]
        if gfid < 10:
            needgold = random.randint(4,10)*200
        else:
            needgold = random.randint(4,10)*400
        if score < needgold:
            await bot.finish(ev, f'购买需要{needgold}金币，您的金币不足哦。', at_sender=True) 
         
        duel._add_gift(gid,uid,gfid)
        daily_SHOP_limiter.increase(guid)
        score_counter._reduce_score(gid,uid,needgold)
        await bot.finish(ev, f'成功购买了{shop4},花费了{needgold}金币。', at_sender=True) 
    if shopid == 5:
        needgold = 1000+random.randint(5,10)*200
        if score < needgold:
            await bot.finish(ev, f'购买需要{needgold}金币，您的金币不足哦。', at_sender=True) 
        gfid = GIFT_DICT[shop5]
        duel._add_gift(gid,uid,gfid)
        daily_SHOP_limiter.increase(guid)
        score_counter._reduce_score(gid,uid,needgold)
        await bot.finish(ev, f'成功购买了{shop5},花费了{needgold}金币。', at_sender=True)    
 
@sv.on_prefix(['批量送礼'])
async def give_gift(bot, ev: CQEvent):
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
    x = num
    favor,text = check_gift(cid,gfid)
    while(x):
        duel._reduce_gift(gid,uid,gfid)
        duel._add_favor(gid,uid,cid,favor)
        x -= 1
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    c = chara.fromid(cid)
    msg = f'\n{c.name}:“{text}”\n\n你和{c.name}的好感上升了{favor*num}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)    

@sv.scheduled_job('cron', hour ='*',)
async def clock():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if not now.hour == 5:#每天5点结算
        return         
    score_dict = {}
    score_counter = ScoreCounter2()
    duel = DuelCounter() 
    bot = nonebot.get_bot()
    r = 0
    n = 0
    glist = await bot.get_group_list()
    d = {}
    for m in glist:
        d[m['group_id']] = m['group_id']
    mlist = duel._get_gid_list()
    for e in range(len(mlist)):
     gid = int(mlist[e])       
     if not gid in d: #判断是否在群，避免100
        continue
     if duel._get_SWITCH2(gid) == 0:#判断是否开启惩罚，默认为关
            continue
     umlist = duel._get_uid_list(gid)
     for s in range(len(umlist)):
        uid = int(umlist[s])
        if uid != '':#避免返回空uid
         Game = duel._get_DALIY(gid,uid)
         DayS = duel._get_TOTAL(gid,uid)#获取连续多少天不决斗
         level = duel._get_level(gid,uid)
         if level >=1 and Game == 0:#如果需要连续多少天不决斗惩罚在这改
            duel._TOTAL_ADD(gid,uid)#增加一天未决斗天数
           #惩罚内容
            if DayS >= 2:#连续两天不决斗
             n = 1
             r = 0
            else:
             n = 0
            while(n):
             cidlist = duel._get_cards(gid, uid)
             try:
                selected_girl = random.choice(cidlist)
             except:
                break
             queen = duel._search_queen(gid,uid)
           #判断被扣掉的的是否为妻子，是则重选。    
             if selected_girl==queen:
                if r!=10:
                    r+=1
                    continue
                else:
                    break
             else:
               #判断好感是否足够，足够则扣掉好感
                favor = duel._get_favor(gid,uid,selected_girl)    
                if favor>=favor_reduce_NEED:
                    c = chara.fromid(selected_girl)
                    duel._reduce_favor(gid,uid,selected_girl,favor_reduce)
                    msg = f'[CQ:at,qq={uid}]由于连续两天未决斗，您与{c.name}的好感下降了{favor_reduce}点。\n{c.icon.cqcode}'
                    n = 0
                else:
                    c = chara.fromid(selected_girl)
                    duel._delete_card(gid, uid, selected_girl)
                    msg = f'[CQ:at,qq={uid}]由于昨日未决斗，且好感过低，您的女友{c.name}离开了\n{c.icon.cqcode}'
                    n = 0
                await asyncio.sleep(1)
                await bot.send_group_msg(
                    group_id = int(gid),
                    message = msg
                )
         duel._DALIY_SET(gid,uid)#重置今日是否决斗
         s += 1
    #await bot.send_group_msg(
                   #group_id = int(gid),
                   #message = f'本群公爵以上，未参与过改版后决斗的有{i}人，请注意，超出7天不决斗您的数据会被清除！'
               #) 
    e += 1

from .comateffectiveness import *
from .cechara import *