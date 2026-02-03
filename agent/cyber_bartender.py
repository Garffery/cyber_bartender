import asyncio
import os
from typing import List

from dotenv import load_dotenv
from langchain_core.messages import get_buffer_string
from loguru import logger
from langchain_community.tools import TavilySearchResults
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import START, END, StateGraph

from agent.prompts import BARTENDER_SYSTEM_PROMPT
from agent.state import BartenderState, Question, ExtractRequirements, CocktailInfo

# Load environment variables from .env file
load_dotenv()

async def get_bartender_tool():
    """Returns the list of tools available to the bartender."""
    tools = [TavilySearchResults(max_results=1), tool(Question), tool(ExtractRequirements), tool(CocktailInfo)]
    return tools

async def BartenderNode(state: BartenderState):
    """The main agent node that generates responses or tool calls."""
    tools = await get_bartender_tool()

    
    llm = ChatDeepSeek(model="deepseek-chat").bind_tools(tools)
    bartender_chain = BARTENDER_SYSTEM_PROMPT | llm
    
    # print(f"Current state: {state}")
    # Pass the full message history to the LLM
    logger.info(f"酒保节点的状态：{state}")

    origin_input = state["origin_input"]
    user_requirements = state["user_requirements"]
    history = get_buffer_string(state["messages"])
    logger.info(f"原始输入:{origin_input}")
    logger.info(f"客人需求:{user_requirements}")
    logger.info(f"对话历史:{history}")
    user_requirements_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(history))

    res = await bartender_chain.ainvoke({"history": history, "origin_input":origin_input, "user_requirements":user_requirements_str})
    
    return {"messages": res}

async def BartenderToolNode(state: BartenderState):
    """Executes tools requested by the LLM."""
    tools = await get_bartender_tool()
    tool_map = {t.name: t for t in tools}
    
    result = []
    require = []
    final_recommendation = None
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls'):
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            
            if tool_name == "Question":
                # The Question tool triggers an interrupt to ask the user
                logger.info("========询问用户===========")
                human_value = interrupt({
                    "question": tool_call["args"]
                })
                # After resume, human_value contains the user's answer
                result.append({
                    "role": "user",
                    "content": human_value
                })
            elif tool_name == "ExtractRequirements":
                logger.info("========提取需求===========")
                res = tool_call["args"]
                require.append(res["requirements"])
                logger.info(f"需求：{res}")
            elif tool_name == "CocktailInfo":
                logger.info("========进行推荐===========")
                res = tool_call["args"]
                logger.info(f"推荐的鸡尾酒：{res}")
                final_recommendation = res
            
            elif tool_name in tool_map:
                selected_tool = tool_map[tool_name]
                try:
                    observation = await selected_tool.ainvoke(tool_call["args"])
                except Exception as e:
                    observation = f"Error executing tool {tool_name}: {str(e)}"
                
                result.append({
                    "role": "tool",
                    "content": observation,
                    "name": tool_name,
                    "tool_call_id": tool_call["id"]
                })
            else:
                result.append({
                    "role": "tool",
                    "content": f"Error: Tool {tool_name} not found.",
                    "name": tool_name,
                    "tool_call_id": tool_call["id"]
                })
    final_result = {}
    final_result["messages"] = result
    final_result["user_requirements"] = require
    final_result["final_recommendation"] = final_recommendation
    logger.info(f"返回结果：{final_result}")
    return final_result

async def should_use_tool(state: BartenderState):
    """Determines the next node based on the last message."""
    logger.debug(f"Deciding next step: {state}")
    res = state.get("final_recommendation")
    message = state["messages"][-1]
    
    if res is not None:
        logger.info("======= Ending ========")
        return END
    elif hasattr(message, 'tool_calls') and message.tool_calls:
        logger.info("======= Going to Tools ========")
        return "BartenderToolNode"
    else:
        logger.info("======= Default End ========")
        return END

# Define the graph
workflow = StateGraph(BartenderState)
workflow.add_node("BartenderNode", BartenderNode)
workflow.add_node("BartenderToolNode", BartenderToolNode)

workflow.add_edge(START, "BartenderNode")
workflow.add_edge("BartenderToolNode", "BartenderNode")
workflow.add_conditional_edges("BartenderNode", should_use_tool, [END, "BartenderToolNode"])

def get_app():
    """Compiles and returns the LangGraph application."""
    return workflow.compile(checkpointer=MemorySaver())

if __name__ == "__main__":
    async def main():
        app = get_app()
        inputs = {"origin_input": "帮我推荐一杯使用威士忌作为基酒的鸡尾酒","user_requirements":[]}
        thread_config = {"configurable": {"thread_id": "1"}}
        
        print("Starting interaction...")
        async for event in app.astream(inputs, config=thread_config):
            print(f"Event: {event}")
            if "__interrupt__" in event:
                print("Interrupted by Question tool. Resuming with mock answer...")
                user_answer = "我今天的心情不错,想要清爽的"
                command = Command(resume=user_answer)
                async for sub_event in app.astream(command, config=thread_config):
                    print(f"Sub-event: {sub_event}")

    asyncio.run(main())
