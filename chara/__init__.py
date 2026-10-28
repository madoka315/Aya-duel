from .data import CHARA_NAME, DLC_IDS
from .roster import roster, UNKNOWN
from .card import Chara, gen_team_pic

__all__ = ['CHARA_NAME', 'DLC_IDS', 'roster', 'UNKNOWN', 'Chara', 'gen_team_pic',
           'name2id', 'fromid', 'fromname', 'guess_id']


def name2id(name):
    return roster.get_id(name)


def fromid(id_, star=0, equip=0):
    return Chara(id_, star, equip)


def fromname(name, star=0, equip=0):
    id_ = name2id(name)
    return Chara(id_, star, equip)


def guess_id(name):
    """@return: id, name, score"""
    return roster.guess_id(name)
