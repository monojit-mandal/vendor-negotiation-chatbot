# from langchain.chat_models import AzureChatOpenAI
# import os
# from dotenv import load_dotenv
# load_dotenv()
# from typing import Sequence
# from langchain_core.messages import BaseMessage
# from langgraph.graph.message import add_messages
# from typing_extensions import Annotated, TypedDict
# from langchain_core.messages import SystemMessage, trim_messages
# from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import START, MessagesState, StateGraph
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# import duckdb
# import polars as pl


# class State(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], add_messages]
#     language: str

# model = AzureChatOpenAI(
#     deployment_name= "gpt-4o",
#     api_key=os.getenv('AZURE_OPENAI_API_KEY'),
#     api_version="2023-09-15-preview",
#     azure_endpoint="https://acsstscdamoai02.openai.azure.com/"
# )

# trimmer = trim_messages(
#     max_tokens=10000,
#     strategy="last",
#     token_counter=model,
#     include_system=True,
#     allow_partial=False,
#     start_on="human",
# )

# workflow = StateGraph(state_schema=State)

# def call_model(state: State):
#     global model
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             (
#                 "system",
#                 '''You are an experienced Prefessional. 
#                 Your job is to negotiate with Vendors. 
#                 Be polite always.
#                 Please keep professional tone throught the conversation and 
#                 always speak in {language}.''',
#             ),
#             MessagesPlaceholder(variable_name="messages"),
#         ]
#     )
#     chain = prompt | model
#     trimmed_messages = trimmer.invoke(state["messages"])
#     response = chain.invoke(
#         {"messages": trimmed_messages, "language": state["language"]}
#     )
#     return {"messages": [response]}

# workflow.add_edge(START, "model")
# workflow.add_node("model", call_model)

# memory = MemorySaver()
# app = workflow.compile(checkpointer=memory)

# def get_message_history(user_id:int,session_id:int):
#     db_connection = duckdb.connect("chatbot.db")
#     query = '''
#     select m.sender,m.content,m.timestamp from Users u left join Sessions s
#     on u.user_id = s.user_id
#     left join Messages m
#     on s.session_id = m.session_id
#     where u.user_id = ?
#     and s.session_id = ?
#     order by timestamp asc
#     '''
#     df_message_hist = pl.DataFrame(
#         db_connection.execute(
#             query=query,
#             parameters=(user_id,session_id)
#         ).arrow()
#     )
#     db_connection.close()
#     messages = []
#     for row in df_message_hist.rows(named=True):
#         if row['sender'] == 'user':
#             messages.append(
#                 HumanMessage(
#                     content=row['content']
#                 )
#             )
#         if row['sender'] == 'bot':
#             messages.append(
#                 AIMessage(
#                     content=row['content']
#                 )
#             )
#     return messages

# def get_system_message():
#     return SystemMessage(
#         content='''
#         You are a negotiator of the company. 
#         Your job is to negotiate with Human who are suppliers to your company.
#         Please be polite & keep your tone as experienced professional.
#         At You need start with the unit price for the material. 
#         Each time you can offer 1.05 times the price you offered last time.
#         Negotiation price should not exceed 150 $. Once your price matched with 
#         Vendor's offered price or Vendor agrees to go ahead with your offered price
#         you will stop negotiating and generate offer
#         '''
#     )


# def chatbot_response(user_id:int,session_id:int,input_message:str):
#     system_message = get_system_message()
#     message_history = get_message_history(user_id,session_id)
#     input_messages = (
#         [system_message] + 
#         message_history + 
#         [HumanMessage(content=input_message)]
#     )
#     config = {"configurable": {"thread_id": f'{user_id}-{session_id}'}}
#     output = app.invoke(
#         {"messages": input_messages, "language": 'English'},
#         config,
#     )
#     return output['messages'][-1].content

# Model Related packages
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import polars as pl
import random
from dotenv import load_dotenv
load_dotenv()
import utils
import utils_database as udb
from typing import List, Dict, Tuple


def offer_to_text(
    offer:utils.ContractActual
):
    offer_txt = f"""Unit Price: $ {round(offer.price_per_unit,1)}; Quantity: {round(offer.quantity)} units; Payment Terms: {utils.payment_term_to_txt(offer.payment_term)}; Delivery Timelines: {round(offer.delivery_timeline)} days; Contract Period: {round(offer.contract_period)} years; Warranties: {round(offer.warranty)} year(s); Incoterms: {utils.incoterm_to_text(offer.incoterms)}"""
    return offer_txt

def levers_to_offer_text(
    price_per_unit,
    quantity,
    bundling_unit,
    bundling_amount,
    bundling_discount,
    payment_term,
    payment_term_markup,
    delivery_timeline,
    contract_period,
    contract_inflation,
    rebates_threshold_unit,
    rebates_discount,
    warranty,
    incoterms
):
    offer_text = ''''''
    offer_text = offer_text + f'Unit Price: \$ {price_per_unit};'
    offer_text = offer_text + f'Quantity: {quantity};'
    offer_text = offer_text + f'Payment Term: Default NET30, if {payment_term} then mark up discount of {payment_term_markup};'
    offer_text = offer_text + f'Delivery Timeline: {delivery_timeline};'
    offer_text = offer_text + f'Contract Period: {contract_period} years with inflation {contract_inflation} % in each year;'
    offer_text = offer_text + f'Rebates: If purchase above {rebates_threshold_unit} unit then discout is {rebates_discount} %;'
    offer_text = offer_text + f'Warranty: {warranty} years;'
    offer_text = offer_text + f'Incoterms: {incoterms}'
    if bundling_unit == None and bundling_amount == None:
        pass
    if bundling_unit == None and bundling_amount != None:
        offer_text = offer_text + f'Bundling: If purchased amount {bundling_amount} $ or above then a discount of {bundling_discount} % on total contract'
    if bundling_unit != None and bundling_amount == None:
        offer_text = offer_text + f'Bundling: If purchased volume {bundling_unit} or above then a discount of {bundling_discount} % on total contract'
    if bundling_unit != None and bundling_amount != None:
        offer_text = offer_text + f'Bundling: If purchased volume above {bundling_unit} or bundling amount above {bundling_amount} $ then a discount of {bundling_discount} % on total contract'
    return offer_text
    


def generate_offer(
    base_offer:utils.ContractOffer,
    min_levers:dict,
    max_levers:dict,
    step:int,
    TCO_hike_threshold_pct:float,
    supplier_offer:utils.ContractOffer = None
):
    MIN_HIKE = 6
    MAX_HIKE = 8
    actual = utils.ContractActual(
        quantity = base_offer.quantity,
        price_per_unit=base_offer.price_per_unit,
        payment_term=base_offer.payment_term.term,
        delivery_timeline= base_offer.delivery_timeline,
        contract_period=base_offer.contract_period,
        warranty=base_offer.warranty,
        incoterms = base_offer.incoterms
    )
    TCO = actual.calculate_TCO_yearly(offer=base_offer)
    match step:
        case 1:
            # generate three offers
            hike = min(TCO_hike_threshold_pct,random.randint(MIN_HIKE,MAX_HIKE))
            print('TCO after 1st hike: ',TCO*(1+hike/100))
            offers = utils.generate_three_eqv_offers(
                offer = base_offer,
                actual = actual,
                tco_hike_pct = hike,
                min_levers = min_levers,
                max_levers = max_levers
            )
            return {'offers':offers,'status':'live'}
        case 2:
            # Evaluate supplier's offer
            tco_supplier = utils.ContractActual().calculate_TCO_yearly(
                offer=supplier_offer
            )
            hike = min(TCO_hike_threshold_pct,2*random.randint(MIN_HIKE,MAX_HIKE))
            print('TCO after 2nd hike: ',TCO*(1+hike/100))
            # If supplier offer is less than hiked TCO then return supplier offer & accept
            if TCO*(1+hike/100) > tco_supplier:
                return {'offers':[supplier_offer],'status':'accepted'}
            else:
                offers = utils.generate_three_eqv_offers(
                    offer = base_offer,
                    actual = actual,
                    tco_hike_pct = hike,
                    min_levers = min_levers,
                    max_levers = max_levers
                )
                return {'offers':offers,'status':'live'}
        case 3:
            hike = min(TCO_hike_threshold_pct,3*random.randint(MIN_HIKE,MAX_HIKE))
            offers = utils.generate_three_eqv_offers(
                offer = base_offer,
                actual = actual,
                tco_hike_pct = hike,
                min_levers = min_levers,
                max_levers = max_levers
            )
            return {'offers':offers,'status':'live'}
        case 4:
            # Evaluate supplier's final offer
            tco_supplier = utils.ContractActual().calculate_TCO_yearly(
                offer=supplier_offer
            )
            hike = min(TCO_hike_threshold_pct,4*random.randint(MIN_HIKE,MAX_HIKE))
            # If our final offer is less than supplier's final offer then we will accept
            if TCO*(1+hike/100) > tco_supplier:
                return {'offers':[supplier_offer],'status':'accepted'}
            # Else we will share our final offer
            else:
                offers = utils.generate_three_eqv_offers(
                    offer = base_offer,
                    actual = actual,
                    tco_hike_pct = hike,
                    min_levers = min_levers,
                    max_levers = max_levers
                )
                return {'offers':offers,'status':'live'}

def get_base_offer(user_id,material_id):
    contract = udb.get_last_contract(
        user_id=user_id,
        material_id=material_id,
    )
    base_offer = utils.ContractOffer().load_from_data(contract)
    return base_offer

# TODO
def generate_offer_using_LLM(
    base_offer:str,
    min_levers:dict,
    max_levers:dict,
    step:int,
    TCO_hike_threshold_pct:float,
    model:AzureChatOpenAI,
    supplier_offer:str,
    levers:List[str]
):
    # return {
    #     'offers': [
    #         'Unit Price: \\$ 100\nQuantity: 10,000 units\nBundling: No bundling option.\nPayment Terms: NET10, no option for extending to NET30.\nDelivery Timelines: 7 days.\nContract Period Length: 1 year, with the option to renew at the same price.\nRebates: 1% rebate on orders above 10,000 units.\nWarranties: 1-year standard warranty with an option to extend to 3 years for an additional \\$5/unit.\nIncoterms: DAP (Delivered At Place) – supplier manages shipping, with buyer handling customs and delivery.', 'Unit Price: \\$ 100\nQuantity: 10,000 units\nBundling: No bundling option.\nPayment Terms: NET10, no option for extending to NET30.\nDelivery Timelines: 7 days.\nContract Period Length: 1 year, with the option to renew at the same price.\nRebates: 2% rebate on orders above 11,000 units.\nWarranties: 1-year standard warranty with an option to extend to 3 years for an additional \\$5/unit.\nIncoterms: CIF (Cost, Insurance, and Freight) – supplier manages shipping and insurance.', 'Unit Price: \\$ 100\nQuantity: 10,000 units\nBundling: No bundling option.\nPayment Terms: NET10, no option for extending to NET30.\nDelivery Timelines: 7 days.\nContract Period Length: 1 year, with the option to renew at the same price.\nRebates: 2% rebate on orders above 11,000 units.\nWarranties: 1-year standard warranty with an option to extend to 3 years for an additional \\$5/unit.\nIncoterms: DPU (Delivered at Place, the supplier handles most of the shipping and delivery logistics).'
    #     ], 
    #     'status': 'live'
    # }
    MIN_HIKE = 6
    MAX_HIKE = 8
    TCO = utils.calculate_TCO_from_offer_using_LLM(
        base_offer=base_offer,
        proposal=base_offer,
        model = model
    )['Annual Cost of Contract ($)']
    print('TCO with existing offer: ',TCO)
    match step:
        case 1:
            # generate three offers
            hike = min(TCO_hike_threshold_pct,random.randint(MIN_HIKE,MAX_HIKE))
            TCO_new = TCO*(1+hike/100)
            TCO_min = TCO
            print('TCO after 1st hike: ',TCO*(1+hike/100))
            offers = utils.generate_eqv_offers_using_LLM(
                existing_offer = base_offer,
                TCO_new = TCO_new,
                TCO_min = TCO_min,
                min_levers = min_levers,
                max_levers = max_levers,
                n_offers = 3,
                model = model
            )
            return {'offers':offers,'status':'live'}
        case 2:
            # Evaluate supplier's offer
            tco_supplier = utils.calculate_contract_value_using_LLM(
                offer = supplier_offer,
                base_offer=base_offer,
                model = model
            )['Annual Cost of Contract ($)']
            print('Supplier is asking for TCO: ',tco_supplier)
            hike = min(TCO_hike_threshold_pct,2*random.randint(MIN_HIKE,MAX_HIKE))
            min_hike = min(TCO_hike_threshold_pct,MAX_HIKE)
            TCO_new = TCO*(1+hike/100)
            TCO_min = TCO*(1+min_hike/100)
            # If supplier offer is less than hiked TCO then return supplier offer & accept
            if TCO_new > tco_supplier:
                return {'offers':[supplier_offer],'status':'accepted'}
            else:
                levers = utils.understand_priority_levers(
                    existing_offer=base_offer,
                    supplier_offer=supplier_offer,
                    model = model
                )['Levers']
                offers = utils.generate_eqv_offers_using_LLM(
                    existing_offer = base_offer,
                    TCO_new = TCO_new,
                    TCO_min = TCO_min,
                    min_levers = min_levers,
                    max_levers = max_levers,
                    n_offers = 3,
                    model = model,
                    levers = levers
                )
                return {'offers':offers,'status':'live'}
        case 3:
            hike = min(TCO_hike_threshold_pct,3*random.randint(MIN_HIKE,MAX_HIKE))
            min_hike = min(TCO_hike_threshold_pct,2*MAX_HIKE)
            TCO_new = TCO*(1+hike/100)
            TCO_min = TCO*(1+min_hike/100)
            offers = utils.generate_eqv_offers_using_LLM(
                existing_offer = base_offer,
                TCO_new = TCO_new,
                TCO_min = TCO_min,
                min_levers = min_levers,
                max_levers = max_levers,
                n_offers = 3,
                model = model,
                levers = levers
            )
            return {'offers':offers,'status':'live'}
        case 4:
            tco_supplier = utils.calculate_contract_value_using_LLM(
                offer = supplier_offer,
                base_offer=base_offer,
                model = model
            )['Annual Cost of Contract ($)']
            print('Offer')
            hike = min(TCO_hike_threshold_pct,4*random.randint(MIN_HIKE,MAX_HIKE))
            min_hike = min(TCO_hike_threshold_pct,3*MAX_HIKE)
            TCO_new = TCO*(1+hike/100)
            TCO_min = TCO*(1+min_hike/100)
            # If supplier offer is less than hiked TCO then return supplier offer & accept
            if TCO_new > tco_supplier:
                return {'offers':[supplier_offer],'status':'accepted'}
            else:
                levers = utils.understand_priority_levers(
                    existing_offer=base_offer,
                    supplier_offer=supplier_offer,
                    model = model
                )['Levers']
                offers = utils.generate_eqv_offers_using_LLM(
                    existing_offer = base_offer,
                    TCO_new = TCO_new,
                    TCO_min = TCO_min,
                    min_levers = min_levers,
                    max_levers = max_levers,
                    n_offers = 3,
                    model = model,
                    levers=levers
                )
                return {'offers':offers,'status':'live'}