from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from IPython.display import Image, display
import graphviz
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.memory import MemorySaver

# import logging

# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# class LoggingToolNode(ToolNode):
#     def __call__(self, state):
#         logging.info(f"TavilySearchResults tool is being invoked with state: {state}")
#         return super().__call__(state) 

load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

tool = TavilySearchResults(max_results=2)
tools = [tool]

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(api_key=openai_api_key)

llm_with_tools = llm.bind_tools(tools)  

def chatbot(state: State):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

graph_builder.add_node("chatbot", chatbot)


tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

memory = MemorySaver()

graph = graph_builder.compile(checkpointer=memory)

# try:
#     image_data = graph.get_graph().draw_mermaid_png()
#     image_path = "graph.png"

#     with open(image_path, "wb") as f:  
#         f.write(image_data)

# except Exception as e:
#     print(f"Error generating the graph: {e}")

config = {"configurable": {"thread_id": "1"}}

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break

    for event in graph.stream({"messages": [("user", user_input)]}, config):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

