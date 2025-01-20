from typing import Literal
from agent_state import AgentState
from langgraph.graph import StateGraph
from agent_node import resarch_node, chart_node
from tool_kit import tool_node
from langgraph.graph import START, END, StateGraph
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

def router(state) -> Literal["call_tool", "__end__", "continue"]:
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "call_tool"
    elif last_message.content.startswith("FINAL ANSWER"):
        return "__end__"
    else:
        return "continue"


workflow = StateGraph(AgentState)
workflow.add_node("Researcher", resarch_node)
workflow.add_node("Chart_Generator", chart_node)
workflow.add_node("call_tool", tool_node)

# reasercher condition edge
workflow.add_conditional_edges(
    "Researcher",
    router,
    {
        "continue": "Chart_Generator",
        "call_tool": "call_tool",
        "__end__": END,
    },
)

# chart_generator condition edge
workflow.add_conditional_edges(
    "Chart_Generator",
    router,
    {
        "continue": "Researcher",
        "call_tool": "call_tool",
        "__end__": END,
    },
)

# call_tool condition edge
workflow.add_conditional_edges(
    "call_tool",
    lambda x: x["sender"],
    {
        "Researcher": "Researcher",
        "Chart_Generator": "Chart_Generator",
    },
)

workflow.add_edge(START, "Researcher")

graph = workflow.compile()

# chatbot_mermaid = graph.get_graph().draw_mermaid_png(output_file_path="multi-chain-mermaid.png")

events = graph.stream(
    {
        "messages": [
            HumanMessage(content="Obtain the ETH price from 2008-2024, "
                         "and generate a price chart(.png） to current folder(./) with python,"
                         "End the task after generating the table.")
        ]
    },
    {"return_messages": 20},
    stream_mode="values"
)

for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()
