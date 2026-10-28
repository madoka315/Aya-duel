# -*- coding: utf-8 -*-
"""贵族决斗：女友/爵位/礼物/胜负等核心数据表"""
import os
import sqlite3
from ..constants import DUEL_DB_PATH
from .base import Singleton, get_connection






   
# 记录贵族相关数据

class DuelCounter(Singleton):
    def __init__(self):
        if self._ready:
            return
        self._create_charatable()
        self._create_uidtable()
        self._create_leveltable()
        self._create_queentable()
        self._create_weapon()
        self._create_WLC()
        self._create_DayDuel()
        self._create_favortable()
        self._create_gifttable()
        self._create_SWITCH2()
        self._create_warehousetable()
        self._ready = True

    def _connect(self):
        return get_connection(DUEL_DB_PATH)

    def _create_charatable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS CHARATABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except Exception:
            raise Exception('创建角色表发生错误')

    def _create_uidtable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS UIDTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except Exception:
            raise Exception('创建UID表发生错误')

    def _create_leveltable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS LEVELTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           LEVEL           INT    NOT NULL,
                           
                           PRIMARY KEY(GID, UID));''')
        except Exception:
            raise Exception('创建UID表发生错误')

    def _get_card_owner(self, gid, cid):
        try:
            r = self._connect().execute("SELECT UID FROM CHARATABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找角色归属发生错误')

    def _set_card_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO CHARATABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_card_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM CHARATABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )


# 查询已被邀请的女友列表

    def _get_card_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM CHARATABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}

    def _get_level(self, gid, uid):
        try:
            r = self._connect().execute("SELECT LEVEL FROM LEVELTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找等级发生错误')

    def _get_cards(self, gid, uid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT CID, NUM FROM UIDTABLE WHERE GID=? AND UID=? AND NUM>0", (gid, uid)
            ).fetchall()
        return [c[0] for c in r] if r else {}

    def _get_card_num(self, gid, uid, cid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT NUM FROM UIDTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)
            ).fetchone()
            return r[0] if r else 0

    def _add_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        if cid !=9999:
            self._set_card_owner(gid, cid, uid)
            self._set_favor(gid,uid,cid,0)

    def _delete_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        self._delete_card_owner(gid, cid)
        self._delete_favor(gid,uid,cid)

    def _add_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _reduce_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _set_level(self, gid, uid, level):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )
    def _get_level_num(self, gid, level):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT COUNT(UID) FROM LEVELTABLE WHERE GID=? AND LEVEL=? ", (gid, level)
            ).fetchone()
            return r[0] if r else 0    



#皇后部分

    def _create_queentable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS QUEENTABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except Exception:
            raise Exception('创建皇后表发生错误')

    def _get_queen_owner(self, gid, cid):
        try:
            r = self._connect().execute("SELECT UID FROM QUEENTABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找皇后归属发生错误')

    def _set_queen_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO QUEENTABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_queen_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM QUEENTABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )
    def _get_queen_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM QUEENTABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}
#查询某人的皇后，无则返回0
    def _search_queen(self,gid,uid):
        try:
            r = self._connect().execute("SELECT CID FROM QUEENTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找皇后发生错误')
#购买女友上限部分（移植自上游0.7）
    def _create_warehousetable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WAREHOUSE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except Exception:
            raise Exception('创建仓库上限表发生错误')

    def _get_warehouse(self, gid, uid):
        try:
            r = self._connect().execute("SELECT NUM FROM WAREHOUSE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找上限发生错误')

    def _add_warehouse(self, gid, uid, num):
        housenum = self._get_warehouse(gid, uid)
        housenum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WAREHOUSE (GID, UID, NUM) VALUES (?, ?, ?)",
                (gid, uid, housenum),
            )
#好感度部分
    def _create_favortable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS FAVORTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           FAVOR           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except Exception:
            raise Exception('创建好感表发生错误')


    def _set_favor(self, gid, uid, cid, favor):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _get_favor(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT FAVOR FROM FAVORTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找好感发生错误')

    def _add_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        if favor == None:
            favor = 0
        favor += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _reduce_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        favor -= num
        favor = max(favor,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _delete_favor(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM FAVORTABLE  WHERE GID=? AND UID=? AND CID=?",
                (gid, uid, cid),
            )
#礼物仓库部分

    def _create_gifttable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GIFTTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           GFID             INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, GFID));''')
        except Exception:
            raise Exception('创建礼物表发生错误')

    def _get_gift_num(self, gid, uid, gfid):
        try:
            r = self._connect().execute("SELECT NUM FROM GIFTTABLE WHERE GID=? AND UID=? AND GFID=?", (gid, uid, gfid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找礼物发生错误')

    def _add_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        if giftnum == None:
            giftnum = 0
        giftnum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            )    

    def _reduce_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        giftnum -= num
        giftnum = max(giftnum,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            ) 
#群惩罚开关部分
    def _create_SWITCH2(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SWITCHCF
                          (GID             INT    NOT NULL,
                           NUM             INT    NULL,
                           PRIMARY KEY(GID));''')
        except Exception:
            raise Exception('创建开关表发生错误')
            
    def _get_SWITCH2(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT NUM FROM SWITCHCF WHERE GID=?", (gid,)).fetchone()
            return 0 if r is None else r[0]
            
    def _set_SWITCH2(self, gid, num):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO SWITCHCF (GID, NUM) VALUES (?, ?)",
                (gid, num),
            )
#武器部分
    def _create_weapon(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WEAPON
                          (GID             INT    NOT NULL,
                           WEAPON           INT    NOT NULL,
                           PRIMARY KEY(GID));''')
        except Exception:
            raise Exception('创建武器表发生错误')
            
    def _get_weapon(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT WEAPON FROM WEAPON WHERE GID=?", (gid,)).fetchone()
            return 6 if r is None else r[0]
    
    def _set_weapon(self, gid, weapon):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WEAPON (GID, WEAPON) VALUES (?, ?)",
                (gid, weapon),
            )
#胜负场部分
    def _create_WLC(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WLC
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           WIN             INT    NOT NULL,
                           LOST            INT    NOT NULL,
                           ADMIT           INT    NOT NULL,
                           PRIMARY KEY(GID,UID));''')
        except Exception:
            raise Exception('创建胜负表发生错误')
            
    def _get_WLCWIN(self, gid, uid):
        try:
            r = self._connect().execute("SELECT WIN FROM WLC WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找胜场发生错误')
    
    def _get_WLCLOSE(self, gid, uid):
        try:
            r = self._connect().execute("SELECT LOST FROM WLC WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找负场发生错误')
    
    def _get_ADMIT(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ADMIT FROM WLC WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找认输场发生错误')
    
    def _add_Win(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, WIN+1, LOSE, ADMIT))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')
            
    def _add_Lose(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, WIN, LOSE+1, ADMIT))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')
    
    def _add_ADMIT(self, gid, uid):
        try:
            WIN = self._get_WLCWIN(gid, uid)
            LOSE = self._get_WLCLOSE(gid, uid)
            ADMIT = self._get_ADMIT(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, WIN, LOSE, ADMIT+1))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')
            
    def _WLC_Remake(self, gid, uid):
        try:
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WLC (GID,UID,WIN,LOST,ADMIT) \
                                VALUES (?,?,?,?,?)", (gid, uid, 0, 0, 0))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')
            
#每日不决斗扣除女友部分
    def _get_gid_list(self):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT DISTINCT(GID) FROM LEVELTABLE").fetchall()
            return [g[0] for g in r] if r else {}
    
    def _get_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM LEVELTABLE WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except Exception:
            raise Exception('查找uid表发生错误')
            
    def _create_DayDuel(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS DAYDUEL
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           DALIY            INT    NOT NULL,
                           TOTAL           INT    NOT NULL,
                           PRIMARY KEY(GID,UID));''')
        except Exception:
            raise Exception('创建每日决斗表发生错误')
            
    def _DALIY_add(self, gid, uid):
        try:
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO DAYDUEL (GID,UID,DALIY,TOTAL) \
                                VALUES (?,?,?,?)", (gid, uid, 1, 0))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')
            
    def _get_DALIY(self, gid, uid):
        try:
            r = self._connect().execute("SELECT DALIY FROM DAYDUEL WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找决斗场次发生错误')
    
    def _get_TOTAL(self, gid, uid):
        try:
            r = self._connect().execute("SELECT TOTAL FROM DAYDUEL WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except Exception:
            raise Exception('查找未决斗天数发生错误')
            
    def _DALIY_SET(self, gid, uid):
        try:
            TOTAL = self._get_TOTAL(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO DAYDUEL (GID,UID,DALIY,TOTAL) \
                                VALUES (?,?,?,?)", (gid, uid, 0, TOTAL))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')
            
    def _TOTAL_ADD(self, gid, uid):
        try:
            TOTAL = self._get_TOTAL(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO DAYDUEL (GID,UID,DALIY,TOTAL) \
                                VALUES (?,?,?,?)", (gid, uid, 0, TOTAL + 1))
            conn.commit()
        except Exception:
            raise Exception('更新表发生错误')