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
        for idx, names in data.CHARA_NAME.items():
            for n in names:
                n = util.normalize_str(n)
                if n not in self._roster:
                    self._roster[n] = idx
                else:
                    logger.warning(f'pcr_duel.chara.Roster: 出现重名{n}于id{idx}与id{self._roster[n]}')
        self._all_name_list = self._roster.keys()

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
