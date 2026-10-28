# -*- coding: utf-8 -*-
"""贵族决斗：决斗/交易/礼物交换的内存状态机与每日限次器"""
from .constants import ALLOWANCE_DAILY_LIMIT, DATE_DAILY_LIMIT, DATE_EXTRA_LIMIT, DUEL_DAILY_LIMIT, GIFT_DAILY_LIMIT, GIFT_PER_GIRL_DAILY, PATROL_DAILY_LIMIT, RACE_DAILY_LIMIT, RECRUIT_DAILY_LIMIT, RESET_HOUR, Remake_LIMIT, SHOP_LIMIT, SIGN_DAILY_LIMIT, SW_DAILY_LIMIT, WEEKLY_DAILY_LIMIT
from .db.score import DailyAmountLimiter, ScoreCounter2




daily_sign_limiter = DailyAmountLimiter("sign", SIGN_DAILY_LIMIT, RESET_HOUR)
daily_date_limiter = DailyAmountLimiter("date", DATE_DAILY_LIMIT, RESET_HOUR)
daily_gift_limiter = DailyAmountLimiter("gift", GIFT_DAILY_LIMIT, RESET_HOUR)
daily_duel_limiter = DailyAmountLimiter("duel", DUEL_DAILY_LIMIT, RESET_HOUR)
daily_Remake_limiter = DailyAmountLimiter("Remake", Remake_LIMIT, RESET_HOUR)
daily_GOLDTOSW_limiter = DailyAmountLimiter("sw", SW_DAILY_LIMIT, RESET_HOUR)
daily_allowance_limiter = DailyAmountLimiter("allowance", ALLOWANCE_DAILY_LIMIT, RESET_HOUR)
daily_SHOP_limiter = DailyAmountLimiter("shop", SHOP_LIMIT, RESET_HOUR)
daily_patrol_limiter = DailyAmountLimiter("patrol", PATROL_DAILY_LIMIT, RESET_HOUR)
daily_weekly_limiter = DailyAmountLimiter("weekly", WEEKLY_DAILY_LIMIT, RESET_HOUR)
daily_race_limiter = DailyAmountLimiter("race", RACE_DAILY_LIMIT, RESET_HOUR)
daily_recruit_limiter = DailyAmountLimiter("recruit", RECRUIT_DAILY_LIMIT, RESET_HOUR)
daily_gift_per_girl_limiter = DailyAmountLimiter("giftgirl", GIFT_PER_GIRL_DAILY, RESET_HOUR)
daily_date_extra_limiter = DailyAmountLimiter("dateextra", DATE_EXTRA_LIMIT, RESET_HOUR)

#招募连败计数（内存，成功清零；重启清零可接受）
_recruit_fail_count = {}


def get_recruit_fail_count(gid, uid):
    return _recruit_fail_count.get((gid, uid), 0)


def add_recruit_fail_count(gid, uid):
    _recruit_fail_count[(gid, uid)] = get_recruit_fail_count(gid, uid) + 1


def clear_recruit_fail_count(gid, uid):
    _recruit_fail_count.pop((gid, uid), None)


def refund_allin_support(gid):
    """退还本群尚未结算的梭哈托管金币，返回[(uid, 退还金币)]"""
    support = duel_judger.get_support(gid)
    if not support:
        return []
    score_counter = ScoreCounter2()
    refunded = []
    for uid in support:
        support_id, support_score, allin = support[uid]
        if allin:
            score_counter._add_score(gid, uid, support_score)
            refunded.append((uid, support_score))
    return refunded




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

    def add_support(self, gid, uid, id, score, allin=False):
        self.support[gid][uid] = [id, score, allin]

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


class HorseRace:
    """赛马场：每群一间内存房间，报名→下注→鸣枪→结算，全内存不落库"""

    def __init__(self):
        self.rooms = {}

    def get(self, gid):
        return self.rooms.get(gid)

    def new_room(self, gid, task=None):
        self.rooms[gid] = {
            'horses': [],   # [{no, uid, cid, ce, speed, owner_name}]
            'bets': {},     # uid -> (horse_no, amount)
            'phase': 'signup',
            'task': task,
        }
        return self.rooms[gid]

    def remove(self, gid):
        room = self.rooms.pop(gid, None)
        if room and room.get('task') is not None:
            task = room['task']
            if not task.done():
                task.cancel()
        return room

    def add_horse(self, gid, uid, cid, ce, name):
        room = self.rooms.get(gid)
        if room is None:
            return None
        if any(h['uid'] == uid for h in room['horses']):
            return 'dup'
        no = len(room['horses']) + 1
        room['horses'].append({
            'no': no, 'uid': uid, 'cid': cid, 'ce': ce,
            'name': name, 'speed': 0, 'pos': 0,
        })
        return no


horse_race = HorseRace()