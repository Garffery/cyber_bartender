import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from langgraph.types import Command
from loguru import logger

# Add project root to python path to allow importing agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
logger.add(os.path.join(log_dir, "server.log"), rotation="10 MB", level="INFO")

from agent.cyber_bartender import get_app

app = FastAPI(title="Cyber Bartender API")

# Initialize the agent
agent_app = get_app()

class ChatRequest(BaseModel):
    message: Optional[str] = None
    thread_id: str
    resume_value: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    is_interrupt: bool = False
    interrupt_question: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    thread_config = {"configurable": {"thread_id": request.thread_id}}
    logger.info(f"Received chat request thread_config: {thread_config}")
    final_response = ""
    is_interrupt = False
    interrupt_question = None

    try:
        input_data = None
        if request.resume_value:
            # We are resuming from an interrupt
            input_data = Command(resume=request.resume_value)
        elif request.message:
            # New message
            input_data = {
                "origin_input": request.message,
                "user_requirements": []
            }
        else:
            raise HTTPException(status_code=400, detail="Either message or resume_value must be provided")

        async for event in agent_app.astream(input_data, config=thread_config):
            logger.debug(f"Event: {event}")
            
            if "__interrupt__" in event:
                logger.info("Interrupt detected")
                is_interrupt = True
                # Extract the question from the interrupt payload
                # The payload structure depends on how interrupt was called.
                # In BartenderToolNode: interrupt({"question": args})
                # So event['__interrupt__'] should contain this value.
                interrupt_data = event["__interrupt__"]
                if hasattr(interrupt_data, "value"):
                     interrupt_question = interrupt_data.value.get("question")
                elif isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                     # Sometimes it comes as (Interrupt(...),)
                     val = interrupt_data[0].value
                     interrupt_question = val.get("question") if isinstance(val, dict) else str(val)
                
                # We stop processing here and return to user
                break
            
            # Capture the bot's response
            if "BartenderNode" in event:
                messages = event["BartenderNode"].get("messages")
                if messages:
                    # It could be a list or a single message object/dict
                    if isinstance(messages, list):
                        last_msg = messages[-1]
                    else:
                        last_msg = messages
                    
                    if hasattr(last_msg, "content"):
                        final_response = last_msg.content
                    elif isinstance(last_msg, dict):
                        final_response = last_msg.get("content", "")

        return ChatResponse(
            response=final_response,
            is_interrupt=is_interrupt,
            interrupt_question=str(interrupt_question) if interrupt_question else None
        )

    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
