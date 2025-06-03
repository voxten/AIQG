import streamlit as st
import mysql.connector
from typing import Dict, Any, Optional, Tuple, List

# Database configuration
SUPPORTED_DB_TYPES = {
    "MySQL": {
        "module": mysql.connector,
        "port": 3306,
        "default_host": "localhost",
        "icon": "🛢️"
    },
}


def init_session_state():
    """Initialize session state variables"""
    if 'db_connections' not in st.session_state:
        st.session_state.db_connections = {}
    if 'active_connection' not in st.session_state:
        st.session_state.active_connection = None
    if 'last_connection' not in st.session_state:
        st.session_state.last_connection = None
    if 'schema' not in st.session_state:
        st.session_state.schema = ""
    if 'SUPPORTED_DB_TYPES' not in st.session_state:
        st.session_state.SUPPORTED_DB_TYPES = SUPPORTED_DB_TYPES
    if 'generated_sql' not in st.session_state:
        st.session_state.generated_sql = None

def get_db_connection(db_type: str, host: str, port: int, user: str, password: str, database: str) -> Any:
    """Get or create a database connection"""
    connection_key = f"{db_type}_{host}_{port}_{user}_{database}"

    if connection_key in st.session_state.db_connections:
        return st.session_state.db_connections[connection_key]

    try:
        if db_type == "MySQL":
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            st.session_state.db_connections[connection_key] = conn
            st.session_state.active_connection = connection_key
            return conn
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        return None


def get_schema(conn: Any, db_type: str) -> str:
    """Get database schema"""
    cursor = conn.cursor()
    schema = "Database Schema:\n"

    try:
        if db_type == "MySQL":
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                schema += f"\nTable: {table_name}\nColumns:\n"
                for col in columns:
                    schema += f"- {col[0]} ({col[1]})\n"

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
    except Exception as e:
        st.error(f"Error fetching schema: {str(e)}")
    finally:
        cursor.close()
    return schema


def run_sql(conn: Any, sql: str, db_type: str) -> Tuple[Optional[List[str]], Any]:
    """Execute SQL query"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        if cursor.description:
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return columns, results
        else:
            conn.commit()
            return None, f"Query executed successfully. Rows affected: {cursor.rowcount}"
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cursor.close()


def handle_connections():
    """Handle connection logic"""
    init_session_state()

    # Check if we need to refresh schema
    if (st.session_state.active_connection and
            st.session_state.active_connection != st.session_state.last_connection):
        conn = st.session_state.db_connections[st.session_state.active_connection]
        db_type = st.session_state.active_connection.split('_')[0]
        st.session_state.schema = get_schema(conn, db_type)
        st.session_state.last_connection = st.session_state.active_connection


def get_active_connection_info():
    """Get info about the active connection"""
    if not st.session_state.active_connection:
        return None

    conn_key = st.session_state.active_connection
    db_info = conn_key.split('_')
    conn = st.session_state.db_connections[conn_key]

    return {
        'conn': conn,
        'type': db_info[0],
        'host': db_info[1],
        'port': db_info[2],
        'user': db_info[3],
        'database': db_info[4],
        'key': conn_key
    }