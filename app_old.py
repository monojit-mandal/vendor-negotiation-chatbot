# UI packages
import streamlit as st
from streamlit_chat import message
import duckdb
import utils_database as udb
import utils
import utils_model as um

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username and password:  # Simple authentication logic
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Please enter both username and password.")

    # Check if user exists, else add user
    user_id = udb.get_user_id(username=username)
    if not user_id:
        st.session_state.user_id = udb.add_user(username)
    else:
        st.session_state.user_id = user_id[0]

def main():
    # Set custom page config and styles
    st.set_page_config(page_title="Supplier Negotiation Chatbot", layout="wide")

    st.markdown(
        """
        <style>
        body {
            background-color: #F5F5FF;
        }
        .stSidebar {
            background-color: #EDE7F6;
        }
        .stButton > button {
            background-color: #D1C4E9;
            color: black;
            border-radius: 8px;
        }
        .stButton > button:hover {
            background-color: #B39DDB;
        }
        .css-1cpxqw2 { /* Chat bubbles */
            background-color: #EDE7F6 !important;
        }
        .css-1ynm9l1 { /* User messages */
            background-color: #D1C4E9 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "step" not in st.session_state:
        st.session_state.step = 0

    if "sessions" not in st.session_state:
        st.session_state.sessions = {}

    # if "current_session" not in st.session_state:
    #     st.session_state.current_session = 1
    
    if "offer_selected" not in st.session_state:
        st.session_state.offer_selected = False
    
    if "topic" not in st.session_state:
        st.session_state.topic = False
    
    if "material_id" not in st.session_state:
        st.session_state.material_id = None
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "appear_start_button" not in st.session_state:
        st.session_state.appear_start_button = False
    
    # Header with user icon and logout option
    with st.container():
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    if st.session_state.material_id == None:
        list_materials = udb.list_materials(st.session_state.user_id)
        # print(list_materials)
        option = st.selectbox(
            "Please pick a Material",
            list_materials,
            placeholder="Choose an option"
        )
        st.session_state.material_id = option
    else:
        # Sidebar for session selection
        with st.sidebar:
            st.html(f'Negotiation for material: {st.session_state.material_id}')
            st.title("Previous Sessions")
            list_sessions = udb.list_sessions(user_id=st.session_state.user_id)
            if len(list_sessions) == 0:
                st.session_state.session_id = udb.start_session(user_id=st.session_state.user_id)
                print(True)
            else:
                st.session_state.session_id = list_sessions[0][0]
            session_names = [session[0] for session in list_sessions]

            # st.session_state.messages = udb.pull_message_history(st.session_state.session_id)
            # if len(st.session_state.messages) != 0:
            #     st.session_state.step = st.session_state.messages[0]['step']
            # print(st.session_state.messages)

            selected_session = st.selectbox("Select a session:", session_names, key="session_selector")

            if st.button("Switch Session"):
                st.session_state.messages = udb.pull_message_history(selected_session)

            if st.button("Start New Session"):
                st.session_state.step = 0
                st.session_state.session_id = udb.start_session(user_id=st.session_state.user_id)
                st.session_state.messages = []

        st.title("Supplier Negotiation Chatbot")

        # Base offer------------------------------------------------------
        # base_offer = um.get_base_offer(
        #     user_id = st.session_state.user_id,
        #     material_id = st.session_state.material_id
        # )
        # material = udb.get_material_info(
        #     material_id=st.session_state.material_id
        # )

        # actual = utils.ContractActual(
        #     quantity=material['quantity'],
        #     price_per_unit=material['price_per_unit']
        # )
        # MIN_LEVERS = {
        #     'price_per_unit':material['min_price_per_unit'],
        #     'quantity': material['min_quantity']
        # }
        # MAX_LEVERS = {
        #     'price_per_unit':material['max_price_per_unit'],
        #     'quantity': material['max_quantity']
        # }
        # response = um.generate_offer(
        #     base_offer = base_offer,
        #     min_levers = MIN_LEVERS,
        #     max_levers = MAX_LEVERS,
        #     step = 1,
        #     TCO_hike_threshold_pct = 40,
        #     supplier_offer = None
        # )

        # Display chat messages from history
        for msg in st.session_state.messages:
            message(message=msg["content"], is_user=True if msg["user"] != 'bot' else False)

        # Display start button before chat begins
        if st.session_state.step == 0:
            print('We are in step 0')
            st.session_state.messages.append(
                {
                    'user':'bot',
                    'content':"Welcome to Tailend Negotiation Chatbot! Let's get started!"
                }
            )
            for msg in st.session_state.messages:
                message(message=msg["content"], is_user=True if msg["user"] != 'bot' else False)
            print(st.session_state.messages)
        
        
        
        # Step 2: Ask the first question
        if st.session_state.step == 1:
            # options = [
            #     um.offer_to_text(response['offers'][0]),
            #     um.offer_to_text(response['offers'][1]),
            #     um.offer_to_text(response['offers'][2]),
            # ]
            # # topic = st.radio("Choose a topic:", options, key="topic")
            # columns = st.columns(len(options))
            # # Display options side by side
            # for col,option in zip(columns,options):
            #     with col:
            #         if st.button(option):
            #             st.session_state.topic = option
            #             st.session_state.offer_selected = True

            if st.session_state.offer_selected == True:
                if st.button("Accept"):
                    st.session_state.messages.append(
                        {
                            "content": f"""
                            Thanks for accepting the offer. 
                            Please check the offer details:
                            {st.session_state.topic}""", 
                            "user": True
                        }
                    )
                    # st.session_state.messages.append({"content": "Let's dive deeper.", "is_user": False})
                    # st.session_state.step += 1
            if st.session_state.offer_selected == False:
                if st.button("Negotiate"):
                    st.session_state.messages.append({"content": f"You chose to negotiate", "user": 'bot'})
                    # st.session_state.messages.append({"content": "Please ", "user": 'bot'})
                    st.session_state.step += 1

        # Step 3: Follow-up question based on the chosen topic
        elif st.session_state.step == 2:
            selected_topic = st.session_state.messages[-2]["content"].split("You chose ")[1].strip('.').lower()

            if selected_topic == "technology":
                options = ["AI", "Blockchain", "IoT"]
            elif selected_topic == "health":
                options = ["Mental Health", "Nutrition", "Exercise"]
            elif selected_topic == "education":
                options = ["Online Learning", "Traditional Education", "Skill Development"]
            elif selected_topic == "finance":
                options = ["Investing", "Budgeting", "Saving"]
            
            sub_topic = st.multiselect("Select one or more sub-topics:", options, key="sub_topic")
            if st.button("Next"):
                st.session_state.messages.append({"content": f"You chose sub-topics: {', '.join(sub_topic)}.", "is_user": True})
                st.session_state.messages.append({"content": "Thank you for your responses! Here's what we've discussed today:", "is_user": False})
                for msg in st.session_state.messages:
                    if msg["is_user"]:
                        st.session_state.messages.append({"content": msg["content"], "is_user": False})
                st.session_state.messages.append({"content": "Would you like to restart?", "is_user": False})
                st.session_state.step += 1

        # Step 4: Restart option
        elif st.session_state.step == 3:
            if st.button("Restart Chat"):
                st.session_state.sessions[st.session_state.current_session] = st.session_state.messages
                st.session_state.step = 0
                st.session_state.messages = []

if __name__ == "__main__":
    # udb.clear_sessions()
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if not st.session_state.logged_in:
        login_page()
    else:
        main()
