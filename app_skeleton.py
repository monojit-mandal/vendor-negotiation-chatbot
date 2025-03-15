import streamlit as st
import pandas as pd
from streamlit_chat import message

# Sample DataFrame
data = {
    "Product": ["Apple", "Banana", "Orange"],
    "Price": [1.2, 0.8, 1.5],
    "Stock": [50, 100, 80]
}
df = pd.DataFrame(data)

# Convert DataFrame to Markdown Table
def df_to_markdown(df):
    return df.to_markdown(index=False)

# Streamlit App
st.title("Chatbot with Streamlit-Chat")

# Display User Message
message("Here is the product price list:", is_user=True)

# Display DataFrame as Markdown Table in Message
message(f"```\n{df_to_markdown(df)}\n```", is_user=True)
