import duckdb
import datetime

# Connect to DuckDB and create tables if they don’t exist
db_connection = duckdb.connect("chatbot.db")  # This will create a local database file named "chatbot.db"

# Create sequences for auto-incrementing IDs
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1;")
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS session_id_seq START 1;")
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS message_id_seq START 1;")

# Define and create tables
db_connection.execute("""
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER DEFAULT nextval('user_id_seq') PRIMARY KEY,
    username VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

db_connection.execute("""
CREATE TABLE IF NOT EXISTS Sessions (
    session_id INTEGER DEFAULT nextval('session_id_seq') PRIMARY KEY,
    user_id INTEGER,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
""")

db_connection.execute("""
CREATE TABLE IF NOT EXISTS Messages (
    message_id INTEGER DEFAULT nextval('message_id_seq') PRIMARY KEY,
    session_id INTEGER,
    sender VARCHAR CHECK (sender IN ('user', 'bot')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES Sessions(session_id)
);
""")

db_connection.close()

# Function to add a new user
def add_user(username,db_connection):
    db_connection.execute("INSERT INTO Users (username) VALUES (?)", (username,))
    return db_connection.execute("SELECT user_id FROM Users WHERE username = ?", (username,)).fetchone()[0]

# Function to start a new session for a user
def start_session(user_id,db_connection):
    db_connection.execute("INSERT INTO Sessions (user_id) VALUES (?)", (user_id,))
    return db_connection.execute("SELECT session_id FROM Sessions WHERE user_id = ? ORDER BY start_time DESC LIMIT 1", (user_id,)).fetchone()[0]

# Function to add a message to a session
def add_message(session_id, sender, content,db_connection):
    db_connection.execute("INSERT INTO Messages (session_id, sender, content) VALUES (?, ?, ?)", (session_id, sender, content))

# Function to end a session
def end_session(session_id,db_connection):
    end_time = datetime.datetime.now()
    db_connection.execute("UPDATE Sessions SET end_time = ? WHERE session_id = ?", (end_time, session_id))

# Function to list user's previous sessions
def list_sessions(user_id,db_connection):
    sessions = db_connection.execute("SELECT session_id, start_time, end_time FROM Sessions WHERE user_id = ?", (user_id,)).fetchall()
    return sessions

# Function to display messages in an existing session
def display_previous_messages(session_id,db_connection):
    messages = db_connection.execute("SELECT sender, content, timestamp FROM Messages WHERE session_id = ? ORDER BY timestamp", (session_id,)).fetchall()
    for sender, content, timestamp in messages:
        print(f"[{timestamp}] {sender.capitalize()}: {content}")

def clear_previous_conversations(user_id,session_id,db_connection):
    return None

def clear_database(db_connection):
    return None