"""
Database access layer for UmugandaSync.

Provides connection management, query execution, CRUD helpers,
transaction support, batch operations, and health checks.
All domain modules import from here instead of using mysql.connector directly.
"""

import logging
from contextlib import contextmanager
from typing import Any, Iterator, Optional

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

import config

logger = logging.getLogger(__name__)

_pool: Optional[MySQLConnectionPool] = None
POOL_NAME: str = "umuganda_pool"
POOL_SIZE: int = 5


def _get_pool() -> Optional[MySQLConnectionPool]:
    global _pool
    if _pool is None:
        try:
            _pool = MySQLConnectionPool(
                pool_name=POOL_N
AME,
                pool_size=POOL_SIZE,
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
            )
            logger.info(f"Connection pool '{POOL_NAME}' created (size={POOL_SIZE})")
        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            return None
    return _pool


def connect_db() -> Optional[mysql.connector.MySQLConnection]:
    pool = _get_pool()
    if pool is not None:
        try:
            connection = pool.get_connection()
            logger.debug("Got connection from pool")
            return connection
        except Error as e:
            logger.warning(f"Pool get_connection failed, fallback to direct: {e}")
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        print("Could not connect to database.")
        print(e)
        print("Check if MySQL is running and password in config.py")
        return None


def close_db(connection: Any, cursor: Any = None) -> None:
    try:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            if connection.is_connected():
                connection.close()
                logger.debug("Database connection closed")
    except Error:
        pass


def run_query(
    sql: str, values: Optional[tuple] = None, fetch: Optional[str] = None
) -> Any:
    connection = connect_db()
    if connection is None:
        return None
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        if values is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, values)

        if fetch == "one":
            result = cursor.fetchone()
            close_db(connection, cursor)
            return result
        if fetch == "all":
            result = cursor.fetchall()
            close_db(connection, cursor)
            return result
        connection.commit()
        last_id = cursor.lastrowid
        close_db(connection, cursor)
        return last_id
    except Error as e:
        logger.error(f"SQL error: {e}")
        print("SQL error:")
        print(e)
        try:
            connection.rollback()
        except Error:
            pass
        close_db(connection, cursor)
        return None


def test_connection() -> bool:
    connection = connect_db()
    if connection is None:
        print("FAILED: could not connect.")
        return False
    print("SUCCESS: connected to MySQL database", config.DB_NAME)
    close_db(connection)
    return True


@contextmanager
def transaction() -> Iterator[Any]:
    connection = connect_db()
    if connection is None:
        yield None
        return
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        yield cursor
        connection.commit()
    except Error as e:
        logger.error(f"Transaction error: {e}")
        print("Transaction error:", e)
        try:
            connection.rollback()
        except Error:
            pass
        raise
    finally:
        close_db(connection, cursor)


def execute_many(sql: str, values_list: list[tuple]) -> Optional[int]:
    connection = connect_db()
    if connection is None:
        return None
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.executemany(sql, values_list)
        connection.commit()
        affected = cursor.rowcount
        logger.debug(f"execute_many: {affected} rows affected")
        return affected
    except Error as e:
        logger.error(f"Batch SQL error: {e}")
        print("Batch SQL error:", e)
        try:
            connection.rollback()
        except Error:
            pass
        return None
    finally:
        close_db(connection, cursor)


def insert_one(table: str, data: dict[str, Any]) -> Optional[int]:
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return run_query(sql, tuple(data.values()), fetch=None)


def update_one(
    table: str, data: dict[str, Any], where: str, where_values: tuple = ()
) -> Optional[int]:
    set_clause = ", ".join([f"{k} = %s" for k in data])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
    values = tuple(data.values()) + where_values
    return run_query(sql, values, fetch=None)


def delete_one(table: str, where: str, where_values: tuple = ()) -> Optional[int]:
    sql = f"DELETE FROM {table} WHERE {where}"
    return run_query(sql, where_values, fetch=None)


def get_one(
    table: str, where: str, where_values: tuple = ()
) -> Optional[dict[str, Any]]:
    sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
    return run_query(sql, where_values, fetch="one")


def get_many(
    table: str,
    where: str = "1=1",
    where_values: tuple = (),
    order_by: str = "",
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    sql = f"SELECT * FROM {table} WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit is not None:
        sql += f" LIMIT {limit}"
    result = run_query(sql, where_values, fetch="all")
    return result if result is not None else []


def count(
    table: str, where: str = "1=1", where_values: tuple = ()
) -> int:
    sql = f"SELECT COUNT(*) AS total FROM {table} WHERE {where}"
    result = run_query(sql, where_values, fetch="one")
    if result is None:
        return 0
    return result.get("total", 0) or 0


def exists(
    table: str, where: str, where_values: tuple = ()
) -> bool:
    sql = f"SELECT 1 FROM {table} WHERE {where} LIMIT 1"
    result = run_query(sql, where_values, fetch="one")
    return result is not None


if __name__ == "__main__":
    test_connection()
