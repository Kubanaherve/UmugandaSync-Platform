"""
Database access layer for UmugandaSync.

Provides connection management, query execution, and health checks.
All domain modules import from here instead of using mysql.connector directly.
"""

import logging
import mysql.connector
from mysql.connector import Error
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)


def connect_db() -> Optional[mysql.connector.MySQLConnection]:
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


if __name__ == "__main__":
    test_connection()
