import functools
from langchain_openai import ChatOpenAI
from agent_helper import create_agent,agent_node
from tool_kit import tavily_search,python_repl

research_llm = ChatOpenAI(model="gpt-4o")
chart_llm = ChatOpenAI(model="gpt-4o")

research_agent = create_agent(
    research_llm,
    [tavily_search],
    tool_message=(
        "Before using the search engine, carefully think through and clarify the query."
        " Then, conduct a single search that addresses all aspects of the query in one go"
    ),
    custom_notice=(
        "Notice:\n"
        "Only gather and organize information. Do not generate code or give final conclusions, leave that for other assistants."
    ),
)

resarch_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

chart_agent = create_agent(
    chart_llm,
    [python_repl],
    tool_message="Create clear and user-friendly charts based on the provided data.",
    custom_notice="Notice:\n"
    "If you have completed all tasks, respond with FINAL ANSWER.",
)

chart_node = functools.partial(agent_node, agent=chart_agent, name="Chart_Generator")
