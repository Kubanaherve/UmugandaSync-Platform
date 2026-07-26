"""
Database access layer for UmugandaSync.

Provides connection management, query execution, CRUD helpers,
transaction support, batch operations, and health checks.
All domain modules import from here instead of using mysql.connector directly.

Usage:
    row = database.run_query("SELECT * FROM members WHERE national_id = %s", (national_id,), fetch="one")
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


def _table_exists(cursor: Any, table: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (config.DB_NAME, table),
    )
    row = cursor.fetchone()
    return bool(row and row[0])


def _column_exists(cursor: Any, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
        """,
        (config.DB_NAME, table, column),
    )
    row = cursor.fetchone()
    return bool(row and row[0])


def _index_exists(cursor: Any, table: str, index_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.statistics
        WHERE table_schema = %s AND table_name = %s AND index_name = %s
        """,
        (config.DB_NAME, table, index_name),
    )
    row = cursor.fetchone()
    return bool(row and row[0])


def _members_uses_legacy_int_pk(cursor: Any) -> bool:
    """True when members still has the old auto-increment member_id primary key."""
    if not _column_exists(cursor, "members", "member_id"):
        return False
    cursor.execute(
        """
        SELECT DATA_TYPE, COLUMN_KEY
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = 'members'
          AND column_name = 'member_id'
        """,
        (config.DB_NAME,),
    )
    row = cursor.fetchone()
    if not row:
        return False
    data_type, column_key = row[0], row[1]
    return str(data_type).lower() in ("int", "integer") and column_key == "PRI"


def ensure_schema() -> bool:
    """
    Bring an older umuganda_sync database in line with database.sql
    without dropping existing data when safe.

    Members must use national_id CHAR(16) as the primary key. Databases
    still on the legacy INT member_id PK cannot be migrated in place —
    reload with: mysql -u root < database.sql
    """
    connection = connect_db()
    if connection is None:
        return False

    cursor = None
    applied: list[str] = []
    try:
        cursor = connection.cursor()

        required_tables = (
            "admins",
            "members",
            "attendance",
            "projects",
            "tools",
            "tool_borrows",
        )
        missing_core = [t for t in required_tables if not _table_exists(cursor, t)]
        if missing_core:
            logger.error("Missing core tables: %s", ", ".join(missing_core))
            print("Database is incomplete. Missing tables:", ", ".join(missing_core))
            print("Run: mysql -u root < database.sql")
            return False

        if _members_uses_legacy_int_pk(cursor):
            logger.error("Legacy INT member_id primary key detected")
            print()
            print("Your database still uses the old integer Member ID.")
            print("UmugandaSync now requires the 16-digit National ID as the")
            print("primary key for members (and as member_id in related tables).")
            print()
            print("Reload the schema (this recreates the database):")
            print("  mysql -u root < database.sql")
            print()
            return False

        if not _column_exists(cursor, "members", "national_id"):
            print("members.national_id is missing. Run: mysql -u root < database.sql")
            return False

        # members.email — required by members.py and search.py
        if not _column_exists(cursor, "members", "email"):
            cursor.execute(
                """
                ALTER TABLE members
                ADD COLUMN email VARCHAR(100) NULL AFTER national_id
                """
            )
            applied.append("members.email")

        # Prefer longer password hashes / future bcrypt
        cursor.execute(
            """
            SELECT CHARACTER_MAXIMUM_LENGTH
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'admins'
              AND column_name = 'password'
            """,
            (config.DB_NAME,),
        )
        pw_len_row = cursor.fetchone()
        if pw_len_row and pw_len_row[0] is not None and int(pw_len_row[0]) < 255:
            cursor.execute(
                "ALTER TABLE admins MODIFY password VARCHAR(255) NOT NULL"
            )
            applied.append("admins.password length")

        if not _table_exists(cursor, "notifications"):
            cursor.execute(
                """
                CREATE TABLE notifications (
                    notification_id   INT AUTO_INCREMENT PRIMARY KEY,
                    notification_type VARCHAR(50)  NOT NULL,
                    message           TEXT         NOT NULL,
                    related_id        INT          NULL,
                    severity          VARCHAR(20)  NOT NULL DEFAULT 'info',
                    is_read           TINYINT(1)   NOT NULL DEFAULT 0,
                    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT chk_notification_severity CHECK (
                        severity IN ('info', 'warning', 'error', 'success')
                    ),
                    CONSTRAINT chk_notification_type CHECK (
                        notification_type IN (
                            'low_stock', 'overdue_project', 'broken_tool',
                            'absent_member', 'new_member', 'attendance_reminder',
                            'system'
                        )
                    )
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            applied.append("notifications table")

        index_specs = (
            ("members", "idx_members_phone", "phone"),
            ("members", "idx_members_status", "status"),
            ("members", "idx_members_village", "village"),
            ("attendance", "idx_attendance_date", "attendance_date"),
            ("projects", "idx_projects_status", "status"),
            ("projects", "idx_projects_end_date", "expected_end_date"),
            ("tools", "idx_tools_condition", "condition_status"),
            ("tool_borrows", "idx_borrows_status", "status"),
        )
        for table, index_name, column in index_specs:
            if _table_exists(cursor, table) and not _index_exists(cursor, table, index_name):
                if _column_exists(cursor, table, column):
                    cursor.execute(
                        f"CREATE INDEX {index_name} ON {table}({column})"
                    )
                    applied.append(index_name)

        connection.commit()
        if applied:
            logger.info("Schema updates applied: %s", ", ".join(applied))
            print("Database schema updated:", ", ".join(applied))
        else:
            logger.info("Database schema already up to date")
        return True
    except Error as e:
        logger.error(f"Schema ensure failed: {e}")
        print("Could not update database schema:", e)
        try:
            connection.rollback()
        except Error:
            pass
        return False
    finally:
        close_db(connection, cursor)


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
    if test_connection():
        ensure_schema()
