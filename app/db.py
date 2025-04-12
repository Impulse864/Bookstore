import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Database connection pool created successfully!")
except Exception as e:
    print(f"Error setting up database connection pool: {e}")

def get_db_connection():
    return connection_pool.getconn()

def close_db_connection(conn):
    connection_pool.putconn(conn)
