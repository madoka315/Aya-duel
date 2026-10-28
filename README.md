# Aya-duel（贵族决斗）

在群里扮演贵族、招募女友、用俄罗斯轮盘决斗的小游戏。  
基于上游 [PcrDuel](https://github.com/Rs794613/PcrDuel) v0.5fix1 重写，模块名仍为 `pcr_duel`。

## 安装

1. 把本目录放到 `hoshino/modules/pcr_duel/`；
2. `hoshino/config/__bot__.py` 的 `MODULES_ON` 加上 `pcr_duel`；
3. 重启 hoshino，群里发送 `创建贵族`。

依赖：`hoshino`、`Pillow`、`pygtrie`、`fuzzywuzzy`、`zhconv`、`pytz`。

## 玩法

| 玩法   | 说明                                     |
| ---- | -------------------------------------- |
| 贵族决斗 | 轮流开枪的俄罗斯轮盘，输的一方随机失去一名女友                |
| 巡逻   | 每天 3 次，绑定的女友自动出战，产出金币/好感/经验            |
| 周本   | 全群共享血量的 boss，每天可出刀 1 次，自动取战力最高的 5 人    |
| 赛马场  | 女友参赛、5 段跑马直播，可押注                       |
| 养成   | 好感（约会/礼物）、rank（金币+好感）、等级（经验），三条线共同决定战力 |
| 爵位   | 12 级：男爵 → 神帝                           |

## 核心数值

- 战力：决斗胜利追加金币、巡逻胜率、周本伤害、赛马速度（权重很低）
- 决斗胜负与战力无关，只取决于子弹位置

## 指令

发送以下指令查看完整说明：

- `贵族帮助` —— 总表
- `战斗帮助` —— 战力 / rank / 巡逻 / 周本 / 赛马
- `好感系统帮助` —— 约会 / 礼物 / 交换
- `声望系统帮助` —— 加冕 / 皇室婚礼 / 兑换
- `dlc帮助` —— DLC 加载与重名角色写法

## 目录

```
core/      常量、规则、状态机、数据库（base / score / duel / ce）
handlers/  指令入口（决斗 / 女友 / 爵位 / 经济 / 交易 / 武器 / 赛马 / DLC / 帮助）
combat/    战斗扩展（成长 / 巡逻 / 周本 / 经验池）
chara/     角色数据与头像解析（自包含，不依赖 priconne 包）
```

## 数据

- 数据库：`~/.hoshino/pcr_duel.db`（女友、爵位、rank、周本）、`~/.hoshino/pcr_running_counter.db`（金币、声望、每日限次）
- 角色数据：`chara/data/base.json` + `chara/data/dlc/*.json`，新增 DLC 只需丢一个 json
- 头像：`res/img/pcr_duel/unit/`，缺图时 DLC 角色显示 unknown，基础角色后台补图

## 说明

- 本版本删除了装备 / 抽卡 / 副本币 / 队伍 / 挂机修炼，旧指令会提示已下线
- 许可证见 [LICENSE](LICENSE)
