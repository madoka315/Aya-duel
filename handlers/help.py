# -*- coding: utf-8 -*-
"""贵族决斗：总帮助"""
from hoshino.typing import CQEvent
from .. import sv
from ..core.constants import FORWARD_QQ


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