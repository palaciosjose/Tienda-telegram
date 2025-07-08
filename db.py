import sqlite3
import atexit
import files

_connection = None

def get_db_connection():
    """Return a cached connection to the main database."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(files.main_db, check_same_thread=False)
    else:
        try:
            _connection.cursor()
        except sqlite3.ProgrammingError:
            _connection = sqlite3.connect(files.main_db, check_same_thread=False)
    return _connection

def close_connection():
    """Close the cached database connection if it exists."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None

atexit.register(close_connection)
