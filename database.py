"""
Database access layer for UmugandaSync.

Provides connection management, query execution, CRUD helpers,
transaction support, batch operations, and health checks.
All domain modules import from here instead of using mysql.connector directly.

Usage:
    row = database.run_query("SELECT * FROM members WHERE member_id = %s", (1,), fetch="one")
    rows = database.get_many("members", where="status = %s", where_values=("Active",), order_by="last_name")
    new_id = database.insert_one("members", {"first_name": "John", "last_name": "Doe", ...})
    with database.transaction() as cursor:
        cursor.execute(...)
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
CONNECT_TIMEOUT: int = 10


def _get_ssl_config() -> dict:
    ssl_config = {}
    if config.DB_SSL_CA:
        ssl_config["ssl_ca"] = config.DB_SSL_CA
    if config.DB_SSL_MODE:
        ssl_config["ssl_disabled"] = config.DB_SSL_MODE.upper() != "REQUIRED"
    return ssl_config


def _get_pool() -> Optional[MySQLConnectionPool]:
    global _pool
    if _pool is None:
        try:
            _pool = MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                connect_timeout=CONNECT_TIMEOUT,
                **_get_ssl_config(),
            )
            logger.info(f"Connection pool '{POOL_NAME}' created (size={POOL_SIZE})")
        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            return None
    return _pool


def connect_db() -> Optional[mysql.connector.MySQLConnection]:
    """Get a database connection from the pool, falling back to direct connect."""
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
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            connect_timeout=CONNECT_TIMEOUT,
            **_get_ssl_config(),
        )
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        print("Could not connect to database.")
        print(f"  Host: {config.DB_HOST}")
        print(f"  Port: {config.DB_PORT}")
        print(f"  User: {config.DB_USER}")
        print(f"  Database: {config.DB_NAME}")
        print(f"  Error: {e}")
        print()
        print("Checklist:")
        print("  1. Is MySQL running and reachable?")
        print("  2. Set env vars or update .env with correct credentials")
        print("  3. Run: mysql -u root < database.sql")
        return None


def close_db(connection: Any, cursor: Any = None) -> None:
    """Safely close a cursor and connection, returning pool connections."""
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
        sql_preview = sql[:80] + "..." if len(sql) > 80 else sql
        print(f"Query: {sql_preview}")
        try:
            connection.rollback()
        except Error:
            pass
        close_db(connection, cursor)
        return None


def execute_transaction(queries):
    connection = connect_db()
    if connection is None:
        return False
    cursor = None
    try:
        cursor = connection.cursor()
        for sql, values in queries:
            cursor.execute(sql, values)
        connection.commit()
        return True
    except Error:
        connection.rollback()
        raise
    finally:
        close_db(connection, cursor)


def test_connection() -> bool:
    """Quick health check — returns True if database is reachable."""
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
