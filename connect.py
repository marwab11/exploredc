"""
ExploreDC - DBMS connection check
CS 5614 - Introduction to Database Systems, Summer 2026
Author: Marwa Bahr

Connects Python (interface language) to MySQL (DBMS) and confirms
the connection. The password is NEVER hardcoded: it is read from the
MYSQL_PASSWORD environment variable, or prompted for security.

Usage:
    pip install mysql-connector-python
    python connect.py
"""

import os
import getpass

import mysql.connector


def get_connection():
    password = os.environ.get("MYSQL_PASSWORD")
    if password is None:
        password = getpass.getpass("MySQL password: ")

    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=password,
        database="exploredc",
    )


def main():
    conn = get_connection()
    if conn.is_connected():
        info = conn.get_server_info()
        print("=" * 40)
        print("  Connected")
        print("=" * 40)
        print(f"DBMS: MySQL (server version {info})")
        print("Database: exploredc")

        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
        print(f"Tables ({len(tables)}): {', '.join(tables)}")

        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{t}`")
            print(f"  {t}: {cur.fetchone()[0]} rows")

        cur.close()
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
