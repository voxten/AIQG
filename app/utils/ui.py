import streamlit as st
import time
import pandas as pd
from utils.database import get_db_connection, run_sql, get_schema, SUPPORTED_DB_TYPES
from utils.query import generate_sql, explain_query, prepare_results


def setup_ui():
    """Setup the main UI configuration"""
    st.set_page_config(layout="wide", page_title="Database Query Tool")


def show_connection_ui():
    """Show connection management UI in sidebar"""
    with st.sidebar:
        st.title("🔌 Database Connections")
        st.markdown("---")

        with st.expander("➕ New Connection", expanded=True):
            db_type = st.selectbox(
                "Database Type",
                list(SUPPORTED_DB_TYPES.keys()),
                format_func=lambda x: f"{SUPPORTED_DB_TYPES[x]['icon']} {x}"
            )

            host = st.text_input(
                "Host",
                value=SUPPORTED_DB_TYPES[db_type]["default_host"],
                help="Database server hostname or IP address"
            )

            col1, col2 = st.columns(2)
            with col1:
                port = st.number_input(
                    "Port",
                    value=st.session_state.SUPPORTED_DB_TYPES[db_type]["port"],
                    min_value=1,
                    max_value=65535
                )
            with col2:
                database = st.text_input(
                    "Database",
                    value="",
                    placeholder="Database name"
                )

            user = st.text_input("Username", value="")
            password = st.text_input("Password", type="password")

            if st.button("Connect", type="primary", use_container_width=True):
                with st.spinner("Connecting..."):
                    conn = get_db_connection(db_type, host, port, user, password, database)
                    if conn:
                        st.toast("✅ Connection established!", icon="✅")
                        time.sleep(1)
                        st.rerun()

        st.markdown("---")
        st.subheader("🌐 Active Connections")

        if not st.session_state.db_connections:
            st.caption("No active connections")
        else:
            for idx, (key, conn) in enumerate(st.session_state.db_connections.items()):
                db_info = key.split('_')
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{db_info[0]}** @ {db_info[1]}")
                    st.caption(f"Database: {db_info[-1]}")
                with col2:
                    if st.button("⚡", key=f"use_{idx}", help="Use this connection"):
                        st.session_state.active_connection = key
                        st.rerun()

        st.markdown("---")
        if st.button("❌ Disconnect All", use_container_width=True):
            for conn in st.session_state.db_connections.values():
                try:
                    conn.close()
                except:
                    pass
            st.session_state.db_connections = {}
            st.session_state.active_connection = None
            st.rerun()


def show_query_ui(conn_info):
    """Show the main query interface"""
    if not conn_info:
        st.info("👈 Connect to a database using the sidebar to get started")
        st.markdown("""
        ### How to use this tool:
        1. Open the sidebar and enter your database connection details
        2. Click "Connect" to establish a connection
        3. Use either:
           - **Natural Language tab**: Ask questions in plain English
           - **SQL Editor tab**: Write and execute custom SQL queries
        """)
        return

    # Display connection info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{conn_info['type']} Connection")
    with col2:
        if st.button("🔄 Refresh Schema", help="Refresh database schema"):
            st.session_state.schema = get_schema(conn_info['conn'], conn_info['type'])
            st.rerun()

    st.caption(f"Connected to: {conn_info['host']}:{conn_info['port']} | Database: {conn_info['database']}")

    # Query tabs
    tab1, tab2 = st.tabs(["Natural Language Query", "SQL Editor"])

    with tab1:
        show_natural_language_ui(conn_info)

    with tab2:
        show_sql_editor_ui(conn_info)

    # Schema explorer
    with st.expander("📚 Database Schema Explorer", expanded=False):
        st.text(st.session_state.schema)


def show_natural_language_ui(conn_info):
    """Show natural language query interface"""
    st.subheader("Ask in Plain English")
    user_query = st.text_area(
        "Enter your question:",
        placeholder="e.g., 'Show me top 5 customers by total purchases'",
        height=100
    )

    if user_query:
        col1, col2 = st.columns([1, 1])
        with col1:
            generate_btn = st.button("🔧 Generate SQL", use_container_width=True)
        with col2:
            execute_btn = st.button("▶️ Execute Query", type="primary", use_container_width=True)

        if generate_btn:
            with st.spinner("Generating SQL..."):
                sql = generate_sql(user_query, st.session_state.schema)
                st.session_state.generated_sql = sql  # Store the generated SQL in session state

        if 'generated_sql' in st.session_state:
            st.markdown("### Generated SQL")
            st.code(st.session_state.generated_sql, language="sql")

        if execute_btn and 'generated_sql' in st.session_state:
            with st.spinner("Executing..."):
                columns, results = run_sql(conn_info['conn'], st.session_state.generated_sql, conn_info['type'])

            if columns:
                st.success("Query executed successfully!")
                df, csv = prepare_results(columns, results)
                st.dataframe(df, use_container_width=True)

                st.download_button(
                    "💾 Download as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.error(f"Error: {results}")


def show_sql_editor_ui(conn_info):
    """Show SQL editor interface"""
    st.subheader("Run Custom SQL")
    custom_sql = st.text_area(
        "Enter SQL query:",
        height=200,
        placeholder="SELECT * FROM customers LIMIT 10;"
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        execute_btn = st.button("▶️ Execute", type="primary", use_container_width=True)
    with col2:
        explain_btn = st.button("🔍 Explain Query", use_container_width=True)

    if execute_btn and custom_sql:
        with st.spinner("Executing..."):
            columns, results = run_sql(conn_info['conn'], custom_sql, conn_info['type'])

        if columns:
            st.success("Query executed successfully!")
            df, csv = prepare_results(columns, results)
            st.dataframe(df, use_container_width=True)

            st.download_button(
                "💾 Download as CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            if "successfully" in results:
                st.success(results)
            else:
                st.error(f"Error: {results}")

    if explain_btn and custom_sql:
        with st.spinner("Analyzing query..."):
            explanation = explain_query(custom_sql, st.session_state.schema)
            st.markdown("### Query Explanation")
            st.write(explanation)
