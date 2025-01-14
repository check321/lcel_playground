from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain import hub
import os
from langchain.schema.runnable import RunnablePassthrough

load_dotenv()

# question = "What is the investment perspective of BII in December 2024?"
# question = "文中提到对BTC投资的态度是什么，有哪些观点佐证？"
question = "文中提到的“magnificent 7”对BTC的影响有哪些？"
# 1. Read source document.
path = os.chdir(os.path.dirname(os.path.abspath(__file__)))
file_path = "assets/bii-investment-perspectives-december-2024.pdf"
loader = PyPDFLoader(file_path)
pages = loader.load()

# print(pages[0].page_content)

# 2. split document into chunks.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200,add_start_index=True)
chunks = text_splitter.split_documents(pages)

# print(chunks[2].metadata)

# 3. Create embeddings for chunks.
persist_dir = "chroma_db"
base_url=os.getenv("OPENAI_BASE_URL")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small",api_key=os.getenv("OPENAI_API_KEY"),base_url=base_url)
if not os.path.exists(persist_dir):
    os.makedirs(persist_dir)
    vec_store = Chroma.from_documents(documents=chunks, embedding=embeddings,persist_directory=persist_dir)
else:
    vec_store = Chroma(persist_directory=persist_dir,embedding_function=embeddings)

# 4. Query the vector store.
retriever = vec_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# 5. Create and run the RAG chain
# propmt template from langchain hub (https://smith.langchain.com/hub/rlm/rag-prompt)
rag_prompt = hub.pull("rlm/rag-prompt")

# 初始化 LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)

# 构建 RAG 链
chain = (
    {"context": retriever, "question": RunnablePassthrough()} 
    | rag_prompt 
    | llm
)

# 执行查询
result = chain.invoke(question)
print(result)