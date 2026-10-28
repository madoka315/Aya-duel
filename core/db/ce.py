# -*- coding: utf-8 -*-
"""贵族决斗：战斗数据表（等级 / 代表 / rank / 经验池 / 周本）"""
from ..constants import DUEL_DB_PATH
from .base import Singleton, get_connection


class CECounter(Singleton):
    def __init__(self):
        if self._ready:
            return
        self._create_exptable()
        self._create_guajitable()
        self._create_rank()
        self._create_expnumtable()
        self._create_weeklystate()
        self._create_weeklyfight()
        self._ready = True

    def _connect(self):
        return get_connection(DUEL_DB_PATH)

    # ---------- 角色等级 / 经验 ----------
    def _create_exptable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS EXPTABLE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           CID           INT    NOT NULL,
                           LEVEL           INT    NOT NULL,
                           EXP           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except Exception:
            raise Exception('创建角色等级经验表发生错误')

    # 重置角色等级
    def _set_card_exp(self, gid, uid, cid, level=0, exp=0):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO EXPTABLE (GID, UID, CID, LEVEL, EXP) VALUES (?, ?, ?, ?, ?)",
                (gid, uid, cid, level, exp),
            )

    # 查询角色等级信息
    def _get_card_level(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT LEVEL FROM EXPTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)).fetchone()
            if r is None:
                self._set_card_exp(gid, uid, cid)
                return 0
            return r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))

    # 查询角色经验信息
    def _get_card_exp(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT EXP FROM EXPTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)).fetchone()
            if r is None:
                self._set_card_exp(gid, uid, cid)
                return 0
            return r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))

    # 更新角色等级、经验信息
    def _add_card_exp(self, gid, uid, cid, level, exp):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO EXPTABLE (GID, UID, CID, LEVEL, EXP) VALUES (?, ?, ?, ?, ?)",
                (gid, uid, cid, level, exp),
            )

    # ---------- 代表女友（原挂机绑定） ----------
    def _create_guajitable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GUAJITABLE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           CID           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except Exception:
            raise Exception('创建代表女友表发生错误')

    def _get_guaji(self, gid, uid):
        try:
            r = self._connect().execute("SELECT CID FROM GUAJITABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))

    def _add_guaji(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GUAJITABLE (GID, UID, CID) VALUES (?, ?, ?)",
                (gid, uid, cid),
            )

    # ---------- rank ----------
    def _create_rank(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS RANKTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           RANK        INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except Exception:
            raise Exception('创建rank表发生错误')

    def _add_rank(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO RANKTABLE (GID, UID, CID, RANK) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, 0),
            )

    def _up_rank(self, gid, uid, cid):
        rank = self._get_rank(gid, uid, cid)
        rank += 1
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO RANKTABLE (GID, UID, CID, RANK) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, rank),
            )

    def _get_rank(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT RANK FROM RANKTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找rank发生错误')

    def _get_cards_byrank(self, gid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT GID,RANK,UID,CID FROM RANKTABLE WHERE GID={gid} ORDER BY RANK desc LIMIT {num}").fetchall()
            return r if r else []

    # ---------- 经验池 ----------
    def _create_expnumtable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS EXPNUM
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           NUM        INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except Exception:
            raise Exception('创建经验池表发生错误')

    def _get_exp_chizi(self, gid, uid):
        try:
            r = self._connect().execute("SELECT NUM FROM EXPNUM WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            if r is None:
                return 0
            return r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))

    def _add_exp_chizi(self, gid, uid, num):
        now_exp = self._get_exp_chizi(gid, uid) + num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO EXPNUM (GID, UID, NUM) VALUES (?, ?, ?)",
                (gid, uid, now_exp),
            )

    # ---------- 周本 ----------
    def _create_weeklystate(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WEEKLYSTATE
                          (
                           GID             INT    NOT NULL,
                           PERIOD             INT    NOT NULL,
                           BOSSID             INT    NOT NULL,
                           HP        INT    NOT NULL,
                           PRIMARY KEY(GID));''')
        except Exception:
            raise Exception('创建周本状态表发生错误')

    def _create_weeklyfight(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WEEKLYFIGHT
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           PERIOD           INT    NOT NULL,
                           DMG        INT    NOT NULL,
                           PRIMARY KEY(GID, UID, PERIOD));''')
        except Exception:
            raise Exception('创建周本出刀表发生错误')

    def _get_weeklystate(self, gid, period):
        """返回 (bossid, hp)；没有记录返回 (0, 0)"""
        try:
            r = self._connect().execute("SELECT BOSSID,HP FROM WEEKLYSTATE WHERE GID=? AND PERIOD=?", (gid, period)).fetchone()
            return (0, 0) if r is None else (r[0], r[1])
        except Exception as e:
            raise Exception('错误:\n' + str(e))

    def _set_weeklystate(self, gid, period, bossid, hp):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WEEKLYSTATE (GID, PERIOD, BOSSID, HP) VALUES (?, ?, ?, ?)",
                (gid, period, bossid, hp),
            )

    def _up_weekly_hp(self, gid, period, hp):
        with self._connect() as conn:
            conn.execute(
                "UPDATE WEEKLYSTATE SET HP=? WHERE GID=? AND PERIOD=?",
                (hp, gid, period),
            )

    def _add_weeklyfight(self, gid, uid, period, dmg):
        now = self._connect().execute(
            "SELECT DMG FROM WEEKLYFIGHT WHERE GID=? AND UID=? AND PERIOD=?", (gid, uid, period)).fetchone()
        total = (0 if now is None else now[0]) + dmg
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WEEKLYFIGHT (GID, UID, PERIOD, DMG) VALUES (?, ?, ?, ?)",
                (gid, uid, period, total),
            )
        return total

    def _get_weekly_rank(self, gid, period, num=10):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT UID,DMG FROM WEEKLYFIGHT WHERE GID=? AND PERIOD=? ORDER BY DMG DESC LIMIT ?", (gid, period, num)).fetchall()
            return r if r else []

    def _get_weekly_participants(self, gid, period):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT UID FROM WEEKLYFIGHT WHERE GID=? AND PERIOD=?", (gid, period)).fetchall()
            return [x[0] for x in r] if r else []

    def _get_weekly_total(self, gid, period):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT SUM(DMG),COUNT(UID) FROM WEEKLYFIGHT WHERE GID=? AND PERIOD=?", (gid, period)).fetchone()
            if r is None or r[0] is None:
                return (0, 0)
            return (r[0], r[1])
