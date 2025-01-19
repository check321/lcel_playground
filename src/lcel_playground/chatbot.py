from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage,ToolMessage,BaseMessage
from typing import Literal
import json
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: Annotated[list,add_messages]
    
class BasicToolNode:
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name:tool for tool in tools}
    
    def __call__(self, inputs: dict):
        if messages := inputs.get("messages",[]):
            message = messages[-1]
        else:
            raise ValueError("No messages found in inputs")
    
        outputs = []
        
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}
    
def route_tools(
    state: State,
) -> Literal["tools","__end__"]:
    if isinstance(state,list):
        ai_message = state[-1]
    elif messages := state.get("messages",[]):
        ai_message = messages[-1]
    else:
        raise ValueError("No messages found in state: {state}")

    if hasattr(ai_message,"tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "__end__"

    
graph_builder = StateGraph(State)

chat_model = ChatOpenAI(model="gpt-4o-mini")
# tools
tavily_search = TavilySearchResults(k=1)
tools = [tavily_search]
llm_with_tools = chat_model.bind_tools(tools)
tool_node = BasicToolNode(tools = tools)
graph_builder.add_node("tools",tool_node)

def chatbot(state: State):
    return {"messages": [llm_with_tools .invoke(state["messages"])]}

graph_builder.add_node("chatbot",chatbot)
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {
        "tools": "tools",
        "__end__":"__end__"
    },
)
graph_builder.add_edge("tools","chatbot")
graph_builder.add_edge(START,"chatbot")
# graph_builder.add_edge("chatbot",END)

graph = graph_builder.compile()
# output the graph to a file
# chatbot_mermaid = graph.get_graph().draw_mermaid_png(output_file_path="chatbot-mermaid.png")
while True:
    user_input = input("User: ")
    
    if user_input.lower() in ["exit","quit","q","bye"]:
        print("Bye!")
        break
    for event in graph.stream({"messages":("user",user_input)}):
        for value in event.values():
            if isinstance(value["messages"][-1],BaseMessage):
                print("Assistant:",value["messages"][-1].content)


