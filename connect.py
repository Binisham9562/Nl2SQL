"""Quick check that the database settings in .env work. Run: python connect.py"""
import os

import pymysql
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print("Connection failed:", e)
