import streamlit as st
from streamlit_chat import message
import duckdb
import utils_database as udb
import utils
import utils_model as um
import polars as pl
import os
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import polars as pl
import random
from dotenv import load_dotenv
load_dotenv()
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage,HumanMessage
from langchain.output_parsers import ResponseSchema,StructuredOutputParser
from enum import Enum
import datetime as dt
from streamlit_option_menu import option_menu
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, AgGridTheme
from typing import List, Dict, Tuple

class ConversationState(Enum):
    DEFAULT = 0
    FIRST_OFFER = 1
    SUPPLIER_LEVERS_INPUT = 2
    SECOND_OFFER = 3
    SUPPLIER_LEVER_PRIORITY = 4
    THIRD_OFFER = 5
    SUPPLIER_FINAL_OFFER = 6
    FINAL_OFFER = 7
    OFFER_ACCEPTED = 8
    RESTART = 9
    WELCOME_PAGE = 10
    NEGOTIATION_CONFIRMATION = 11
    SUPPLER_STATUS = 12
    NONE = 13
    # SESSION_HISTORY = 11

def login_page():
    st.markdown(
        """
        <style>
        /* Center the login form */
        .login-container {
            width: 700px;
            padding: 30px;
            background-color: #f4f4f4;
            border-radius: 12px;
            text-align: center;
            margin: auto;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            position: relative;
        }
        /* Logo styling inside the container */
        .logo-container {
            position: absolute;
            top: -40px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff;
            padding: 10px;
            border-radius: 50%;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }
        .login-container h1 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #333;
        }
        /* Style the login button */
        .stButton {
            display: flex;
            justify-content: center;
        }
        /* Style the login button */
        .stButton > button {
            background-color: #A100FF !important; /* Purple */
            color: white !important;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 16px;
            border: none;
        }
        .stButton > button:hover {
            background-color: #9932CC !important; /* Lighter Purple on Hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Login container with logo inside
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Company Logo
    st.markdown('<div class="logo-container"><img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png" width="60"></div>', unsafe_allow_html=True)
    # Login Title
    st.markdown("<h4 align='center'><b>Login</b></h4>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    
    if st.button("Login"):
        if username and password:  # Simple authentication logic
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Please enter both username and password.")
        st.rerun()

    # Check if user exists, else add user
    user_id = udb.get_user_id(username=username)
    if not user_id:
        st.session_state.user_id = udb.add_user(
            username = username,
            role = 'supplier'
        )
    else:
        st.session_state.user_id = user_id[0]
    st.markdown("</div>", unsafe_allow_html=True)

def ag_grid_configured(data:pl.DataFrame,key:str,editable_columns:List[str]):
    data = data.to_pandas()
    gob = GridOptionsBuilder.from_dataframe(data)
    for column in data.columns:
        if column in editable_columns:
            gob.configure_column(column, filter=True,editable = True)
    gridOptions = gob.build()
    grid_return = AgGrid(
        data = data,
        gridOptions=gridOptions, 
        update_mode=GridUpdateMode.MODEL_CHANGED,
        theme=AgGridTheme.ALPINE,
        reload_data=True,
        key = key
    )
    return pl.DataFrame(grid_return['data'])

def show_suppliers_table():
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f4f4f4;
            }
        </style>
    """, unsafe_allow_html=True)
    # st.markdown("<h5 style='text-align: center;'>Suppliers</h5>", unsafe_allow_html=True)
    data = udb.pull_all_suplliers()
    data = data.rename(
        {
            'user_id':'User ID',
            'username':'Username',
            'role':'Role',
            'created_at':'Created Timestamp'
        }
    )
    data = ag_grid_configured(
        data=data,
        key = 'suppliers',
        editable_columns=[]
    )
    # data = udb.pull_all_suplliers()
    # data = data.with_columns(pl.col('created_at').cast(pl.Date))
    # columns = data.columns
    # st.markdown("<h6 style='text-align: center;'>Suppliers</h6>", unsafe_allow_html=True)
    # cols = st.columns(len(columns))
    # for i in range(len(cols)):
    #     cols[i].write(f'*{columns[i]}*')

    # for row in data.rows(named = True):
    #     cols = st.columns(len(columns))
    #     for i in range(len(columns)):
    #         cols[i].write(row[columns[i]])

def show_materials_table():
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f4f4f4;
            }
        </style>
    """, unsafe_allow_html=True)
    # st.markdown("<h5 style='text-align: center;'>Materials</h5>", unsafe_allow_html=True)
    data = udb.pull_all_materials()
    data = data.with_columns(
        [
            pl.col('price_per_unit').round().alias('price_per_unit'),
            pl.col('min_price_per_unit').round().alias('min_price_per_unit'),
            pl.col('max_price_per_unit').round().alias('max_price_per_unit'),
            pl.col('created_at').cast(pl.Date)
        ]
    )
    data = data.rename(
        {
            'material_id':'Material ID',
            'description': 'Material Description',
            'quantity': 'Quantity',
            'price_per_unit':'Unit Price ($)',
            'min_quantity': 'Min Quantity',
            'max_quantity': 'Max Quantity',
            'min_price_per_unit': 'Min Unit Price ($)',
            'max_price_per_unit': 'Max Unit Price ($)',
            'created_at': 'Created Timestamp'
        }
    )
    data = ag_grid_configured(
        data=data,
        key = 'suppliers',
        editable_columns=[
            'Min Quantity','Max Quantity',
            'Min Unit Price ($)','Min Unit Price ($)'
        ]
    )
    # columns = data.columns
    # st.markdown("<h6 style='text-align: center;'>Materials</h6>", unsafe_allow_html=True)
    # cols = st.columns(len(columns))
    # for i in range(len(cols)):
    #     cols[i].write(f'*{columns[i]}*')

    # for row in data.rows(named = True):
    #     cols = st.columns(len(columns))
    #     for i in range(len(columns)):
    #         cols[i].write(row[columns[i]])

def show_contracts_table():
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f4f4f4;
            }
        </style>
    """, unsafe_allow_html=True)
    # st.markdown("<h6 style='text-align: center;'>Contracts</h6>", unsafe_allow_html=True)
    data = udb.pull_all_contracts()
    data = data.with_columns(
        [
            pl.col('created_at').cast(pl.Date)
        ]
    )
    data = data.rename(
        {
            'contract_id':'Contract ID',
            'user_id':'User ID',
            'material_id':'Material ID',
            'contract_details':'Contract Description',
            'price_per_unit':'Unit Price ($)',
            'quantity':'Quantity',
            'bundling_unit':'Bundling Unit',
            'bundling_amount':'Bundling Amount ($)',
            'bundling_discount':'Bundling Discount (%)',
            'payment_term':'Payment Term',
            'delivery_timeline':'Delivery Time (Days)',
            'contract_period':'Contract Length (Years)',
            'contract_inflation':'Contract Inflation (%)',
            'rebates_threshold_unit':'Rebate Volume',
            'rebates_discount':'Rebates Discount (%)',
            'warranty':'Warranty (Years)',
            'incoterms':'Incoterms',
            'created_at':'Created Timestamp',
            'expiry_tmstp':'Expiry Timestamp'
        }
    )
    data = ag_grid_configured(
        data=data,
        key = 'suppliers',
        editable_columns=[]
    )
    # columns = data.columns
    # st.markdown("<h6 style='text-align: center;'>Contracts</h6>", unsafe_allow_html=True)
    # cols = st.columns(len(columns))
    # for i in range(len(cols)):
    #     cols[i].write(f'*{columns[i]}*')

    # for row in data.rows(named = True):
    #     cols = st.columns(len(columns))
    #     for i in range(len(columns)):
    #         cols[i].write(row[columns[i]])

def show_session_history_table_admin():
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f4f4f4;
            }
        </style>
    """, unsafe_allow_html=True)
    # data = [
    #     {"ID": 1, "Material": "Material 1", 'Supplier Name':'abc123',"Timestamp": (dt.datetime.now()-dt.timedelta(days=5)).date()},
    #     {"ID": 2, "Material": "Material 2", 'Supplier Name':'abc231',"Timestamp": (dt.datetime.now()-dt.timedelta(days=3)).date()},
    #     {"ID": 3, "Material": "Material 3", 'Supplier Name':'abc321', "Timestamp": (dt.datetime.now()-dt.timedelta(days=1)).date()},
    # ]
    data =  udb.pull_all_sessions()
    data = data.with_columns(
        [
            pl.col('start_time').cast(pl.Date),
            pl.col('end_time').cast(pl.Date),
            pl.lit(None).alias('Action')
        ]
    )
    data = data.rename(
        {
            'session_id':'ID',
            'username': 'Username',
            'description':'Material Description',
            'start_time':'Start Time',
            'end_time':'End Time'
        }
    )
    columns = data.columns
    cols = st.columns(len(columns))
    for i in range(len(cols)):
        cols[i].write(f'**{columns[i]}**')

    for row in data.rows(named = True):
        cols = st.columns(len(columns))
        for i in range(len(columns)-1):
            cols[i].write(row[columns[i]])
        action_col1, action_col2 = cols[-1].columns(2)
        
        if action_col1.button("💬", key=f"chat_{row['ID']}"):
            st.session_state.selected_session = row
            st.session_state.action = "chat_history"
            st.rerun()
        
        if action_col2.button("ℹ️", key=f"info_{row['ID']}"):
            st.session_state.selected_session = row
            st.session_state.action = "info"
            st.rerun()


def show_session_history_table_suppliers():
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f4f4f4;
            }
        </style>
    """, unsafe_allow_html=True)
    # data = [
    #     {"ID": 1, "Material": "Material 1", "Timestamp": (dt.datetime.now()-dt.timedelta(days=5)).date()},
    #     {"ID": 2, "Material": "Material 2", "Timestamp": (dt.datetime.now()-dt.timedelta(days=3)).date()},
    #     {"ID": 3, "Material": "Material 3", "Timestamp": (dt.datetime.now()-dt.timedelta(days=1)).date()},
    # ]
    data =  udb.pull_sessions_by_user(username=st.session_state.username)
    data = data.with_columns(
        [
            pl.col('start_time').cast(pl.Date),
            pl.col('end_time').cast(pl.Date),
            pl.lit(None).alias('Action')
        ]
    )
    data = data.rename(
        {
            'session_id':'ID',
            'username': 'Username',
            'description':'Material Description',
            'start_time':'Start Time',
            'end_time':'End Time'
        }
    )
    columns = data.columns
    cols = st.columns(len(columns))
    for i in range(len(cols)):
        cols[i].write(f'**{columns[i]}**')

    for row in data.rows(named = True):
        cols = st.columns(len(columns))
        for i in range(len(columns)-1):
            cols[i].write(row[columns[i]])
        action_col1, action_col2, action_col3 = cols[-1].columns(3)
        if action_col1.button("🔄", key=f"restart_{row['ID']}"):
            st.session_state.selected_session = row
            st.session_state.action = "restart"
            st.rerun()
        
        if action_col2.button("💬", key=f"chat_{row['ID']}"):
            st.session_state.selected_session = row
            st.session_state.action = "chat"
            st.rerun()
        
        if action_col3.button("ℹ️", key=f"info_{row['ID']}"):
            st.session_state.selected_session = row
            st.session_state.action = "info"
            st.rerun()

    # if st.button("Start New Session"):
    #     st.session_state.action = 'restart'
    #     st.rerun()
    
    if st.session_state.action in ['chat','restart']:
        st.session_state.messages.append(
            {
                "content": """
                Hello, and welcome to the Tail Spend Negotiation Tool! 
                In our efforts to ensure the best outcomes for both parties, 
                we use this platform to explore the most mutually beneficial 
                terms with our suppliers. We also track supplier agreements 
                and prioritize collaborations with suppliers who have provided 
                competitive terms in the past. Let's get started!""", 
                "sender": 'bot'
            }
        )
        st.session_state.messages.append(
            {
                "content": """How are you today?""", 
                "sender": 'bot'
            }
        )
        st.session_state.step = ConversationState.SUPPLER_STATUS

def supplier_status():
    if st.button("Good"):
        st.session_state.messages.append(
            {
                'content':'Good',
                'sender':'user'
            }
        )
        st.session_state.messages.append(
            {
                'content':'Glad to hear that!',
                'sender':'bot'
            }
        )
        st.session_state.messages.append(
            {
                'content':f'Before we proceed, could you confirm that you are the correct contact to discuss Quote {random.randrange(11111,99999)}?',
                'sender':'bot'
            }
        )
        st.session_state.step = ConversationState.NEGOTIATION_CONFIRMATION
        st.rerun()

    if st.button("Great"):
        st.session_state.messages.append(
            {
                'content':'Great',
                'sender':'user'
            }
        )
        st.session_state.messages.append(
            {
                'content':'Glad to hear that!',
                'sender':'bot'
            }
        )
        st.session_state.messages.append(
            {
                'content':'Before we proceed, could you confirm that you are the correct contact to discuss Quote {}?',
                'sender':'bot'
            }
        )
        st.session_state.step = ConversationState.NEGOTIATION_CONFIRMATION
        st.rerun()

def negotiation_confirmation():
    if st.button("Yes"):
        st.session_state.messages.append(
            {
                'content':'Yes',
                'sender':'user'
            }
        )
        st.session_state.messages.append(
            {
                'content':'Thanks for your confirmation. Let us review the quotation and make offers for you',
                'sender':'bot'
            }
        )
        st.session_state.step = ConversationState.FIRST_OFFER
        st.rerun()

    if st.button("No"):
        st.session_state.messages.append(
            {
                'content':'No',
                'sender':'user'
            }
        )
        st.session_state.step = ConversationState.DEFAULT
        st.rerun()

# def first_offer_page():
#     if st.session_state.first_time_offer_generated == False:
#         st.session_state.responses = um.generate_offer_using_LLM(
#             base_offer = st.session_state.base_offer,
#             min_levers = st.session_state.MIN_LEVERS,
#             max_levers = st.session_state.MAX_LEVERS,
#             step = 1,
#             TCO_hike_threshold_pct = 30,
#             model = st.session_state.model,
#             supplier_offer = None,
#             levers = st.session_state.levers
#         )
#         st.session_state.first_time_offer_generated = True
#     st.html(f'Please select an offer from any of the offers below to negotiate')
#     options = [
#         utils.convert_to_markdown(st.session_state.responses['offers'][0]),
#         utils.convert_to_markdown(st.session_state.responses['offers'][1]),
#         utils.convert_to_markdown(st.session_state.responses['offers'][2]),
#     ]

#     cols = st.columns(3)
#     for i in range(len(cols)):
#         with cols[i]:
#             option = options[i]
#             if st.button(label = option,key = str(i)):
#                 st.session_state.supplier_offer = option
#                 st.session_state.offer_selected = True
#                 st.rerun()
            
#     if st.session_state.offer_selected:
#         if st.button("Accept"):
#             st.session_state.messages.append(
#                 {
#                     'content':f'''Here are the offers for you: 
#                     Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
#                     Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
#                     Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
#                     'sender':'bot'
#                 }
#             )
#             st.session_state.messages.append(
#                 {
#                     "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.supplier_offer}", 
#                     "sender": 'bot'
#                 }
#             )
#             st.session_state.step = ConversationState.OFFER_ACCEPTED
#             st.rerun()

#         if st.button("Negotiate"):
#             st.session_state.messages.append(
#                 {
#                     'content':f'''Here are the offers for you: 
#                     Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
#                     Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
#                     Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
#                     'sender':'bot'
#                 }
#             )
#             st.session_state.messages.append(
#                 {
#                     "content": f"I want to negotiate.", 
#                     "sender": 'user'
#                 }
#             )
#             st.session_state.step = ConversationState.SUPPLIER_LEVERS_INPUT
#             st.rerun()

def first_offer_page():
    session = udb.get_session_by_id(
        session_id = st.session_state.selected_session['ID']
    ).rows(named = True)[0]
    st.session_state.material_id = session['material_id']
    # st.session_state.session_id = udb.start_session(
    #     user_id=session['user_id'],
    #     material_id=session['material_id']
    # )
    st.session_state.base_offer = udb.get_last_contract(
        user_id=session['user_id'],
        material_id=session['material_id']
    )['contract_details']
    material = udb.pull_material_by_id(session['material_id']).rows(named = True)[0]
    st.session_state.MIN_LEVERS = {
        'Unit Price':material['min_price_per_unit'],
        'Quantity': material['min_quantity']
    }
    st.session_state.MAX_LEVERS = {
        'Unit Price': material['max_price_per_unit'],
        'Quantity': material['max_quantity']
    }
    if st.session_state.first_time_offer_generated == False:
        st.session_state.responses = um.generate_offer_using_LLM(
            base_offer = st.session_state.base_offer,
            min_levers = st.session_state.MIN_LEVERS,
            max_levers = st.session_state.MAX_LEVERS,
            step = 1,
            TCO_hike_threshold_pct = 30,
            model = st.session_state.model,
            supplier_offer = None,
            levers = st.session_state.levers
        )
        st.session_state.first_time_offer_generated = True
    st.html(f'Please select an offer from any of the offers below to negotiate')
    options = [
        utils.convert_to_markdown(st.session_state.responses['offers'][0]),
        utils.convert_to_markdown(st.session_state.responses['offers'][1]),
        utils.convert_to_markdown(st.session_state.responses['offers'][2]),
    ]

    for i in range(3):
        with st.expander(f'Offer {i+1}', expanded=False):
            # st.session_state.supplier_offer = options[i]
            st.markdown(
                f"""
                <div style="font-size: 12px; line-height: 1.2;">
                    {options[i]}
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1,col2 = st.columns(2)
            with col1:
                if st.button("Accept",key=f'accept_{i}'):
                    st.session_state.supplier_offer = options[i]
                    st.session_state.messages.append(
                        {
                            'content':f'''Here are the offers for you: 
                            Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
                            Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
                            Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
                            'sender':'bot'
                        }
                    )
                    st.session_state.messages.append(
                        {
                            "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.supplier_offer}", 
                            "sender": 'bot'
                        }
                    )
                    st.session_state.step = ConversationState.OFFER_ACCEPTED
                    st.rerun()
            with col2:
                if st.button("Negotiate",key=f'negotiate_{i}'):
                    st.session_state.supplier_offer = options[i]
                    st.session_state.messages.append(
                        {
                            'content':f'''Here are the offers for you: 
                            Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
                            Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
                            Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
                            'sender':'bot'
                        }
                    )
                    st.session_state.messages.append(
                        {
                            "content": f"I want to negotiate.", 
                            "sender": 'user'
                        }
                    )
                    st.session_state.step = ConversationState.SUPPLIER_LEVERS_INPUT
                    st.rerun()

def supplier_levers_input_page():
    st.html(f'Please share your offer based on the levers input')
    levers = utils.extract_levers_from_text(
        offer_text=st.session_state.supplier_offer,
        model = st.session_state.model,
        example_data=pl.read_csv('data/sample_offers.csv')
    )
    col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
    col8,col9,col10, col11, col12,col13,col14 =  st.columns(7)
    with col1:
        unit_price = st.number_input(
            "Unit Price ($/unit)", 
            value = float(levers['price_per_unit']) if levers['price_per_unit'] != None else 0.0,
            min_value = 0.0, 
            max_value = 1000.0
        )
    with col2:
        quantity = st.number_input(
            "Quantity (in unit)", 
            value = int(levers['quantity']) if levers['quantity'] != None else 0, 
            min_value = 0, 
            max_value = 1000000, 
            step = 1
        )
    with col3:
        payment_term = st.selectbox(
            "Payment Term", 
            [
                'NET10','NET20','NET30','NET40',
                'NET50','NET60','NET70','NET80','NET90'
            ],
            placeholder=levers['payment_term'] if levers['payment_term'] != None else 'NET30'
        )
    with col4:
        payment_term_markup = st.number_input(
            "Payment Term Mark Up (%)", 
            value = float(levers['payment_term_markup']) if levers['payment_term_markup'] != None else 0.0, 
            min_value = 0.0, 
            max_value = 100.0
        )
    with col5:
        delivery_days = st.number_input(
            "Delivery Time (in Days)", 
            value = int(levers['delivery_timeline']) if levers['delivery_timeline'] != None else 1, 
            min_value = 1, 
            max_value = 100
        )
    with col6:
        contract_years = st.number_input(
            "Contract Period (in Years)", 
            value = int(levers['contract_period']) if levers['contract_period'] != None else 1,
            min_value = 1,
            max_value = 10
        )
    with col7:
        contract_inflation = st.number_input(
            "Contract Inflation (%)", 
            value = float(levers['contract_inflation']) if levers['contract_inflation'] != None else 0.0,
            min_value = 0.0,
            max_value = 100.0
        )
    with col8:
        warranty = st.number_input(
            "Warranty (in Years)", 
            value = int(levers['warranty']) if levers['warranty'] != None else 1, 
            min_value = 1,
            max_value = 100
        )
    with col9:
        incoterm = st.selectbox(
            "Incoterms", 
            [
                'EXW','FCA','FAS','FOB','CFR',
                'CIF','CPT','CIP','DAP','DPU','DDP'
            ],
            placeholder=levers['incoterms'] if levers['incoterms'] != None else 'DDP'
        )
    with col10:
        bundling_unit = st.number_input(
            "Bundling Unit", 
            value = int(levers['bundling_unit']) if levers['bundling_unit'] != None else None, 
            min_value = 0,
            max_value = 10**10
        )
    with col11:
        bundling_amount = st.number_input(
            "Bundling Amount ($)", 
            value = int(levers['bundling_amount']) if levers['bundling_amount'] != None else None, 
            min_value = 0,
            max_value = 10**10
        )
    with col12:
        bundling_discount = st.number_input(
            "Bundling Discount (%)", 
            value = float(levers['bundling_discount']) if levers['bundling_discount'] != None else 0.0, 
            min_value = 0.0,
            max_value = 100.0
        )
    with col13:
        rebates_threshold = st.number_input(
            "Rebate Unit", 
            value = int(levers['rebates_threshold_unit']) if levers['rebates_threshold_unit'] != None else None, 
            min_value = 0,
            max_value = 10**10
        )
    with col14:
        rebates_discount = st.number_input(
            "Rebate Discount (%)", 
            value = float(levers['rebates_discount']) if levers['rebates_discount'] != None else 0.0, 
            min_value = 0.0,
            max_value = 100.0
        )
    st.session_state.supplier_offer = um.levers_to_offer_text(
        price_per_unit = unit_price,
        quantity = quantity,
        bundling_unit = bundling_unit,
        bundling_amount = bundling_amount,
        bundling_discount = bundling_discount,
        payment_term = payment_term,
        payment_term_markup = payment_term_markup,
        delivery_timeline = delivery_days,
        contract_period = contract_years,
        contract_inflation = contract_inflation,
        rebates_threshold_unit = rebates_threshold,
        rebates_discount = rebates_discount,
        warranty = warranty,
        incoterms = incoterm
    )
    if st.button("Next"):
        st.session_state.messages.append(
            {
                "content": f'''Here is my offer: {st.session_state.supplier_offer}''', 
                "sender": 'user'
            }
        )
        st.session_state.step = ConversationState.SECOND_OFFER
        st.session_state.offer_selected = False
        st.rerun()

def second_offer_page():
    if st.session_state.second_time_offer_generated == False:
        st.session_state.responses = um.generate_offer_using_LLM(
            base_offer = st.session_state.base_offer,
            min_levers = st.session_state.MIN_LEVERS,
            max_levers = st.session_state.MAX_LEVERS,
            step = 2,
            TCO_hike_threshold_pct = 30,
            model = st.session_state.model,
            supplier_offer = st.session_state.supplier_offer,
            levers = st.session_state.levers
        )
        st.session_state.second_time_offer_generated = True
    if st.session_state.responses['status'] == 'accepted':
        st.session_state.messages.append(
            {
                'sender':'bot',
                'content':"We are happy to share that we have accepted your offer. Let's make the deal"
            }
        )
        if st.button("Next"):
            st.session_state.step = ConversationState.RESTART
            st.rerun()
    else:
        st.html(f'Please select an offer from any of the offers below to negotiate')
        options = [
            utils.convert_to_markdown(st.session_state.responses['offers'][0]),
            utils.convert_to_markdown(st.session_state.responses['offers'][1]),
            utils.convert_to_markdown(st.session_state.responses['offers'][2]),
        ]
        for i in range(3):
            with st.expander(f'Offer {i+1}', expanded=False):
                # st.session_state.supplier_offer = options[i]
                st.markdown(
                    f"""
                    <div style="font-size: 12px; line-height: 1.2;">
                        {options[i]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col1,col2 = st.columns(2)
                with col1:
                    if st.button("Accept",key = f'accept_{i}'):
                        st.session_state.supplier_offer = options[i]
                        st.session_state.messages.append(
                            {
                                'content':f'''Here are the offers for you: 
                                Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
                                Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
                                Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
                                'sender':'bot'
                            }
                        )
                        st.session_state.messages.append(
                            {
                                "content": f"I want to proceed with this offer: {st.session_state.supplier_offer}", 
                                "sender": 'user'
                            }
                        )
                        st.session_state.step = ConversationState.OFFER_ACCEPTED
                        st.rerun()
                with col2:
                    if st.button("Negotiate",key = f'negotiate_{i}'):
                        st.session_state.supplier_offer = options[i]
                        st.session_state.messages.append(
                            {
                                'content':f'''Here are the offers for you: 
                                Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
                                Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
                                Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
                                'sender':'bot'
                            }
                        )
                        st.session_state.messages.append(
                            {
                                "content": f"I want to negotiate further", 
                                "sender": 'user'
                            }
                        )
                        st.session_state.step = ConversationState.SUPPLIER_LEVER_PRIORITY
                        st.rerun()


        # cols = st.columns(3)
        # for i in range(len(cols)):
        #     with cols[i]:
        #         option = options[i]
        #         if st.button(label = option,key = str(i)):
        #             st.session_state.supplier_offer = option
        #             st.session_state.offer_selected = True
        #             # st.rerun()
                
        # if st.session_state.offer_selected:
        #     # col1,col2 = st.columns(2)
        #     # with col1:
        #     if st.button("Accept"):
        #         st.session_state.messages.append(
        #             {
        #                 'content':f'''Here are the offers for you: 
        #                 Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
        #                 Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
        #                 Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
        #                 'sender':'bot'
        #             }
        #         )
        #         st.session_state.messages.append(
        #             {
        #                 "content": f"I want to proceed with this offer: {st.session_state.supplier_offer}", 
        #                 "sender": 'user'
        #             }
        #         )
        #         st.session_state.step = ConversationState.OFFER_ACCEPTED
        #         st.rerun()
        #     # with col2:
        #     if st.button("Negotiate"):
        #         st.session_state.messages.append(
        #             {
        #                 'content':f'''Here are the offers for you: 
        #                 Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
        #                 Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
        #                 Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
        #                 'sender':'bot'
        #             }
        #         )
        #         st.session_state.messages.append(
        #             {
        #                 "content": f"I want to negotiate further", 
        #                 "sender": 'user'
        #             }
        #         )
        #         st.session_state.step = ConversationState.SUPPLIER_LEVER_PRIORITY
        #         st.rerun()

def supplier_priority_lever_page():
    col1,col2,col3 = st.columns(3)
    with col1:
        priority_1 = st.selectbox(
            "Priority Lever 1", 
            [
                'Unit Price','Quantity','Payment Term','Incoterms',
                'Warranty','Delivery Timeline','Contract Length'
            ]
        )
    with col2:
        priority_2 = st.selectbox(
            "Priority Lever 2", 
            [
                'Unit Price','Quantity','Payment Term','Incoterms',
                'Warranty','Delivery Timeline','Contract Length'
            ]
        )
    with col3:
        priority_3 = st.selectbox(
            "Priority Lever 3", 
            [
                'Unit Price','Quantity','Payment Term','Incoterms',
                'Warranty','Delivery Timeline','Contract Length'
            ]
        )
    if st.button("Next"):
        st.session_state.messages.append(
            {
                "content": f'''My top priority levers are: 1. {priority_1}, 2. {priority_2}, 3. {priority_3}''', 
                "sender": 'user'
            }
        )
        st.session_state.levers = [priority_1,priority_2,priority_3]
        st.session_state.step = ConversationState.THIRD_OFFER
        st.session_state.offer_selected = False
        st.rerun()

def third_offer_page():
    if st.session_state.third_time_offer_generated == False:
        st.session_state.responses = um.generate_offer_using_LLM(
            base_offer = st.session_state.base_offer,
            min_levers = st.session_state.MIN_LEVERS,
            max_levers = st.session_state.MAX_LEVERS,
            step = 3,
            TCO_hike_threshold_pct = 30,
            model = st.session_state.model,
            supplier_offer = st.session_state.supplier_offer,
            levers = st.session_state.levers
        )
        st.session_state.third_time_offer_generated = True
    st.html(f'Please select an offer from any of the offers below to negotiate')
    options = [
        utils.convert_to_markdown(st.session_state.responses['offers'][0]),
        utils.convert_to_markdown(st.session_state.responses['offers'][1]),
        utils.convert_to_markdown(st.session_state.responses['offers'][2]),
    ]
    for i in range(3):
        with st.expander(f'Offer {i+1}', expanded=False):
            # st.session_state.supplier_offer = options[i]
            st.markdown(
                f"""
                <div style="font-size: 12px; line-height: 1.2;">
                    {options[i]}
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1,col2 = st.columns(2)
            with col1:
                if st.button("Accept",key = f'accept_{i}'):
                    st.session_state.supplier_offer = options[i]
                    st.session_state.messages.append(
                        {
                            'content':f'''Here are the offers for you: 
                            Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
                            Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
                            Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
                            'sender':'bot'
                        }
                    )
                    st.session_state.messages.append(
                        {
                            "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.supplier_offer}", 
                            "sender": 'bot'
                        }
                    )
                    st.session_state.step = ConversationState.OFFER_ACCEPTED
                    st.rerun()
            with col2:
                if st.button("Negotiate",key = f'negotiate_{i}'):
                    st.session_state.supplier_offer = options[i]
                    st.session_state.messages.append(
                        {
                            'content':f'''Here are the offers for you: 
                            Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
                            Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
                            Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
                            'sender':'bot'
                        }
                    )
                    st.session_state.messages.append(
                        {
                            "content": f"I am not okay with the current offer. want to negotiate further", 
                            "sender": 'user'
                        }
                    )
                    st.session_state.step = ConversationState.SUPPLIER_FINAL_OFFER
                    st.rerun()


    # cols = st.columns(3)
    # for i in range(len(cols)):
    #     with cols[i]:
    #         option = options[i]
    #         if st.button(label = option,key = str(i)):
    #             # st.session_state.supplier_offer = option
    #             st.session_state.supplier_offer = option
    #             st.session_state.offer_selected = True
    #             # st.rerun()
            
    # if st.session_state.offer_selected:
    #     # col1,col2 = st.columns(2)
    #     # with col1:
    #     if st.button("Accept"):
    #         st.session_state.messages.append(
    #             {
    #                 'content':f'''Here are the offers for you: 
    #                 Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
    #                 Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
    #                 Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
    #                 'sender':'bot'
    #             }
    #         )
    #         st.session_state.messages.append(
    #             {
    #                 "content": f"Thanks for chosing an offer. Please check the offer chosen by you and confirm {st.session_state.supplier_offer}", 
    #                 "sender": 'bot'
    #             }
    #         )
    #         st.session_state.step = ConversationState.OFFER_ACCEPTED
    #         st.rerun()
    #     # with col2:
    #     if st.button("Negotiate"):
    #         st.session_state.messages.append(
    #             {
    #                 'content':f'''Here are the offers for you: 
    #                 Offer 1: {utils.convert_to_markdown(st.session_state.responses['offers'][0])}
    #                 Offer 2: {utils.convert_to_markdown(st.session_state.responses['offers'][1])}
    #                 Offer 3: {utils.convert_to_markdown(st.session_state.responses['offers'][2])}''',
    #                 'sender':'bot'
    #             }
    #         )
    #         st.session_state.messages.append(
    #             {
    #                 "content": f"I am not okay with the current offer. want to negotiate further", 
    #                 "sender": 'user'
    #             }
    #         )
    #         st.session_state.step = ConversationState.SUPPLIER_FINAL_OFFER
    #         st.rerun()

def supplier_final_levers_input_page():
    st.html(f'Please share your offer based on the levers input')
    levers = utils.extract_levers_from_text(
        offer_text=st.session_state.supplier_offer,
        model = st.session_state.model,
        example_data=pl.read_csv('data/sample_offers.csv')
    )
    col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
    col8,col9,col10, col11, col12,col13,col14 =  st.columns(7)
    with col1:
        unit_price = st.number_input(
            "Unit Price ($/unit)", 
            value = float(levers['price_per_unit']) if levers['price_per_unit'] != None else 0.0,
            min_value = 0.0, 
            max_value = 1000.0
        )
    with col2:
        quantity = st.number_input(
            "Quantity (in unit)", 
            value = int(levers['quantity']) if levers['quantity'] != None else 0, 
            min_value = 0, 
            max_value = 1000000, 
            step = 1
        )
    with col3:
        payment_term = st.selectbox(
            "Payment Term", 
            [
                'NET10','NET20','NET30','NET40',
                'NET50','NET60','NET70','NET80','NET90'
            ],
            placeholder=levers['payment_term'] if levers['payment_term'] != None else 'NET30'
        )
    with col4:
        payment_term_markup = st.number_input(
            "Payment Term Mark Up (%)", 
            value = float(levers['payment_term_markup']) if levers['payment_term_markup'] != None else 0.0, 
            min_value = 0.0, 
            max_value = 100.0
        )
    with col5:
        delivery_days = st.number_input(
            "Delivery Time (in Days)", 
            value = int(levers['delivery_timeline']) if levers['delivery_timeline'] != None else 1, 
            min_value = 1, 
            max_value = 100
        )
    with col6:
        contract_years = st.number_input(
            "Contract Period (in Years)", 
            value = int(levers['contract_period']) if levers['contract_period'] != None else 1,
            min_value = 1,
            max_value = 10
        )
    with col7:
        contract_inflation = st.number_input(
            "Contract Inflation (%)", 
            value = float(levers['contract_inflation']) if levers['contract_inflation'] != None else 0.0,
            min_value = 0.0,
            max_value = 100.0
        )
    with col8:
        warranty = st.number_input(
            "Warranty (in Years)", 
            value = int(levers['warranty']) if levers['warranty'] != None else 1, 
            min_value = 1,
            max_value = 100
        )
    with col9:
        incoterm = st.selectbox(
            "Incoterms", 
            [
                'EXW','FCA','FAS','FOB','CFR',
                'CIF','CPT','CIP','DAP','DPU','DDP'
            ],
            placeholder=levers['incoterms'] if levers['incoterms'] != None else 'DDP'
        )
    with col10:
        bundling_unit = st.number_input(
            "Bundling Unit", 
            value = int(levers['bundling_unit']) if levers['bundling_unit'] != None else None, 
            min_value = 0,
            max_value = 10**10
        )
    with col11:
        bundling_amount = st.number_input(
            "Bundling Amount ($)", 
            value = int(levers['bundling_amount']) if levers['bundling_amount'] != None else None, 
            min_value = 0,
            max_value = 10**10
        )
    with col12:
        bundling_discount = st.number_input(
            "Bundling Discount (%)", 
            value = float(levers['bundling_discount']) if levers['bundling_discount'] != None else 0.0, 
            min_value = 0.0,
            max_value = 100.0
        )
    with col13:
        rebates_threshold = st.number_input(
            "Rebate Unit", 
            value = int(levers['rebates_threshold_unit']) if levers['rebates_threshold_unit'] != None else None, 
            min_value = 0,
            max_value = 10**10
        )
    with col14:
        rebates_discount = st.number_input(
            "Rebate Discount (%)", 
            value = float(levers['rebates_discount']) if levers['rebates_discount'] != None else 0.0, 
            min_value = 0.0,
            max_value = 100.0
        )
    st.session_state.supplier_offer = um.levers_to_offer_text(
        price_per_unit = unit_price,
        quantity = quantity,
        bundling_unit = bundling_unit,
        bundling_amount = bundling_amount,
        bundling_discount = bundling_discount,
        payment_term = payment_term,
        payment_term_markup = payment_term_markup,
        delivery_timeline = delivery_days,
        contract_period = contract_years,
        contract_inflation = contract_inflation,
        rebates_threshold_unit = rebates_threshold,
        rebates_discount = rebates_discount,
        warranty = warranty,
        incoterms = incoterm
    )
    if st.button("Next"):
        st.session_state.messages.append(
            {
                "content": f'''Here is my final offer: {st.session_state.supplier_offer}''', 
                "sender": 'user'
            }
        )
        st.session_state.step = ConversationState.FINAL_OFFER
        st.session_state.offer_selected = False
        st.rerun()

def final_offer_page():
    if st.session_state.final_offer_generated == False:
        st.session_state.responses = um.generate_offer_using_LLM(
            base_offer = st.session_state.base_offer,
            min_levers = st.session_state.MIN_LEVERS,
            max_levers = st.session_state.MAX_LEVERS,
            step = 3,
            TCO_hike_threshold_pct = 30,
            model = st.session_state.model,
            supplier_offer = st.session_state.supplier_offer,
            levers = st.session_state.levers
        )
        st.session_state.final_offer_generated = True
    if st.session_state.responses['status'] == 'accepted':
        st.session_state.messages.append(
            {
                'sender':'bot',
                'content':"We are happy to share that we have accepted your offer. Let's make the deal"
            }
        )
        st.session_state.step = ConversationState.OFFER_ACCEPTED
    else:
        st.session_state.messages.append(
            {
                'sender':'bot',
                'content':"Thanks for sharing your offer. We have assigned a ticket for you. One of our experts will reach out to you soon"
            }
        )
        st.html('Sorry, we could make the deal. However we will assign a ticket for you to connect with Expert. Please select Confirm button to confirm')
    if st.button('Confirm'):
        st.session_state.step = ConversationState.RESTART
        st.session_state.final_offer_shared = True
        st.rerun()
    
def show_sidebar(username):
    st.markdown(
        """
        <style>
        /* Change selected option background color to purple */
        .css-17eq0hr a {
            background-color: #A100FF !important; /* Purple */
            color: white !important;
        }
        .css-17eq0hr a:hover {
            background-color: #9932CC !important; /* Lighter Purple on Hover */
        }
        /* Sidebar Logo */
        .sidebar-logo {
            display: flex;
            justify-content: center;
            margin-bottom: 10px;
        }
        .sidebar-logo img {
            width: 120px;
            padding: 10px;
        }
        /* Logout button styling */
        .logout-button {
            position: absolute;
            bottom: 20px;
            width: 90%;
            left: 50%;
            transform: translateX(-50%);
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-logo"><img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png"></div>', unsafe_allow_html=True)
        st.sidebar.title(f"Welcome, {username}")
        
        if username in ['accenture']:
            selected = option_menu(
                menu_title=None,
                options=["Materials", "Suppliers", "Contracts", "Negotiations"],
                icons=["box", "truck",None,"chat-dots"],
                menu_icon="list",
                default_index=0,
            )
        else:
            selected = option_menu(
                menu_title=None,
                options=["Negotiations"],
                icons=["chat-dots"],
                menu_icon="list",
                default_index=0,
            )

        # Logout button at the bottom
        st.markdown('<div class="logout-button">', unsafe_allow_html=True)
        if st.button("Logout", key="logout_button"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    return selected

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
        /* Style the login button */
        .stButton {
            display: flex;
            justify-content: center;
        }
        /* Style the login button */
        .stButton > button {
            background-color: #A100FF !important; /* Purple */
            color: white !important;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 16px;
            border: none;
        }
        .stButton > button:hover {
            background-color: #9932CC !important; /* Lighter Purple on Hover */
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
        .right-sidebar {
            position: fixed;
            right: 0;
            top: 0;
            width: 300px;
            height: 100%;
            background-color: #f8f9fa;
            padding: 20px;
            border-left: 1px solid #ddd;
            overflow-y: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    page = show_sidebar(st.session_state.username)
    if page == 'Materials':
        show_materials_table()
    if page == 'Suppliers':
        show_suppliers_table()
    if page == "Contracts":
        show_contracts_table()
    if page == 'Negotiations' and st.session_state.action == None:
        if st.session_state.username == 'accenture':
            show_session_history_table_admin()
        else:
            st.session_state.step = ConversationState.DEFAULT
    
    # with st.sidebar:
    #     # Header with user icon and logout option
    #     with st.container():
    #         st.markdown(
    #             """
    #             <div class="sidebar-logo">
    #                 <img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png" style="width: 120px; height: auto;"/>
    #                 <span class="sidebar-logo-text"> </span>
    #             </div>
    #             """,
    #             unsafe_allow_html=True,
    #         )
    #         st.sidebar.title(f"Welcome, {st.session_state.username}")
    #         if st.sidebar.button("Log Out"):
    #             st.session_state.logged_in = False
    #             st.session_state.username = ""
    #             st.rerun()
    #     with st.container():
    #         st.markdown(f'<h4><em>Negotiation in progress for material {st.session_state.material_id}</em></h4>', unsafe_allow_html=True)
    #         # st.html(f'Negotiation for material: {st.session_state.material_id}')
    #         # st.markdown(
    #         #     """
    #         #     <div style="background-color: #f1f3f4; padding: 15px; border-radius: 8px;">
    #         #         <h3 style="color: black;">Navigation</h3>
    #         #         <ul style="list-style: none; padding: 0;">
    #         #             <li>🟣✔ <b>Introduction</b></li>
    #         #             <li>🟣✔ Mutual interests</li>
    #         #             <li>🟣✔ Contract Terms Discussion</li>
    #         #             <li>🟣✔ Summary</li>
    #         #             <li><b style="color:rgb(182, 53, 229);">🟣✔ Conclusion</b></li>
    #         #         </ul>
    #         #     </div>
    #         #     """,
    #         #     unsafe_allow_html=True,
    #         # )

    # st.title("Tailend Supplier Negotiation Chatbot")
    # print(st.session_state.selected_session)
    # if st.session_state.selected_session != None:
    #     session = udb.get_session_by_id(
    #         session_id = st.session_state.selected_session['ID']
    #     ).rows(named = True)[0]
    #     st.session_state.material_id = session['material_id']
    #     # st.session_state.session_id = udb.start_session(
    #     #     user_id=session['user_id'],
    #     #     material_id=session['material_id']
    #     # )
    #     st.session_state.base_offer = udb.get_last_contract(
    #         user_id=session['user_id'],
    #         material_id=session['material_id']
    #     )['contract_details']
    #     material = udb.pull_material_by_id(session['material_id']).rows(named = True)[0]
    #     st.session_state.MIN_LEVERS = {
    #         'Unit Price':material['min_price_per_unit'],
    #         'Quantity': material['min_quantity']
    #     }
    #     st.session_state.MAX_LEVERS = {
    #         'Unit Price': material['max_price_per_unit'],
    #         'Quantity': material['max_quantity']
    #     }

        # print(udb.get_session_by_id(session_id = st.session_state.selected_session['ID']))
    # # TODO: Make it dynamic from database
    # st.session_state.base_offer = """
    # Price per unit: $100
    # Quantity: 10,000 units
    # Bundling: No bundling option.
    # Payment Terms: NET10, no option for extending to NET30.
    # Delivery Timelines: 7 days.
    # Contract Period Length: 1 year, with the option to renew at the same price.
    # Rebates: 1% rebate on orders above 11,000 units.
    # Warranties: 1-year standard warranty with an option to extend to 3 years for an additional $5/unit.
    # Incoterms: FOB (Free on Board) - buyer is responsible for customs and delivery.
    # """
    # # material = udb.get_material_info(
    # #     material_id=st.session_state.material_id
    # # )

    # # actual = utils.ContractActual(
    # #     quantity=material['quantity'],
    # #     price_per_unit=material['price_per_unit']
    # # )
    # st.session_state.MIN_LEVERS = {
    #     'Unit Price':100,
    #     'Quantity': 10000
    # }
    # st.session_state.MAX_LEVERS = {
    #     'Unit Price':120,
    #     'Quantity': 10000
    # }

    if st.session_state.step.value == ConversationState.DEFAULT.value:
        show_session_history_table_suppliers()
        return
    
    for msg in st.session_state.messages:
        if msg["sender"] != 'bot':
            message(msg["content"], is_user=True)
        else:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png" width="40" style="border-radius: 50%; margin-right: 10px;">
                    <div style="background-color: #F1F3F4; color: black; padding: 12px; border-radius: 12px; max-width: 70%;">
                        {msg["content"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    if st.session_state.step.value == ConversationState.OFFER_ACCEPTED.value:
        st.html(f'''
                Thanks for selecting an offer. 
                The offer you you selected: {st.session_state.supplier_offer}
                Please confirm'''
        )
        if st.button("Confirm"):
            st.session_state.messages.append(
                {
                    'content': "Thanks for confirming the offer. Have a great day ahead.",
                    'sender': 'bot',
                }
            )
            st.session_state.step = ConversationState.RESTART
            st.rerun()
    
    
    if st.session_state.step.value == ConversationState.SUPPLER_STATUS.value:
        supplier_status()

    if st.session_state.step.value == ConversationState.NEGOTIATION_CONFIRMATION.value:
        negotiation_confirmation()

    # Step 2: Ask the first question
    if st.session_state.step.value == ConversationState.FIRST_OFFER.value:
        first_offer_page()

    # Step 3: Follow-up question based on the chosen supplier_offer
    if st.session_state.step.value == ConversationState.SUPPLIER_LEVERS_INPUT.value:
        supplier_levers_input_page()

    if st.session_state.step.value == ConversationState.SECOND_OFFER.value:
        second_offer_page()

    if st.session_state.step.value == ConversationState.SUPPLIER_LEVER_PRIORITY.value:
        supplier_priority_lever_page()
    
    if st.session_state.step.value == ConversationState.THIRD_OFFER.value:
        third_offer_page()
    
    if st.session_state.step.value == ConversationState.SUPPLIER_FINAL_OFFER.value:
        supplier_final_levers_input_page()

    if st.session_state.step.value == ConversationState.FINAL_OFFER.value:
        final_offer_page()

    # Last Step: Restart option
    if st.session_state.step.value == ConversationState.RESTART.value:
        if st.button("Restart Chat"):
            st.session_state.sessions[st.session_state.current_session] = st.session_state.messages
            st.session_state.step = ConversationState.DEFAULT
            st.session_state.messages = []
            st.session_state.offer_selected = False
            st.session_state.supplier_offer = None
            st.session_state.first_time_offer_generated = False
            st.session_state.second_time_offer_generated = False
            st.session_state.third_time_offer_generated = False
            st.session_state.final_offer_generated = False
            st.session_state.final_offer_shared = False
            st.session_state.supplier_final_offer = None
            st.session_state.responses = None
            st.rerun()
    # with col2:
    #     st.markdown(
    #         """
    #         <div style="background-color: #f1f3f4; padding: 15px; border-radius: 8px;">
    #             <h3 style="color: black;">We have agreed:</h3>
    #             <p><b>Contract value:</b> $42,874</p>
    #             <p><b>Contract length:</b> 1 year</p>
    #             <p><b>Discount:</b> 8%</p>
    #             <p><b>Pay terms:</b> <span style="color:rgb(200, 53, 229);"><b>120 days</b></span></p>
    #             <p><b>2 year discount:</b> 9%</p>
    #             <hr>
    #             <h4 style="color: black;">Opportunities</h4>
    #             <p><b>Growth for plants:</b> Austin, Cleveland, Houston, Belleville</p>
    #             <p><b>Relationships Options:</b> Conference Call, Right to Pre-bid, SCF invitations</p>
    #         </div>
    #         """,
    #         unsafe_allow_html=True,
    #     )

if __name__ == "__main__":
    st.markdown("<h3 align='center'><b>Tail Spend Supplier Negotiation Chatbot</b></h3>", unsafe_allow_html=True)
    # st.title('Tail Spend Supplier Negotiation Chatbot')
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "material_id" not in st.session_state:
        st.session_state.material_id = None
    
    if "username" not in st.session_state:
        st.session_state.username = ""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "step" not in st.session_state:
        st.session_state.step = ConversationState.NONE

    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    
    if "selected_session" not in st.session_state:
        st.session_state.selected_session = None
    
    if "action" not in st.session_state:
        st.session_state.action = None

    if "current_session" not in st.session_state:
        st.session_state.current_session = "Session 1"
    
    if "offer_selected" not in st.session_state:
        st.session_state.offer_selected = False
    
    if "supplier_offer" not in st.session_state:
        st.session_state.supplier_offer = None

    if "first_time_offer_generated" not in st.session_state:
        st.session_state.first_time_offer_generated = False
    
    if "second_time_offer_generated" not in st.session_state:
        st.session_state.second_time_offer_generated = False
    
    if "third_time_offer_generated" not in st.session_state:
        st.session_state.third_time_offer_generated = False

    if "final_offer_generated" not in st.session_state:
        st.session_state.final_offer_generated = False
    
    if "final_offer_shared" not in st.session_state:
        st.session_state.final_offer_shared = False
    
    if "supplier_final_offer" not in st.session_state:
        st.session_state.supplier_final_offer = None

    if "responses" not in st.session_state:
        st.session_state.responses = None
    
    if "base_offer" not in st.session_state:
        st.session_state.base_offer = None

    if "levers" not in st.session_state:
        st.session_state.levers = [
            'Unit Price','Bundling','Payment Term',
            'Delivery Timeline','Rebates','Warranties',
            'Incoterms'
        ]
    
    if "model" not in st.session_state:
        st.session_state.model = AzureChatOpenAI(
            deployment_name= "gpt-4o",
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2023-09-15-preview",
            azure_endpoint="https://acsstscdamoai02.openai.azure.com/"
        )
    # main()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        # if st.session_state.material_id == None:
        #     material_selection_page()
        # else:
        main()
