# -*- coding: utf-8 -*-
"""贵族决斗：DLC 名单、开关配置与校验"""
import json
import os
from .. import chara
from .constants import FILE_PATH


#加载DLC部分代码
#这里记录每个dlc的列表范围

#DLC列表自动从 chara/data/dlc/ 目录扫描生成：丢一个 json 即为新 DLC，零代码
#已退休DLC（million/sakukoi/majsoul/noraneko/umamusume/punishing/vtuber/mangekyou/tsubakioka）
#已于2026-10-28彻底移除，勿再添加。
dlcdict = {name: ids for name, ids in chara.DLC_IDS.items()}
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