# -*- coding: utf-8 -*-
"""pcr_duel 贵族决斗插件入口：创建 Service 并注册各功能子模块"""
from hoshino import Service

sv = Service('贵族决斗', enable_on_default=False)

from .core import *  # noqa: E402,F401,F403  对外保持 ScoreCounter2 等符号可用（coinboard 依赖）
from . import handlers  # noqa: E402,F401
from . import combat  # noqa: E402,F401
