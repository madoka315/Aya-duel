import importlib

import pygtrie
from fuzzywuzzy import process

import hoshino
from hoshino import log, util

from . import data

logger = log.new_logger('pcr_duel.chara', hoshino.config.DEBUG)
UNKNOWN = 1000


class Roster:

    def __init__(self):
        self._roster = pygtrie.CharTrie()
        self.update()

    def update(self):
        importlib.reload(data)
        self._roster.clear()
        self._alias_display = {}
        pack_of = {}
        for pack, ids in data.DLC_IDS.items():
            for i in ids:
                pack_of[i] = pack
        dup_count = 0
        for idx, names in data.CHARA_NAME.items():
            for n in names:
                key = util.normalize_str(n)
                if key not in self._roster:
                    self._roster[key] = idx
                    continue
                if self._roster[key] == idx:
                    continue
                # 重名：基础角色优先占用原名，DLC 角色追加「名字(包名)」别名
                dup_count += 1
                pack = pack_of.get(idx)
                if pack is None:
                    continue
                display = data.DLC_NAMES.get(pack, pack)
                alias_text = f'{n}({display})'
                alias = util.normalize_str(alias_text)
                suffix = 2
                while alias in self._roster and self._roster[alias] != idx:
                    alias_text = f'{n}({display}{suffix})'
                    alias = util.normalize_str(alias_text)
                    suffix += 1
                if alias not in self._roster:
                    self._roster[alias] = idx
                    self._alias_display[idx] = alias_text
        self._all_name_list = self._roster.keys()
        if dup_count:
            logger.debug(f'pcr_duel.chara.Roster: {dup_count} 个重名已用「名字(包名)」别名区分')

    def alias_of(self, cid):
        """重名角色的消歧昵称，如「初音未来(啤酒烧烤)」；无重名返回空串"""
        return self._alias_display.get(cid, '')

    def get_id(self, name):
        name = util.normalize_str(name)
        return self._roster[name] if name in self._roster else UNKNOWN

    def guess_id(self, name):
        """@return: id, name, score"""
        name, score = process.extractOne(name, self._all_name_list, processor=util.normalize_str)
        return self._roster[name], name, score

    def parse_team(self, namestr):
        """@return: List[ids], unknown_namestr"""
        namestr = util.normalize_str(namestr.strip())
        team = []
        unknown = []
        while namestr:
            item = self._roster.longest_prefix(namestr)
            if not item:
                unknown.append(namestr[0])
                namestr = namestr[1:].lstrip()
            else:
                team.append(item.value)
                namestr = namestr[len(item.key):].lstrip()
        return team, ''.join(unknown)


roster = Roster()
