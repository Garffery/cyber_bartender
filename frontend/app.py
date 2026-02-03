import streamlit as st
import requests
import uuid
import json
import html as html_lib

ST_BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Cyber Bartender", page_icon="🍸", layout="centered")

# Function to render cocktail card
def render_cocktail_card(info):
    # Escape dynamic content to prevent HTML structure breakage
    name = html_lib.escape(info.get('name', 'Cocktail Name'))
    cn_name = html_lib.escape(info.get('cn_name', '中文名称'))
    description = html_lib.escape(info.get('description', '暂无描述'))
    texture = html_lib.escape(info.get('texture', '未知'))
    alcohol_content = html_lib.escape(info.get('alcohol_content', '未知'))
    recommendation = html_lib.escape(info.get('recommendation', '暂无推荐理由'))

    # Note: No indentation in HTML string to prevent Markdown from interpreting it as code blocks
    html = f"""
<div style="background-color: #1e1e1e; border-radius: 20px; padding: 30px; color: white; text-align: center; font-family: 'Helvetica', sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.5); max-width: 400px; margin: auto;">
<div style="margin-bottom: 20px;">
<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d4af37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M8 22h8M12 22v-11M17 11h-10a5 5 0 0 1 0 -10h10a5 5 0 0 1 0 10z"/>
</svg>
</div>
<div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">{name}</div>
<div style="font-size: 18px; color: #d4af37; margin-bottom: 20px;">{cn_name}</div>
<div style="border: 1px solid #333; border-radius: 10px; padding: 15px; font-size: 14px; line-height: 1.6; color: #ccc; margin-bottom: 20px; font-style: italic;">
"{description}"
</div>
<div style="display: flex; justify-content: space-between; margin-bottom: 20px; border-top: 1px solid #333; border-bottom: 1px solid #333; padding: 10px 0;">
<div style="text-align: center; width: 48%;">
<div style="font-size: 12px; color: #888; margin-bottom: 5px;">口感</div>
<div style="font-size: 14px; font-weight: bold; color: #eee;">{texture}</div>
</div>
<div style="text-align: center; width: 48%;">
<div style="font-size: 12px; color: #888; margin-bottom: 5px;">烈度</div>
<div style="font-size: 14px; font-weight: bold; color: #eee;">{alcohol_content}</div>
</div>
</div>
<div style="margin-bottom: 25px;">
<div style="font-size: 12px; color: #d4af37; margin-bottom: 5px;">推荐理由</div>
<div style="font-size: 12px; color: #aaa;">{recommendation}</div>
</div>
</div>
"""
    
    # Wrap in a container to ensure consistent alignment
    with st.chat_message("assistant"):
        st.markdown(html, unsafe_allow_html=True)
        
        # Add Streamlit buttons below the card for interaction
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔄 我不喜欢这个，换一杯", key=f"retry_{uuid.uuid4()}", use_container_width=True):
                 st.session_state.messages.append({"role": "user", "content": "我不喜欢这个，换一杯"})
                 # Trigger rerun to process the new message
                 st.rerun()
        with col2:
            if st.button("🆕", help="重新输入", key=f"reset_{uuid.uuid4()}", use_container_width=True):
                # Clear history to restart
                st.session_state.messages = []
                st.rerun()

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
    if message.get("type") == "cocktail_card":
        render_cocktail_card(message["content"])
    else:
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
                
                # Check for cocktail info
                cocktail_info = data.get("cocktail_info")
                if cocktail_info:
                     st.session_state.messages.append({"role": "assistant", "content": cocktail_info, "type": "cocktail_card"})
                     render_cocktail_card(cocktail_info)

                # Update interrupt state
                st.session_state.interrupted = is_interrupt
                st.session_state.interrupt_question = data.get("interrupt_question")
                if is_interrupt:
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
                
                # Check for cocktail info
                cocktail_info = data.get("cocktail_info")
                if cocktail_info:
                     st.session_state.messages.append({"role": "assistant", "content": cocktail_info, "type": "cocktail_card"})
                     render_cocktail_card(cocktail_info)
                
                # Update interrupt state
                st.session_state.interrupted = is_interrupt
                st.session_state.interrupt_question = data.get("interrupt_question")
                if is_interrupt:
                    st.rerun()
