from utils.ui import setup_ui, show_connection_ui, show_query_ui
from utils.database import handle_connections, get_active_connection_info, init_session_state


def main():
    # Initialize session state
    init_session_state()

    # Setup page configuration and UI
    setup_ui()

    # Handle any connection logic
    handle_connections()

    # Show connection management in sidebar
    show_connection_ui()

    # Get active connection info if exists
    conn_info = get_active_connection_info()

    # Show main query interface if connected
    show_query_ui(conn_info)


if __name__ == "__main__":
    main()