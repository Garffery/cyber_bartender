import streamlit as st
import requests
import uuid
import json

ST_BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Cyber Bartender", page_icon="🍸")

st.title("🍸 Cyber Bartender")

# Initialize session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "interrupted" not in st.session_state:
    st.session_state.interrupted = False

if "interrupt_question" not in st.session_state:
    st.session_state.interrupt_question = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to send message to backend
def send_message(payload):
    try:
        response = requests.post(ST_BACKEND_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error communicating with backend: {e}")
        return None

# Handle input
if st.session_state.interrupted:
    # If interrupted, we need the user to answer the question
    with st.chat_message("assistant"):
        st.markdown(f"**Question:** {st.session_state.interrupt_question}")
    
    answer = st.chat_input("Answer the question...", key="answer_input")
    if answer:
        # Add user answer to local history
        st.session_state.messages.append({"role": "user", "content": answer})
        with st.chat_message("user"):
            st.markdown(answer)
            
        # Send resume payload
        with st.spinner("Bartender is thinking..."):
            payload = {
                "thread_id": st.session_state.thread_id,
                "resume_value": answer
            }
            data = send_message(payload)
            
            if data:
                bot_response = data.get("response", "")
                is_interrupt = data.get("is_interrupt", False)
                
                if bot_response:
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    with st.chat_message("assistant"):
                        st.markdown(bot_response)
                
                # Update interrupt state
                st.session_state.interrupted = is_interrupt
                st.session_state.interrupt_question = data.get("interrupt_question")
                st.rerun()

else:
    # Normal chat mode
    prompt = st.chat_input("What would you like to drink?")
    if prompt:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.spinner("Bartender is mixing..."):
            payload = {
                "thread_id": st.session_state.thread_id,
                "message": prompt
            }
            data = send_message(payload)
            
            if data:
                bot_response = data.get("response", "")
                is_interrupt = data.get("is_interrupt", False)
                
                if bot_response:
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    with st.chat_message("assistant"):
                        st.markdown(bot_response)
                
                # Update interrupt state
                st.session_state.interrupted = is_interrupt
                st.session_state.interrupt_question = data.get("interrupt_question")
                
                if is_interrupt:
                    st.rerun()
