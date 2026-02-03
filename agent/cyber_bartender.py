import asyncio
import getpass
import os

from langchain_community.tools import TavilySearchResults
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from agent.prompts import BARTENDER_PROMPT
from agent.state import BartenderState, Question
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import START, END, StateGraph
async def BartenderNode(state:BartenderState):
    tools = await get_bartender_tool()
    print(f"工具列表:{tools}")
    llm = ChatDeepSeek(model="deepseek-chat").bind_tools(tools)
    bartender_chain = BARTENDER_PROMPT | llm
    print(f"当前的state:{state}")
    res = await bartender_chain.ainvoke({"messages":state["messages"]})
    return {"messages":res}


async def BartenderToolNode(state:BartenderState):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        observation = await tool.ainvoke(tool_call["args"])
        result.append({"role": "tool",
                       "content": observation,
                       "name": tool_call["name"],
                       "tool_call_id": tool_call["id"]})

        if tool_call["name"] == "Question":
            human_value = interrupt(
                {
                    "question": tool_call["args"]
                }
            )
            result.append({"role":"user","content":human_value})

    return {"messages":result}

async def should_use_tool(state:BartenderState):
    print(f"进入选择节点:{state}")
    res = state.get("final_recommendation")
    message = state["messages"][-1]
    if res is not None :
        print("=======结束列表========")
        return END
    elif message.tool_calls:
        print("=======选择进入工具列表========")
        return "BartenderToolNode"
    else:
        print("=======默认结算列表========")
        return END



async def get_bartender_tool():
    tools = [TavilySearchResults(max_results=1), tool(Question)]
    return tools


workflow = StateGraph(BartenderState)
workflow.add_node("BartenderNode", BartenderNode)
workflow.add_node("BartenderToolNode", BartenderToolNode)
workflow.add_edge(START, "BartenderNode")
workflow.add_edge("BartenderToolNode", "BartenderNode")
workflow.add_conditional_edges("BartenderNode", should_use_tool, [END, "BartenderToolNode"])

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("DEEPSEEK_API_KEY")
_set_env("TAVILY_API_KEY")

async def main():
    app = workflow.compile(checkpointer = MemorySaver())
    inputs = {"messages": "大吉利的配方是什么"}
    thread_config = {"configurable": {"thread_id": 1}}
    async for event in app.astream(inputs, config=thread_config):
        print(event)

asyncio.run(main())


