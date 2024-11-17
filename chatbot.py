import duckdb
import datetime
import utils_model
import utils_database


# Main chatbot function to interact with the user
def chatbot():
    print("Welcome to Vendor Negotiation Chatbot!")
    username = input("Enter your username: ")
    db_connection = duckdb.connect("chatbot.db")
    # Check if user exists, else add user
    user_id = db_connection.execute("SELECT user_id FROM Users WHERE username = ?", (username,)).fetchone()
    if not user_id:
        user_id = utils_database.add_user(username,db_connection)
    else:
        user_id = user_id[0]
    
    # Check if the user wants to continue an existing session or start a new one
    sessions = utils_database.list_sessions(user_id,db_connection)
    if sessions:
        print("\nYour previous sessions:")
        for i, (session_id, start_time, end_time) in enumerate(sessions, start=1):
            print(f"{i}. Session ID: {session_id} | Start: {start_time} | End: {end_time or 'Ongoing'}")
        
        choice = input("Enter the session number to continue, or type 'new' to start a new session: ").strip()
        if choice.lower() == 'new':
            session_id = utils_database.start_session(user_id,db_connection)
            print(f"\nStarted a new session (ID: {session_id}). Type 'exit' to end the session.")
        else:
            try:
                session_index = int(choice) - 1
                session_id = sessions[session_index][0]
                print(f"\nContinuing session (ID: {session_id}). Type 'exit' to end the session.")
                utils_database.display_previous_messages(session_id,db_connection)
            except (ValueError, IndexError):
                print("Invalid choice. Starting a new session.")
                session_id = utils_database.start_session(user_id,db_connection)
    else:
        session_id = utils_database.start_session(user_id,db_connection)
        print(f"\nStarted a new session (ID: {session_id}). Type 'exit' to end the session.")
    
    while True:
        # Get user input
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        # Store user message
        utils_database.add_message(session_id, 'user', user_input,db_connection)
        
        # Generate bot response (simple echo response here; replace with a real model if needed)
        bot_response = utils_model.chatbot_response(
            user_id=user_id,
            session_id=session_id,
            input_message=user_input
        )
        print(f"Bot: {bot_response}")
        
        # Store assistant's response
        utils_database.add_message(session_id, 'bot', bot_response,db_connection)
    
    # End the session
    utils_database.end_session(session_id,db_connection)
    print("Session ended.")

    db_connection.close()

# Run the chatbot
if __name__ == "__main__":
    chatbot()
