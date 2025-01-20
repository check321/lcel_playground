from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import tool
from typing import Annotated
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

load_dotenv()

# search tool.
tavily_search = TavilySearchResults(k=2)

# python runtime tool.
repl = PythonREPL()


@tool
def python_repl(code: Annotated[str, "The python code to execute to generate chart."]):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute code: {repr(e)}"
    return f"Successfully executed code: \n ```python\n{code}\n```\n"


tools = [tavily_search, python_repl]

tool_node = ToolNode(tools)
