# -*- coding: utf-8 -*-
"""贵族决斗：总帮助（含已下线玩法的友好提示）"""
from hoshino.typing import CQEvent
from .. import sv
from ..core.constants import FORWARD_QQ


#帮助中猜角色猜头像获胜加金币为个人魔改，如果不魔改可以删掉这两行描述。
@sv.on_fullmatch(['贵族决斗帮助','贵族帮助','贵族指令'])
async def duel_help(bot, ev: CQEvent):
    msg='''
╔                                       ╗    
        贵族决斗相关指令

   1.贵族签到
   2.查询贵族
   3.本群贵族
   4.贵族决斗+@qq
   5.领金币/查金币
   6.贵族舞会(招募女友)
   7.查女友+角色名
   8.升级贵族
   9.重置金币+qq (限群主)
   10.重置角色+qq (限群主) 
   11.重置决斗/重置礼物交换(限管理，卡住时用)
   12.分手+角色名
   13.为@qq转账xxx金币
   14.用xxx金币与@qq交易女友+角色名
   15.确认重开(删号重来)
   16.声望排行/胜场排行/女友排行
   17.武器列表(更换决斗武器)
   18.查询本群不决斗惩罚
   19.用金币兑换声望
   20.神秘商店
   21.购买上限(提高女友数限制)
   22.查名字+女友序号
   
  一个女友只属于一位群友；皇帝可迎娶正妻
  可以从签到、贵族决斗、战斗等途径入手金币
  从贵族决斗、兑换等途径获取声望
  
  其他帮助：
  →声望系统帮助(声望系统国王可开)
  →好感系统帮助
  →战斗系统帮助(战力/rank/巡逻/周本/赛马)
  →dlc帮助
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


_OFFLINE_CMDS = [
    '装备列表', '我的装备', '穿装备', '穿戴装备', '取消装备', '一键穿戴', '一键装备',
    '一键卸装', '一键取消', '装备分解', '分解装备', '一键分解', '副本商城', '兑换装备',
    '抽装备', '查看武器池', '武器池', '我的保底', '查看保底', '星尘兑换',
    '我的副本币', '查副本币', '副本列表', '查看副本', '创建队伍', '解散队伍', '删除队伍',
    '我的队伍', '查询队伍', '挂机修炼', '开始挂机', '结束修炼', '取消修炼',
    '副本系统帮助', '副本帮助', '装备帮助', '抽卡系统帮助', '抽卡帮助', '会战系统帮助', '会战帮助',
]

_OFFLINE_TIP = '该玩法已下线。\n现有玩法：巡逻、出刀（周本）、赛马，发送 战斗帮助 查看详情'


@sv.on_prefix(_OFFLINE_CMDS)
async def offline_tip(bot, ev: CQEvent):
    await bot.send(ev, _OFFLINE_TIP, at_sender=True)


@sv.on_rex(r'^编队.*(进入副本|boss战|补时刀|模拟).*$')
async def offline_compose(bot, ev: CQEvent):
    await bot.send(ev, _OFFLINE_TIP, at_sender=True)


@sv.on_rex(r'^用\d+金币兑换副本币$')
async def offline_duncoin(bot, ev: CQEvent):
    await bot.send(ev, '副本币系统已下线，金币直接用于招募、礼物、约会、rank、赛马下注。', at_sender=True)
