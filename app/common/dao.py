import sqlite3
from sqlite3 import Connection
from functools import wraps
from app.common import config
import os
import inspect

DB_DIR_NAME = "db"
DB_FILE = "storage.db"

def get_db_file():
    """
    获取db文件
    :return: 返回db文件路径
    """
    db_dir = os.path.join(config.get_data_dir(), DB_DIR_NAME)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, DB_FILE)

def query(sql:str):
    with sqlite3.connect(get_db_file()) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        result = cursor.fetchone()

        if result:
            return dict(zip(columns, result))
        return None

def execute(sql:str):
    """
    执行sql
    :param sqls: 需要执行的sql列表
    :return:
    """
    with sqlite3.connect(get_db_file()) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
