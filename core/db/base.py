# -*- coding: utf-8 -*-
"""贵族决斗：SQLite 单例与共享连接"""
import os
import sqlite3

_CONNECTIONS = {}


class Singleton:
    """进程内单例：保证建表只在首次实例化时执行"""

    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            inst = super().__new__(cls)
            inst._ready = False
            cls._instances[cls] = inst
        return cls._instances[cls]


def get_connection(path):
    """同一库文件复用同一条连接（WAL + busy_timeout），避免每条消息反复建连/建表"""
    conn = _CONNECTIONS.get(path)
    if conn is None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=3000')
        _CONNECTIONS[path] = conn
    return conn
