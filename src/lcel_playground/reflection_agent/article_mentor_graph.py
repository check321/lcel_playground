from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import END,StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from IPython.display import Image, display,Markdown
import os
import asyncio

load_dotenv(override=True)

base_url = os.environ.get("OPENAI_BASE_URL")
api_key = os.environ.get("OPENAI_API_KEY")
model = os.environ.get("OPENAI_MODEL")
reasoning_model = os.environ.get("REASONING_MODEL")

# define the State
class State(TypedDict):
    messages: Annotated[list,add_messages]
    
# writer agent
chat_model = ChatOpenAI(model=model,base_url=base_url,api_key=api_key,temperature=1.0)

writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a writing assistant tasked with creating well-crafted, coherent, and engaging articles based on the user's request."
        "Focus on clarity, structure, and qulity to produce the best possible of writing."
        "If the user provides feedback or suggestions, revice and improve the writing to meet the user's expectations."
    ),
    MessagesPlaceholder(variable_name="messages")
])

writer = writer_prompt | chat_model
    
async def writer_node(state:State) -> State:
    return {"messages": [await writer.ainvoke(state['messages'])]}

# mentor node

reflection_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a chief editor of Editing department grading an article submission. write critical and recommendations for the user's submission."
        "Provide detailed recommendations, including requests for length, including requests for length, clarity, depth, style and structure, etc."
        "用中文回答问题"
    ),
    MessagesPlaceholder(variable_name="messages"),
])

mentor_model = ChatOpenAI(model=reasoning_model,base_url=base_url,api_key=api_key,temperature=0.5)

reflect = reflection_prompt | mentor_model

async def mentor_node(state:State) -> State:
    mapper = {"ai":HumanMessage, "human":AIMessage}
    
    translated = [state['messages'][0]] + [
        mapper[msg.type](content=msg.content) for msg in state['messages'][1:]
    ]

    res = await reflect.ainvoke(translated)
    
    return {"messages": [HumanMessage(content = res.content)]}

MAX_ROUND = 6

def should_continue(state:State):
    if len(state['messages']) > MAX_ROUND:
        return END
    return "mentor"

graph_builder = StateGraph(State)

graph_builder.add_node("writer",writer_node)
graph_builder.add_node("mentor",mentor_node)

graph_builder.add_edge(START, "writer")

# writing and reflection in loop
graph_builder.add_conditional_edges("writer",should_continue)
graph_builder.add_edge("mentor","writer")

memory = MemorySaver()

graph = graph_builder.compile(checkpointer=memory)

# try:
#     display(
#         Image(
#             graph.get_graph(xray=True).draw_mermaid_png(output_file_path="article_mentor_graph.png")
#         )
#     )
# except Exception as e:
#     print(e)

def track_step_by_step(func):
    step_counter = {'count': 0}
    def wrapper(event,*args, **kwargs):
        step_counter['count'] += 1
        print(f"**Round {step_counter['count']}**")
        return func(event,*args, **kwargs)
    return wrapper


@track_step_by_step
def pretty_print(event):
    if 'writer' in event:
        generated_md = "#### 写作生成: \n"
        for message in event['writer']['messages']:
            generated_md += f"- {message.content}\n"
        print(generated_md)
    elif 'mentor' in event:
        reflection_md = "#### 编辑反馈: \n"
        for message in event['mentor']['messages']:
            reflection_md += f"- {message.content}\n"
        print(reflection_md)

inputs = {
    "messages": [
        HumanMessage(content="模仿科幻作家Ted Chiang的写作风格,创作一篇关于白酒的科幻短篇小说。要求： 1. 不少于3000字 2. 注意创作风格的模仿 3. 主旨体现科技进步与人文伦理的思辨")
    ]
}

config = {"configurable":{"thread_id": "imagine_2"}}

async def process_stream():
    async for event in graph.astream(inputs,config):
        pretty_print(event)

asyncio.run(process_stream())
