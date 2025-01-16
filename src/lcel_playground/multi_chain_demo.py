from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from dotenv import load_dotenv
import os

load_dotenv()

base_url=os.getenv("OPENAI_BASE_URL")
api_key=os.getenv("OPENAI_API_KEY")

planner = (
    ChatPromptTemplate.from_template(
        "Explain the following computer science concepts to beginners: {concepts}"
    )
    | ChatOpenAI(model="gpt-4o-mini",base_url=base_url,api_key=api_key)
    | StrOutputParser()
    | {"explain": RunnablePassthrough()}
)

in_python = (
    ChatPromptTemplate.from_template(
        "Write a python function that {explain}"
    )
    | ChatOpenAI(model="gpt-4o-mini",base_url=base_url,api_key=api_key)
    | StrOutputParser()
)

in_rust = (
    ChatPromptTemplate.from_template(
        "Write a rust function that {explain}"
    )
    | ChatOpenAI(model="gpt-4o-mini",base_url=base_url,api_key=api_key)
    | StrOutputParser()
)

final_responder = (
    ChatPromptTemplate.from_messages(
        [
            ("ai","{explain}"),
            ("human", "Python example:{python_code} \n\n Rust example:{rust_code}"),
            ("system", "You are a helpful assistant of computer science that explains concepts to beginners.")
        ]
    )
    | ChatOpenAI(model="gpt-4o-mini",base_url=base_url,api_key=api_key)
    | StrOutputParser()
)

chain = (
    planner
    | {
        "python_code": in_python,
        "rust_code": in_rust,
        "explain": itemgetter("explain")
    }
    | final_responder
)

try:    
    result = chain.invoke({"concepts": "quicksort algorithm"})
    print(result)
except Exception as e:
    print(f"Chain execution failed: {str(e)}")