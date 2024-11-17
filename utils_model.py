from langchain.chat_models import AzureChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import SystemMessage, trim_messages
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import duckdb
import polars as pl


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str

model = AzureChatOpenAI(
    deployment_name= "gpt-4o",
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version="2023-09-15-preview",
    azure_endpoint="https://acsstscdamoai02.openai.azure.com/"
)

trimmer = trim_messages(
    max_tokens=10000,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

workflow = StateGraph(state_schema=State)

def call_model(state: State):
    global model
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                '''You are an experienced Prefessional. 
                Your job is to negotiate with Vendors. 
                Be polite always.
                Please keep professional tone throught the conversation and 
                always speak in {language}.''',
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | model
    trimmed_messages = trimmer.invoke(state["messages"])
    response = chain.invoke(
        {"messages": trimmed_messages, "language": state["language"]}
    )
    return {"messages": [response]}

workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def get_message_history(user_id:int,session_id:int):
    db_connection = duckdb.connect("chatbot.db")
    query = '''
    select m.sender,m.content,m.timestamp from Users u left join Sessions s
    on u.user_id = s.user_id
    left join Messages m
    on s.session_id = m.session_id
    where u.user_id = ?
    and s.session_id = ?
    order by timestamp asc
    '''
    df_message_hist = pl.DataFrame(
        db_connection.execute(
            query=query,
            parameters=(user_id,session_id)
        ).arrow()
    )
    db_connection.close()
    messages = []
    for row in df_message_hist.rows(named=True):
        if row['sender'] == 'user':
            messages.append(
                HumanMessage(
                    content=row['content']
                )
            )
        if row['sender'] == 'bot':
            messages.append(
                AIMessage(
                    content=row['content']
                )
            )
    return messages

def get_system_message():
    return SystemMessage(
        content='''
        You are a negotiator of the company. 
        Your job is to negotiate with Human who are suppliers to your company.
        Please be polite & keep your tone as experienced professional.
        At You need start with the unit price for the material. 
        Each time you can offer 1.05 times the price you offered last time.
        Negotiation price should not exceed 150 $. Once your price matched with 
        Vendor's offered price or Vendor agrees to go ahead with your offered price
        you will stop negotiating and generate offer
        '''
    )


def chatbot_response(user_id:int,session_id:int,input_message:str):
    system_message = get_system_message()
    message_history = get_message_history(user_id,session_id)
    input_messages = (
        [system_message] + 
        message_history + 
        [HumanMessage(content=input_message)]
    )
    config = {"configurable": {"thread_id": f'{user_id}-{session_id}'}}
    output = app.invoke(
        {"messages": input_messages, "language": 'English'},
        config,
    )
    return output['messages'][-1].content