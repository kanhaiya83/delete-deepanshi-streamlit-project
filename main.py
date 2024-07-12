import os
from dotenv import load_dotenv
import streamlit as st
from langchain_community.llms import Replicate,Ollama
from langchain_openai import OpenAI
from langchain_core.output_parsers import StrOutputParser
from chatbot_prompt import get_broadband_customer_support_prompt, get_recommendation_prompt

# Load environment variables from .env file
load_dotenv()

# Define function to initialize chatbot
def initialize_chatbot(context):
    print("context",context)
    prompt = get_broadband_customer_support_prompt(context)
    llm = Ollama(model="tinyllama") 
    # llm = Replicate(model="meta/meta-llama-3-8b-instruct",)
    # llm = OpenAI(model_name="gpt-3.5-turbo-instruct")
    output_parser = StrOutputParser()
    chain=  prompt | llm | output_parser
    return chain

# Define function to initialize recommendation model
def initialize_recommendation_model(output):
    prompt = get_recommendation_prompt(output)
    llm = Ollama(model="tinyllama")  # Adjust model name as per your setup
    # llm = Replicate(model="meta/meta-llama-3-8b-instruct",)
    # llm = OpenAI(model_name="gpt-3.5-turbo-instruct")
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    return chain

# Streamlit app
st.title("Chatbot Interface")

# Initialize conversation state
if "conversation" not in st.session_state:
    initial_message = "Hi, I'm facing a problem."
    st.session_state.conversation = [("Customer", initial_message)]
    rec_chain = initialize_recommendation_model(initial_message)
    rec_output = rec_chain.invoke({'question': initial_message})
    st.session_state.recommendations = rec_output.split('\n')

# Display conversation
for role, message in st.session_state.conversation:
    st.write(f"{role}: {message}")
def on_input(input_text):
        st.session_state.conversation.append(("Agent", input_text))
        st.write(f"Agent: {input_text}")
        # Generate context from the current conversation
        context = "\n".join([f"{role}: {message}" for role, message in st.session_state.conversation])

        # Initialize or update chatbot chain with the new context
        chain = initialize_chatbot(context)

        # Get response from chatbot
        output = chain.invoke({'question': input_text})
        # Append chatbot response to conversation
        _output=  output.strip("\n")
        st.session_state.conversation.append(("Customer", _output))
        st.write(f"Customer: {_output}")

        # Initialize recommendation model with the new customer output
        rec_chain = initialize_recommendation_model(output)

        # Get recommendations from recommendation model
        rec_output = rec_chain.invoke({'question': output})
        st.session_state.recommendations = rec_output.split('\n')
        
        # Rerun the app to update the UI
        st.rerun()
# Display recommendations as text
if st.session_state.recommendations:
    container = st.container(border=True)
    container.write("Recommendations:")
    i =0
    for rec in (st.session_state.recommendations):
        i+=1
        if rec and rec.strip() and len(rec.split(" "))>5:
                
            if container.button(f"{rec}",key=i):
                on_input(rec)
        # container.write(rec)

# Input box for agent's response
input_text = st.text_area("Agent's Response", "",key="text_area")

if st.button("Send"):
    if input_text.strip():
        on_input(input_text)