import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()


def get_schema():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = db.cursor()

    # Fetch tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    schema = "Database Schema:\n"
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        schema += f"\nTable: {table_name}\nColumns:\n"
        for col in columns:
            schema += f"- {col[0]} ({col[1]})\n"

    # Add foreign keys
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME 
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE REFERENCED_TABLE_NAME IS NOT NULL 
        AND TABLE_SCHEMA = DATABASE()
    """)
    fks = cursor.fetchall()
    if fks:
        schema += "\nForeign Keys:\n"
        for fk in fks:
            schema += f"- {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}\n"

    cursor.close()
    db.close()
    return schema
