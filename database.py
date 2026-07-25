# database.py
# Owner: Rebecca
# This file connects python to mysql
# Other people should import this, dont write connect code in your own file

import mysql.connector
from mysql.connector import Error
import config


def connect_db():
    # open connection to our database
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return connection
    except Error as e:
        print("Could not connect to database.")
        print(e)
        print("Check if MySQL is running and password in config.py")
        return None


def close_db(connection, cursor=None):
    # close things so we dont leave connections open
    try:
        if cursor != None:
            cursor.close()
        if connection != None:
            if connection.is_connected():
                connection.close()
    except Error:
        pass


def run_query(sql, values=None, fetch=None):
    # Rebecca: one function for select/insert/update/delete
    # fetch = "one" or "all" or None (for insert/update/delete)
    connection = connect_db()
    if connection == None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        if values == None:
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

        # insert update delete
        connection.commit()
        last_id = cursor.lastrowid
        close_db(connection, cursor)
        return last_id

    except Error as e:
        print("SQL error:")
        print(e)
        try:
            connection.rollback()
        except Error:
            pass
        close_db(connection, cursor)
        return None


def test_connection():
    # quick test
    connection = connect_db()
    if connection == None:
        print("FAILED: could not connect.")
        return False
    print("SUCCESS: connected to MySQL database", config.DB_NAME)
    close_db(connection)
    return True


# if we run this file alone we can test connection
if __name__ == "__main__":
    test_connection()

