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


import ollama


def generate_sql(user_query, schema):
    prompt = f"""
    You are a SQL expert. Convert this natural language to valid MySQL syntax query: 

    Database Schema:
    {schema}

    Query: "{user_query}"

    Rules:
    - Use ONLY the tables/columns above.
    - Return ONLY SQL, no explanations.
    - Avoid `+` for concatenation (use `CONCAT()`).
    - Don't use */ or ---------- on start of your answer
    - Use `IFNULL()` instead of `COALESCE()` if needed.
    - For dates, use `YYYY-MM-DD` format.
    """
    response = ollama.generate(
        model="sqlcoder",
        prompt=prompt
    )
    return response["response"].strip()

def run_sql(sql):
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return columns, results
    except Exception as e:
        return None, str(e)
    finally:
        cursor.close()
        db.close()


import streamlit as st

st.title("Natural Language to SQL Dashboard")

schema = get_schema()
user_query = st.text_input("Ask a question (e.g., 'Show me top-selling products last quarter'):")

if user_query:
    sql = generate_sql(user_query, schema)
    st.code(f"Generated SQL:\n{sql}", language="sql")

    if st.button("Run Query"):
        columns, results = run_sql(sql)
        if columns:
            st.table(results)
        else:
            st.error(f"Error: {results}")

