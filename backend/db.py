import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import pooling


load_dotenv()


def env_value(*names, default=None, strip=True):
    for name in names:
        value = os.getenv(name)
        if value is None:
            continue
        if strip:
            value = value.strip()
        if value != "":
            return value
    return default


DB_CONFIG = {
    "host": env_value("MYSQLHOST", "MYSQL_HOST", "DB_HOST", default="localhost"),
    "port": int(env_value("MYSQLPORT", "MYSQL_PORT", "DB_PORT", default="3306")),
    "user": env_value("MYSQLUSER", "MYSQL_USER", "DB_USER", default="root"),
    "password": env_value("MYSQLPASSWORD", "MYSQL_PASSWORD", "DB_PASSWORD", default="", strip=False),
    "database": env_value("MYSQLDATABASE", "MYSQL_DB", "DB_NAME", default="library_management"),
}

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="library_pool",
            pool_size=5,
            autocommit=False,
            **DB_CONFIG,
        )
    return _pool


def get_connection():
    conn = get_pool().get_connection()
    # Explicitly rollback to reset the transaction state on checkout.
    # This prevents stale reads from connection pool reuse when autocommit is False.
    try:
        conn.rollback()
    except:
        pass
    return conn
