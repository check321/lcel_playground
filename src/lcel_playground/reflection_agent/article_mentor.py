import os
import getpass
from langchain_core.messages import HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

base_url = os.environ.get("OPENAI_BASE_URL")
api_key = os.environ.get("OPENAI_API_KEY")

def _set_if_undefined(var:str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please input the value of {var}: ")

chat_model = ChatOpenAI(model="deepseek-chat",base_url=base_url,api_key=api_key,temperature=0.8)
# writer agent
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

article = ""

topic = HumanMessage(content="模仿科幻作家Ted Chiang的写作风格,创作一篇关于白酒的科幻短篇小说。要求： 1. 不少于3000字 2. 注意创作风格的模仿 3. 主旨体现科技进步与人文伦理的思辨")

for chunk in writer.stream({"messages": [topic]}):
    print(chunk.content, end="", flush=True)
    article += chunk.content

# mentor agent
reflection_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a chief editor of Editing department grading an article submission. write critical and recommendations for the user's submission."
        "Provide detailed recommendations, including requests for length, including requests for length, clarity, depth, style and structure, etc."
        "用中文回答问题"
    ),
    MessagesPlaceholder(variable_name="messages"),
])

mentor_model = ChatOpenAI(model="deepseek-chat",base_url=base_url,api_key=api_key,temperature=0.2)

reflect = reflection_prompt | mentor_model

reflection = ""

for chunk in reflect.stream({"messages": [topic,HumanMessage(content=article)]}):
    print(chunk.content, end="", flush=True)
    reflection += chunk.content
