#This is the conversation code. 
import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from langchain_community.llms import Replicate # Put Ollama when use ollama
from langchain_openai import OpenAI
from langchain_core.output_parsers import StrOutputParser
from botprompt import get_broadband_customer_support_prompt, get_recommendation_prompt, get_end_conversation_prompt

# Load environment variables from .env file
load_dotenv()

# Define function to initialize chatbot
def initialize_chatbot(context):
    prompt = get_broadband_customer_support_prompt(context)
    llm = Replicate(model="meta/meta-llama-3-8b-instruct",)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    return chain

# Define function to initialize recommendation model
def initialize_recommendation_model(output):
    prompt = get_recommendation_prompt(output)
    llm = Replicate(model="meta/meta-llama-3-8b-instruct",)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    return chain

# Define function to initialize end conversation model
def initialize_end_conversation_model(context):
    prompt = get_end_conversation_prompt(context)
    llm = Replicate(model="meta/meta-llama-3-8b-instruct",)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    return chain

st.set_page_config(page_title="Customer Support")

# Columns for layout
col1, col2, col3 = st.columns([3, 1, 3], gap='small')

with col1:
    # Streamlit app
    st.title("Chatbot Interface")

    # Initialize conversation state
    if "conversation" not in st.session_state:
        initial_message = "Hi, I'm facing a problem."
        st.session_state.conversation = [("Customer", initial_message)]
        st.session_state.rounds = 0
        rec_chain = initialize_recommendation_model(initial_message)
        rec_output = rec_chain.invoke({'question': initial_message})
        st.session_state.recommendations = rec_output.split('\n')

    # Display conversation
    for role, message in st.session_state.conversation:
        st.write(f"{role}: {message}")

    def on_input(input_text):
        if st.session_state.rounds >= 3:
            st.write("Conversation ended after 3 rounds.")
            return

        st.session_state.conversation.append(("Agent", input_text))
        st.write(f"Agent: {input_text}")
        # Generate context from the current conversation
        context = "\n".join([f"{role}: {message}" for role, message in st.session_state.conversation])

        # Check if it's the second round to end the conversation gracefully
        if st.session_state.rounds == 2:
            chain = initialize_end_conversation_model(context)
        else:
            chain = initialize_chatbot(context)

        # Get response from chatbot
        output = chain.invoke({'question': input_text})
        _output = output.strip("\n")
        st.session_state.conversation.append(("Customer", _output))
        st.write(f"Customer: {_output}")

        # Initialize recommendation model with the new customer output if not ending
        if st.session_state.rounds < 2:
            rec_chain = initialize_recommendation_model(output)
            rec_output = rec_chain.invoke({'question': output})
            st.session_state.recommendations = rec_output.split('\n')

        # Increment rounds counter
        st.session_state.rounds += 1

        # Rerun the app to update the UI
        st.rerun()

    # Input box for agent's response
    input_text = st.text_area("Agent's Response", "", key="text_area")

    if st.button("Send"):
        if input_text.strip():
            on_input(input_text)

with col3:
    # Load data from a CSV file in the directory
    @st.cache_data
    def load_data(file_path):
        df = pd.read_csv(file_path)
        return df

    def get_customer_data(customer_id, df, column_name):
        customer_data = df[df[column_name] == customer_id]
        return customer_data

    # Streamlit app
    st.info('Customer Details')

    # Path to the CSV file
    file_path = 'Customer_data.csv'  # Change this to the actual path of your CSV file

    # Load data from the CSV file
    data = load_data(file_path)

    if not data.empty:
        # Input for customer ID
        customer_id_input = st.text_input('Enter Customer ID:')
        column_name = 'Customer ID'  # Change this to match your CSV file's column name

        if customer_id_input:
            # Use the input directly as a string to match the format CUST0003
            customer_id = customer_id_input.strip()

            # Filter the data based on the customer ID
            customer_data = get_customer_data(customer_id, data, column_name)

            if not customer_data.empty:
                st.write('Customer Data:')
                st.write(customer_data)
                if len(customer_data) > 0:
                    customer = customer_data.iloc[0]  # Assuming only one customer per ID

            else:
                st.write('Customer ID not found.')
    else:
        st.write("Failed to load the data. Please check the file path.")

    # Display recommendations as text
    if st.session_state.recommendations:
        container = st.container()
        container.write("Recommendations:")
        i = 0
        for rec in (st.session_state.recommendations):
            i += 1
            if rec and rec.strip() and len(rec.split(" ")) > 5:
                if container.button(f"{rec}", key=i):
                    on_input(rec)
