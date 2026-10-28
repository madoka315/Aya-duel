import os
import json

# pcr_duel 专用角色数据加载器
# 数据来源：data/base.json（基础角色）+ data/dlc/<名>.json（每 DLC 一个文件）
# 新增 DLC = 往 data/dlc/ 丢一个 json，零代码改动；dlcdict 由 DLC_IDS 自动生成

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BASE_PATH = os.path.join(DATA_DIR, 'base.json')
DLC_DIR = os.path.join(DATA_DIR, 'dlc')

CHARA_NAME = {}
DLC_IDS = {}

# DLC 显示名：用于重名角色的「名字(包名)」别名，如 初音未来(啤酒烧烤)
DLC_NAMES = {
    'blhx': '碧蓝航线',
    'yozi': '柚子社',
    'genshin': '原神',
    'kancolle': '舰C',
    'koikake': '恋×彼女',
    'cloverdays': 'Clover Days',
    'fgo': 'FGO',
    'amairochoco': '巧克甜恋',
    'nekopara': 'Nekopara',
    'pjsk': '啤酒烧烤',
    'bangdream': 'BanG Dream',
    'mrfz': '明日方舟',
}


def _load() -> None:
    global CHARA_NAME, DLC_IDS
    CHARA_NAME = {}
    DLC_IDS = {}
    with open(BASE_PATH, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    for i, names in raw.items():
        CHARA_NAME[int(i)] = names
    for fn in sorted(os.listdir(DLC_DIR)):
        if not fn.endswith('.json'):
            continue
        name = fn[:-5]
        with open(os.path.join(DLC_DIR, fn), 'r', encoding='utf-8') as f:
            raw = json.load(f)
        DLC_IDS[name] = sorted(int(i) for i in raw)
        for i, names in raw.items():
            CHARA_NAME[int(i)] = names


_load()
