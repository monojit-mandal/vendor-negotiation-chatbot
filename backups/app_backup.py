import streamlit as st
from streamlit_chat import message
import duckdb
import utils_database as udb
import utils
import utils_model as um
import polars as pl
import os

def login_page():
    st.header('Login')
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

def material_selection_page():
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
        .center-button {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 50vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    # TODO: Keep material name instead of material ID
    list_materials = [f'Material - {mat}' for mat in udb.list_materials(st.session_state.user_id)]
    option = st.selectbox(
        "Please pick a Material",
        list_materials,
        placeholder="Choose an option"
    )
    # TODO: Remove string splits
    st.session_state.material_id = int(option.split(' - ')[-1])

def main():

    # Set custom page config and styles
    # st.set_page_config(page_title="Tailend Supplier Negotiation Chatbot", layout="wide")

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
        .center-button {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 50vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "step" not in st.session_state:
        st.session_state.step = 0

    if "sessions" not in st.session_state:
        st.session_state.sessions = {}

    if "current_session" not in st.session_state:
        st.session_state.current_session = "Session 1"
    
    if "offer_selected" not in st.session_state:
        st.session_state.offer_selected = False
    
    if "supplier_offer" not in st.session_state:
        st.session_state.supplier_offer = None
    
    if "supplier_final_offer" not in st.session_state:
        st.session_state.supplier_final_offer = None

    # Header with user icon and logout option
    with st.container():
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    # Sidebar for session selection
    with st.sidebar:
        st.html(f'Negotiation for material: {st.session_state.material_id}')
        st.title("Session History")
        session_names = list(st.session_state.sessions.keys())
        # TODO: Session to load from session history
        selected_session = st.selectbox("Select a session:", ['Session - 1','Session - 2'], index=session_names.index(st.session_state.current_session) if session_names else 0, key="session_selector")
        
        if st.button("Load Session"):
            st.session_state.current_session = selected_session
            st.session_state.messages = st.session_state.sessions.get(selected_session, [])
        
        if st.button("Start New Session"):
            new_session_name = f"Session {len(session_names) + 1}"
            st.session_state.sessions[new_session_name] = []
            st.session_state.current_session = new_session_name
            st.session_state.messages = []

    # st.title("Tailend Supplier Negotiation Chatbot")

    base_offer = um.get_base_offer(
        user_id = st.session_state.user_id,
        material_id = st.session_state.material_id
    )
    material = udb.get_material_info(
        material_id=st.session_state.material_id
    )

    actual = utils.ContractActual(
        quantity=material['quantity'],
        price_per_unit=material['price_per_unit']
    )
    MIN_LEVERS = {
        'price_per_unit':material['min_price_per_unit'],
        'quantity': material['min_quantity']
    }
    MAX_LEVERS = {
        'price_per_unit':material['max_price_per_unit'],
        'quantity': material['max_quantity']
    }
    response = um.generate_offer(
        base_offer = base_offer,
        min_levers = MIN_LEVERS,
        max_levers = MAX_LEVERS,
        step = 1,
        TCO_hike_threshold_pct = 40,
        supplier_offer = None
    )

    

    # Display start button before chat begins
    if st.session_state.step == 0:
        st.markdown("<div class='center-button'>", unsafe_allow_html=True)
        if st.button("Start Negotiation"):
            st.session_state.step = 1
            st.session_state.messages.append(
                {
                    "content": "Welcome to Tailend Supplier Negotiation Chatbot! Let's get started!", 
                    "sender": 'bot'
                }
            )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Display chat messages from history
    for msg in st.session_state.messages:
        message(message = msg["content"], is_user = True if msg["sender"] != 'bot' else False)
    
    if st.session_state.step == -1:
        if st.button("Accept"):
            st.session_state.messages.append(
                {
                    'sender': 'bot',
                    'content': "Thanks for confirming the offer. Have a great day ahead."
                }
            )
            st.session_state.step = 100
            
    # Step 2: Ask the first question
    if st.session_state.step == 1:
        st.html(f'Please select an offer from any of the offers below or negotiate')
        options = [
            um.offer_to_text(response['offers'][0]),
            um.offer_to_text(response['offers'][1]),
            um.offer_to_text(response['offers'][2]),
        ]
        # topic = st.radio("Choose a topic:", options, key="topic")
        for option in options:
            if st.button(option):
                st.session_state.topic = option
                st.session_state.offer_selected = True
                
        if st.session_state.offer_selected:
            if st.button("Next"):
                st.session_state.messages.append(
                    {
                        "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.topic}", 
                        "sender": 'bot'
                    }
                )
                st.session_state.step = -1
            if st.button("Reset"):
                st.session_state.topic = None
                st.session_state.offer_selected = False
        else:
            if st.button("Negotiate"):
                st.session_state.messages.append(
                    {
                        "content": f"I want to negotiate.", 
                        "sender": 'user'
                    }
                )
                st.session_state.step += 1

    # Step 3: Follow-up question based on the chosen topic
    elif st.session_state.step == 2:
        st.html(f'Please share your offer based on the levers input')
        col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
        with col1:
            unit_price = st.number_input(
                "Unit Price ($/unit)", 
                value = 0.0, 
                step=0.1, 
                format="%.2f"
            )
        with col2:
            quantity = st.number_input(
                "Quantity (in unit)", 
                value = 1, 
                min_value = 1, 
                max_value = 100000000, 
                step = 1
            )
        with col3:
            payment_term = st.selectbox(
                "Payment Term", 
                [
                    'NET10','NET20','NET30','NET40',
                    'NET50','NET60','NET70','NET80','NET90'
                ]
            )
        with col4:
            delivery_days = st.number_input(
                "Delivery Time (in Days)", 
                value = 1, 
                min_value = 1, 
                max_value = 100, 
                step = 1
            )
        with col5:
            contract_years = st.number_input(
                "Contract Period (in Years)", 
                value = 1,
                min_value = 1,
                max_value = 10, 
                step = 1
            )
        with col6:
            warranty = st.number_input(
                "Contract Period (in Years)", 
                value = 1, 
                min_value = 1,
                max_value = 100, 
                step = 1
            )
        with col7:
            incoterm = st.selectbox(
                "Payment Term", 
                [
                    'EXW','FCA','FAS','FOB','CFR',
                    'CIF','CPT','CIP','DAP','DPU','DDP'
                ]
            )
        st.session_state.supplier_offer = utils.ContractOffer(
            price_per_unit=unit_price,
            quantity=quantity,
            payment_term=utils.format_payment_term(payment_term),
            delivery_timeline=delivery_days,
            contract_period=contract_years,
            warranty=warranty,
            incoterms=utils.format_incoterm(incoterm)
        )
        offer = utils.ContractActual(
            price_per_unit=unit_price,
            quantity=quantity,
            payment_term=utils.format_payment_term(payment_term).term,
            delivery_timeline=delivery_days,
            contract_period=contract_years,
            warranty=warranty,
            incoterms=utils.format_incoterm(incoterm)
        )
        if st.button("Next"):
            st.session_state.messages.append(
                {
                    "content": f'''As per your response your offer: {um.offer_to_text(offer)}''', 
                    "sender": 'user'
                }
            )
            st.session_state.step += 1
            print(st.session_state.step)
    elif st.session_state.step == 3:
        print(True)
        response = um.generate_offer(
            base_offer = base_offer,
            min_levers = MIN_LEVERS,
            max_levers = MAX_LEVERS,
            step = 2,
            TCO_hike_threshold_pct = 40,
            supplier_offer = st.session_state.supplier_offer
        )
        if response['status'] == 'accepted':
            print(True)
            st.session_state.messages.append(
                {
                    'sender':'bot',
                    'content':"We are happy to share that we have accepted your offer. Let's make the deal"
                }
            )
            if st.button("Next"):
                st.session_state.step = 100
        else:
            st.html(f'Please select an offer from any of the offers below or negotiate')
            options = [
                um.offer_to_text(response['offers'][0]),
                um.offer_to_text(response['offers'][1]),
                um.offer_to_text(response['offers'][2]),
            ]
            # topic = st.radio("Choose a topic:", options, key="topic")
            for option in options:
                if st.button(option):
                    st.session_state.topic = option
                    st.session_state.offer_selected = True
                    
            if st.session_state.offer_selected:
                if st.button("Next"):
                    st.session_state.messages.append(
                        {
                            "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.topic}", 
                            "sender": 'bot'
                        }
                    )
                    st.session_state.step = -1
                if st.button("Reset"):
                    st.session_state.topic = None
                    st.session_state.offer_selected = False
            else:
                if st.button("Negotiate"):
                    st.session_state.messages.append(
                        {
                            "content": f"I want to negotiate further", 
                            "sender": 'user'
                        }
                    )
                    st.session_state.step += 1

    elif st.session_state.step == 4:
        print('We are in step 4')
        col1,col2,col3 = st.columns(3)
        with col1:
            priority_1 = st.selectbox(
                "Priority Lever 1", 
                [
                    'Unit Price','Quantity','Payment Term','Incoterms',
                    'Warranty','Delivery Time','Contract Length'
                ]
            )
        with col2:
            priority_2 = st.selectbox(
                "Priority Lever 2", 
                [
                    'Unit Price','Quantity','Payment Term','Incoterms',
                    'Warranty','Delivery Time','Contract Length'
                ]
            )
        with col3:
            priority_3 = st.selectbox(
                "Priority Lever 3", 
                [
                    'Unit Price','Quantity','Payment Term','Incoterms',
                    'Warranty','Delivery Time','Contract Length'
                ]
            )
        if st.button("Next"):
            st.session_state.messages.append(
                {
                    "content": f'''As per the response your top priority levers are : 1. {priority_1}, 2. {priority_2}, 3. {priority_3}''', 
                    "sender": 'user'
                }
            )
            st.session_state.step += 1
    
    elif st.session_state.step == 5:
        response = um.generate_offer(
            base_offer = base_offer,
            min_levers = MIN_LEVERS,
            max_levers = MAX_LEVERS,
            step = 3,
            TCO_hike_threshold_pct = 40
        )
        st.html(f'Please select an offer from any of the offers below or negotiate')
        options = [
            um.offer_to_text(response['offers'][0]),
            um.offer_to_text(response['offers'][1]),
            um.offer_to_text(response['offers'][2]),
        ]
        # topic = st.radio("Choose a topic:", options, key="topic")
        for option in options:
            if st.button(option):
                st.session_state.topic = option
                st.session_state.offer_selected = True
                
        if st.session_state.offer_selected:
            if st.button("Next"):
                st.session_state.messages.append(
                    {
                        "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.topic}", 
                        "sender": 'bot'
                    }
                )
                st.session_state.step = -1
            if st.button("Reset"):
                st.session_state.topic = None
                st.session_state.offer_selected = False
        else:
            if st.button("Negotiate"):
                st.session_state.messages.append(
                    {
                        "content": f"I am not okay with this offer. I want to negotiate further", 
                        "sender": 'user'
                    }
                )
                st.session_state.step += 1
    
    elif st.session_state.step == 6:
        st.session_state.supplier_final_offer = st.chat_input('Please share your final offer')
        if st.session_state.supplier_final_offer != None:
            st.session_state.step += 1
    elif st.session_state.step == 7:
        df_offers = pl.read_csv('data/sample_offers.csv')
        model = um.AzureChatOpenAI(
            deployment_name= "gpt-4o",
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2023-09-15-preview",
            azure_endpoint="https://acsstscdamoai02.openai.azure.com/"
        )
        supplier_response = utils.extract_levers_from_text(
            offer_text=st.session_state.supplier_final_offer,
            model=model,
            example_data=df_offers
        )
        st.session_state.supplier_offer = utils.ContractOffer().load_from_data(supplier_response)
        response = um.generate_offer(
            base_offer = base_offer,
            min_levers = MIN_LEVERS,
            max_levers = MAX_LEVERS,
            step = 3,
            TCO_hike_threshold_pct = 40,
            supplier_offer = st.session_state.supplier_offer
        )
        if response['status'] == 'accepted':
            st.session_state.messages.append(
                {
                    'sender':'bot',
                    'content':"We are happy to share that we have accepted your offer. Let's make the deal"
                }
            )
            st.session_state.step = 6
        else:
            st.session_state.messages.append(
                {
                    'sender':'bot',
                    'content':"Thanks for sharing your offer. We have assigned a ticket for you. One of our experts will reach out to you soon"
                }
            )
            st.html('Sorry, we could make the deal. However we will assign a ticket for you to connect with Expert. Please select Confirm button to confirm')
            if st.button('Confirm'):
                st.session_state.step = 100
    # Last Step: Restart option
    elif st.session_state.step == 100:
        if st.button("Restart Chat"):
            st.session_state.sessions[st.session_state.current_session] = st.session_state.messages
            st.session_state.step = 0
            st.session_state.messages = []

if __name__ == "__main__":
    st.title("Tailend Supplier Negotiation Chatbot")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "material_id" not in st.session_state:
        st.session_state.material_id = None
    
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.material_id == None:
            material_selection_page()
        else:
            main()
