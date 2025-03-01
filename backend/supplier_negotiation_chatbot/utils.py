from dataclasses import dataclass
from typing import List,Dict
from enum import Enum
from scipy.optimize import minimize_scalar
import polars as pl
import random
import ast
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import ResponseSchema, StructuredOutputParser,ListOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage
from langchain.chat_models import AzureChatOpenAI
import copy

class PaymentTerm(Enum):
    NET10 = 10
    NET20 = 20
    NET30 = 30
    NET40 = 40
    NET50 = 50
    NET60 = 60
    NET70 = 70
    NET80 = 80
    NET90 = 90

class Incoterms(Enum):
    EXW = 21000
    FCA = 19000
    FAS = 17000
    FOB = 15000
    CFR = 13000
    CIF = 11000
    CPT = 9000
    CIP = 7000
    DAP = 5000
    DPU = 3000
    DDP = 0

def format_payment_term(payment_term):
    if payment_term == None:
        return None
    pts = {   
        'NET10':PaymentTerm.NET10,
        'NET20':PaymentTerm.NET20,
        'NET30':PaymentTerm.NET30,
        'NET40':PaymentTerm.NET40,
        'NET50':PaymentTerm.NET50,
        'NET60':PaymentTerm.NET60,
        'NET70':PaymentTerm.NET70,
        'NET80':PaymentTerm.NET80,
        'NET90':PaymentTerm.NET90
    }
    return Payment(
        term=pts[payment_term],
        markup=0
    )

def format_incoterm(incoterm:str) -> Incoterms:
    if incoterm == None:
        return None
    incoterms = {
        'EXW':Incoterms.EXW,
        'FCA':Incoterms.FCA,
        'FAS':Incoterms.FAS,
        'FOB':Incoterms.FOB,
        'CFR':Incoterms.CFR,
        'CIF':Incoterms.CIF,
        'CPT':Incoterms.CPT,
        'CIP':Incoterms.CIP,
        'DAP':Incoterms.DAP,
        'DPU':Incoterms.DPU,
        'DDP':Incoterms.DDP
    }
    return incoterms[incoterm]


@dataclass
class Payment:
    term:PaymentTerm = PaymentTerm.NET30
    markup:float = 0

# @dataclass
# class TCOFunctionByLever:
#     lever: str
#     TCOFunction: callable

@dataclass
class ContractOffer:
    price_per_unit:float = None
    quantity:float = None
    bundling_unit:float = None
    bundling_amount:float = None
    bundling_discount:float = None
    payment_term: Payment = None
    delivery_timeline:float = None
    contract_period:int = None
    contract_inflation:float = None
    rebates_threshold_unit:float = None
    rebates_discount:float = None
    warranty:float = None
    incoterms:Incoterms = None

    def update_payment_term(self,payment_term):
        self.payment_term = payment_term
        return self
    
    def load_from_data(self,data):
        if data['price_per_unit'] != None:
            self.price_per_unit = data['price_per_unit']
        if data['quantity'] != None:
            self.quantity = data['quantity']
        if data['bundling_unit'] != None: 
            self.bundling_unit = data['bundling_unit']
        if data['bundling_amount'] != None:
            self.bundling_amount = data['bundling_amount']
        if data['bundling_discount'] != None:
            self.bundling_discount = data['bundling_discount']
        if data['payment_term'] != None:
            self.payment_term = format_payment_term(data['payment_term'])
        if data['delivery_timeline'] != None:
            self.delivery_timeline = data['delivery_timeline']
        if data['contract_period'] != None:
            self.contract_period = data['contract_period']
        if data['contract_inflation'] != None:
            self.contract_inflation = data['contract_inflation']
            # self.contract_inflation_by_year = (
            #     ast.literal_eval(data['contract_inflation_by_year']) 
            #     if data['contract_inflation_by_year'] != None 
            #     else None
            # )
        if data['rebates_threshold_unit'] != None:
            self.rebates_threshold_unit = data['rebates_threshold_unit']
        if data['rebates_discount'] != None:
            self.rebates_discount = data['rebates_discount']
        if data['warranty'] != None:
            self.warranty = data['warranty']
        if data['incoterms'] != None:
            self.incoterms = format_incoterm(data['incoterms'])
        return self


@dataclass
class ContractActual:
    price_per_unit:float = None
    quantity:float = None
    bundling_ind:bool = None
    payment_term:PaymentTerm = PaymentTerm.NET30
    delivery_timeline:float = None
    contract_period:int = None
    warranty:float = None
    incoterms:Incoterms = None

    def cost_without_offer(self,offer:ContractOffer):
        quantity = self.quantity if self.quantity != None else offer.quantity
        ppu = self.price_per_unit if self.price_per_unit != None else offer.price_per_unit
        return ppu*quantity
    
    def cost_with_bundling(self,offer:ContractOffer):
        cost = self.cost_without_offer(offer)
        if offer.bundling_amount != None:
            return (cost + offer.bundling_amount)*(1-offer.bundling_discount/100)
        else:
            return cost
    
    def is_bundling_required(self,offer:ContractOffer):
        cost = self.cost_without_offer(offer)
        cost_with_bundling = self.cost_with_bundling(offer)
        return (cost_with_bundling <= cost)
    
    def min_cost_bundling(self,offer:ContractOffer):
        if self.is_bundling_required(offer) == True:
            return self.cost_with_bundling(offer)
        else:
            return self.cost_without_offer(offer)
    
    def cost_payment_term(
        self,
        offer:ContractOffer
    ) -> float:
        cost = self.min_cost_bundling(offer)
        cost_pt = (
            cost*(1 + offer.payment_term.markup/100) - 
            cost*(6/100)*(offer.payment_term.term.value/365)
        )
        return cost_pt
    
    def min_cost_bundling_payment_term(
        self, 
        offer:ContractOffer
    ) -> float:
        cost_bund = self.min_cost_bundling(offer)
        cost_pt = self.cost_payment_term(offer)
        if cost_bund < cost_pt:
            return cost_bund
        else:
            return cost_pt
    
    def cost_after_rebate(self,offer:ContractOffer):
        cost = self.min_cost_bundling_payment_term(offer)
        # print('Cost after bundling and payment term',cost)
        if self.quantity != None:
            if self.quantity >= offer.rebates_threshold_unit:
                return cost*(1 - offer.rebates_discount/100)
        return cost
    
    def cost_with_incoterm(self,offer:ContractOffer):
        cost = self.cost_after_rebate(offer)
        cost_incoterm = cost+offer.incoterms.value
        return cost_incoterm
    
    def calculate_TCO_yearly(self,offer):
        cost = self.cost_with_incoterm(offer)
        tco_by_year = []
        for i in range(offer.contract_period):
            cost = cost*(1 + offer.contract_inflation/100)
            tco_by_year.append(cost)
        cost = sum(tco_by_year)/len(tco_by_year)
        return cost
    
    def check_delivery_timeline(self,offer:ContractOffer):
        return self.delivery_timeline <= offer.delivery_timeline
    
    def check_warranty(self,offer:ContractOffer):
        return self.warranty <= offer.warranty
    
    def update_from_data(self,data):
        if data['price_per_unit'] != None:
            self.price_per_unit = data['price_per_unit']
        if data['quantity'] != None:
            self.quantity = data['quantity']
        if data['payment_term'] != None:
            self.payment_term = format_payment_term(data['payment_term']).term
        if data['delivery_timeline'] != None:
            self.delivery_timeline = data['delivery_timeline']
        if data['contract_period'] != None:
            self.contract_period = data['contract_period']
        if data['warranty'] != None:
            self.warranty = data['warranty']
        if data['incoterms'] != None:
            self.incoterms = format_incoterm(data['incoterms'])
        return self

# class ChatState(Enum):
#     FIRST_TIME_OFFER = 1
#     SUPPLIER_OFFER_FORM = 2
#     SECOND_TIME_OFFER = 3
#     PRORITY_LEVER_SHARED = 4
#     THIRD_TIME_OFFER = 5
#     FINAL_OFFER_BY_SUPPLIER = 6

# def chatbot_response(
#     supplier_offer:ContractOffer = None,
#     current_offer:ContractActual = None,
#     chat_state:ChatState = None
# ):
#     match chat_state.value:
#         case 1:
#             print('First Time offer given')
#         case 2:
#             print('Supplier shared offer in form')
#         case 3:
#             print('Second time offer given')
#         case 4:
#             print('Priority lever shared by supplier')
#         case 5:
#             print('Third time offer given')
#         case 6:
#             print('Final offer from supplier')

def TCO_from_price_per_unit(price_per_unit,offer,actual):
    act = copy.deepcopy(actual)
    act.price_per_unit = price_per_unit
    return act.calculate_TCO_yearly(offer)

def TCO_from_quantity(quantity,offer,actual):
    act = copy.deepcopy(actual)
    act.quantity = quantity
    return act.calculate_TCO_yearly(offer)

# def TCO_from_payment_term(payment_term,offer,actual):
#     if payment_term <= 10:
#         offer.payment_term_offer = PaymentTerm.NET10
#     if ((payment_term <= 30) and (payment_term > 10)):
#         offer.payment_term_offer = PaymentTerm.NET30
#     if ((payment_term <= 60) and (payment_term > 30)):
#         offer.payment_term_offer = PaymentTerm.NET60
#     return actual.calculate_TCO_yearly(offer)

def incoterm_given_TCO(offer,actual,TCO_target):
    incoterms = [
        Incoterms.EXW,Incoterms.FCA,Incoterms.FAS,Incoterms.FOB,
        Incoterms.CFR,Incoterms.CIF,Incoterms.CPT,Incoterms.CIP,
        Incoterms.DAP,Incoterms.DPU,Incoterms.DDP
    ]
    for incoterm in incoterms:
        offer.incoterms = incoterm
        if actual.calculate_TCO_yearly(offer) <= TCO_target:
            break
    return incoterm

def payment_terms_given_TCO(offer,actual,TCO_target):
    payment_terms = [
        PaymentTerm.NET10,PaymentTerm.NET20,PaymentTerm.NET30,
        PaymentTerm.NET40,PaymentTerm.NET50,PaymentTerm.NET60,
        PaymentTerm.NET70,PaymentTerm.NET80,PaymentTerm.NET90

    ]
    tco_diff = []
    for payment_term in payment_terms:
        offer = offer.update_payment_term(
            Payment(term=payment_term,markup = 0)
        )
        tco = actual.calculate_TCO_yearly(offer)
        tco_diff.append(TCO_target - tco)
    df = pl.DataFrame({'PT':payment_terms,'DIFF':tco_diff})
    try:
        payment_term = (
            df.filter(pl.col('DIFF') > 0)
            .sort(by = 'DIFF',descending=False)
            .head(1)
        )['PT'].to_list()[0]
        return Payment(
            term = payment_term,
            markup = 0
        )
    except:
        return Payment(
            term = actual.payment_term,
            markup = 0
        )

def price_per_unit_given_TCO(offer,actual,TCO_target):
    def objective(x,offer,actual):
        return abs(TCO_from_price_per_unit(x,offer,actual) - TCO_target)
    price_per_unit = minimize_scalar(objective,args=(offer,actual)).x
    return price_per_unit

def quantity_given_TCO(offer,actual,TCO_target):
    def objective(x,offer,actual):
        return abs(TCO_from_quantity(x,offer,actual) - TCO_target)
    unit = minimize_scalar(objective,args=(offer,actual)).x
    return unit

def generate_offer_given_TCO_target(
    actual,
    offer,
    TCO_target,
    lever_priority,
    min_lever,
    max_lever
):
    levers = [ix for ix in lever_priority]
    probs = [lever_priority[ix] for ix in lever_priority]
    probs = [prob/sum(probs) for prob in probs]
    
    lever_negotiate = random.choices(levers,probs)[0]
    print(f'Randonmly selected lever: {lever_negotiate}')
    if lever_negotiate == 'quantity':
        qty = quantity_given_TCO(
            offer = offer,
            actual = actual,
            TCO_target = TCO_target
        )
        if ((qty >= min_lever['quantity']) & (qty <= max_lever['quantity'])):
            return ContractActual(
                price_per_unit = actual.price_per_unit,
                quantity = qty,
                payment_term=actual.payment_term,
                incoterms=actual.incoterms
            )
        else:
            return ContractActual(
                price_per_unit = actual.price_per_unit,
                quantity = max_lever['quantity'],
                payment_term = actual.payment_term,
                incoterms = actual.incoterms
            )
    if lever_negotiate == 'price_per_unit':
        ppu = price_per_unit_given_TCO(
            offer = offer,
            actual = actual,
            TCO_target = TCO_target
        )
        if ((ppu >= min_lever['price_per_unit']) & (ppu <= max_lever['price_per_unit'])):
            return ContractActual(
                price_per_unit = ppu,
                quantity = actual.quantity,
                payment_term = actual.payment_term,
                incoterms = actual.incoterms
            )
        else:
            return ContractActual(
                price_per_unit = max_lever['price_per_unit'],
                quantity = actual.quantity,
                payment_term = actual.payment_term,
                incoterms = actual.incoterms
            )
    if lever_negotiate == 'payment_term':
        pt = payment_terms_given_TCO(
            offer = offer,
            actual = actual,
            TCO_target = TCO_target
        )
        return ContractActual(
            price_per_unit = actual.price_per_unit,
            quantity = actual.quantity,
            payment_term = pt,
            incoterms = actual.incoterms
        )
    if lever_negotiate == 'incoterm':
        it = incoterm_given_TCO(
            offer = offer,
            actual = actual,
            TCO_target = TCO_target
        )
        return ContractActual(
            price_per_unit = actual.price_per_unit,
            quantity = actual.quantity,
            payment_term = actual.payment_term,
            incoterms = it
        )

def generate_offer_tuning_levers(
    offer,
    actual,
    tco_hike_pct,
    levers,
    min_lever,
    max_lever
):
    hikes = [tco_hike_pct*(i+1)/len(levers) for i in range(len(levers))]
    TCO = actual.calculate_TCO_yearly(offer=offer)
    for i in range(len(levers)):
        TCO_target = TCO*(1+hikes[i]/100)
        lever_priority = {levers[i]:1}
        actual = generate_offer_given_TCO_target(
            actual = actual,
            offer = offer,
            TCO_target=TCO_target,
            lever_priority=lever_priority,
            min_lever=min_lever,
            max_lever=max_lever
        )
    return actual

def create_offer_examples(example_data:pl.DataFrame):
    examples = """"""
    for offer in example_data.rows(named = True):
        example = f"""
        Input:
        {offer['offer']}
        Output:
        {'{'}{
            {
                "price_per_unit": offer['price_per_unit'],
                "quantity": offer['quantity'],
                "bundling_unit": offer['bundling_unit'],
                "bundling_amount": offer['bundling_amount'],
                "bundling_discount": offer['bundling_discount'],
                "payment_term": offer['payment_term'],
                "payment_term_markup": offer['payment_term_markup'],
                "delivery_timeline": offer['delivery_timeline'],
                "contract_period": offer['contract_period'],
                "contract_inflation": offer['contract_inflation'],
                "rebates_threshold_unit": offer['rebates_threshold_unit'],
                "rebates_discount": offer['rebates_discount'],
                "warranty": offer['warranty'],
                "incoterms":offer['incoterms']
            }
        }{'}'}
        """
        examples = examples + example
    examples = examples.replace("'",'"')
    examples = examples.replace('None','null')
    return examples

def extract_levers_from_text(
    offer_text:str,
    model:AzureChatOpenAI,
    example_data:pl.DataFrame
) -> ContractOffer:
    examples = create_offer_examples(example_data=example_data)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                You are a Negotiator for a compny. Your job is to understand & review what
                suppliers are offering. You need to understand extract meaningful lever values
                from offers by Suppliers. Your output should be in exactly same format mentione 
                in the examples below. Return None for the particular lever if you don't understand it.
                If you don't find any levers in Supplier's offer, return None for all the levers.
                
                Examples:
                {examples}
                """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    response_schemas = [
        ResponseSchema(name="price_per_unit", description="Price per Unit in $"),
        ResponseSchema(name="quantity",description="Quanity to Purchase"),
        ResponseSchema(name="bundling_unit",description="Unit of measure of price"),
        ResponseSchema(name="bundling_amount",description="Quantity of the product"),
        ResponseSchema(name="bundling_discount",description="Unit of measure of quantity"),
        ResponseSchema(name="payment_term",description="Payment Term"),
        ResponseSchema(name="payment_term_markup",description="Markup on proposed payment term"),
        ResponseSchema(name="delivery_timeline",description="Delivery time in years"),
        ResponseSchema(name="contract_period",description="Contract Period"),
        ResponseSchema(name="contract_inflation",description="Price Inflation of Conract"),
        ResponseSchema(name="rebates_threshold_unit",description="Minimum Unit to Avail Rebate"),
        ResponseSchema(name="rebates_discount",description="Rebate discount"),
        ResponseSchema(name="warranty",description="Warranty in years"),
        ResponseSchema(name="incoterms",description="incoterms"),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    chain = prompt | model | output_parser

    response = chain.invoke(
        {
            "messages": [HumanMessage(content=offer_text)],
        }
    )
    return response

def understand_levers_to_negotiate(
    offer_text:str,
    model:AzureChatOpenAI
) -> ContractOffer:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                You are a Negotiator for a compny. Your job is to understand & review what
                suppliers are offering. You need to understand which from Supplier's message 
                about which lever or set of levers Supplier wants to negotiate. Your response 
                will contain only the lever/levers out of the levers mentioned in these list
                1. price_per_unit
                2. quantity
                3. incoterms
                4. payment_term

                You will return output in Python list

                Examples:
                Input: I think price and quantity is low
                Output: ['price_per_unit','quantity']

                Input: I think we need to change payment days cycle
                Output: ['payment_term']

                Input: I feel offer is too low.
                Output: []
                """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model 

    response = chain.invoke(
        {
            "messages": [HumanMessage(content=offer_text)],
        }
    )
    return  ast.literal_eval(response.content)

def is_interested_to_negotiate(
    offer_text:str,
    model:AzureChatOpenAI
) -> ContractOffer:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                You are a Negotiator for a company. Your job is to understand Supplier's
                message and understand whether supplier wants to negotiate or not. Based on
                your understanding you will response True or False.

                Example:
                Input: I don't think we will be able to make the deal
                Output: False

                Input: I think the offer is too low
                Output: True

                Input: I feel it's impossible to make the deal
                Output: False
                """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model 

    response = chain.invoke(
        {
            "messages": [HumanMessage(content=offer_text)],
        }
    )
    return  ast.literal_eval(response.content)

def is_offer_accepted(
    offer_text:str,
    model:AzureChatOpenAI
) -> ContractOffer:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                You are a Negotiator for a company. Your job is to understand Supplier's
                message and understand whether supplier agreed with the offer. Based on
                your understanding you will response True or False.
                """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model 

    response = chain.invoke(
        {
            "messages": [HumanMessage(content=offer_text)],
        }
    )
    return  ast.literal_eval(response.content)

def generate_three_eqv_offers(
    offer:ContractOffer,
    actual:ContractActual,
    tco_hike_pct:int,
    min_lever:Dict[str,float],
    max_lever:Dict[str,float] 
):
    offer_1 = generate_offer_tuning_levers(
        offer = offer,
        actual=actual,
        tco_hike_pct=tco_hike_pct,
        levers=['price_per_unit'],
        min_lever = min_lever,
        max_lever = max_lever
    )
    print('Offer 1: ',offer_1)
    offer_2 = generate_offer_tuning_levers(
        offer = offer,
        actual=actual,
        tco_hike_pct=10,
        levers=['quantity'],
        min_lever = min_lever,
        max_lever = max_lever
    )
    print('Offer 2: ',offer_2)
    offer_3 = generate_offer_tuning_levers(
        offer = offer,
        actual=actual,
        tco_hike_pct=10,
        levers=['price_per_unit','quantity'],
        min_lever = min_lever,
        max_lever = max_lever
    )
    print('Offer 3: ',offer_3)
    return (offer_1,offer_2,offer_3)


# contract1 = utils.ContractOffer(
#     price_per_unit = 95,
#     quantity = 10000,
#     bundling_unit = None,
#     bundling_amount = 20000,
#     bundling_discount = 5,
#     payment_term=utils.Payment(
#         term=utils.PaymentTerm.NET60,
#         markup=3
#     ),
#     delivery_timeline = 10,
#     contract_period = 2,
#     contract_inflation_by_year = [0,3],
#     rebates_threshold_unit = 12000,
#     rebates_discount = 5,
#     warranty = 1,
#     incoterms = utils.Incoterms.DDP
# )
# contract2 = utils.ContractOffer(
#     price_per_unit = 100,
#     quantity = 10000,
#     bundling_unit = None,
#     bundling_amount = None,
#     bundling_discount = None,
#     payment_term=utils.Payment(
#         term=utils.PaymentTerm.NET10,
#         markup=0
#     ),
#     delivery_timeline = 7,
#     contract_period = 1,
#     contract_inflation_by_year = [0],
#     rebates_threshold_unit = 11000,
#     rebates_discount = 1,
#     warranty = 1,
#     incoterms = utils.Incoterms.FOB
# )
# actual = utils.ContractActual(
#     quantity = 12000,
#     # bundling_ind = True,
#     # payment_term = utils.PaymentTerm.NET60
# )
# actual.calculate_TCO_yearly(offer=contract1)