# 2025/12/13
# zhangzhong
# [ ] https://docs.langchain.com/oss/python/langgraph/quickstart
# [ ] https://docs.langchain.com/oss/python/langgraph/graph-api


## [ ] https://docs.langchain.com/oss/python/langgraph/choosing-apis
# - Both APIs share the same underlying runtime and can be used together in the same application

## When to use Graph API
# - Complex decision trees and branching logic
# - State management across multiple components
# - Parallel processing with synchronization
# - Team development and documentation


## LangGraph visualization
# - https://docs.langchain.com/langsmith/studio


# Quick decision guide
# Use the Graph API when you need:
# - Complex workflow visualization for debugging and documentation
# - Explicit state management with shared data across multiple nodes
# - Conditional branching with multiple decision points
# -!!! Parallel execution paths that need to merge later
# - Team collaboration where visual representation aids understanding
# Use the Functional API when you want:
# - Minimal code changes to existing procedural code
# - Standard control flow (if/else, loops, function calls)
# - Function-scoped state without explicit state management
# - Rapid prototyping with less boilerplate
# - Linear workflows with simple branching logic


# 竟然有两种API
# graph api是最合适的，就只学着一种吧

import os
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.messages import AnyMessage, SystemMessage, ToolMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Literal
from langgraph.graph import StateGraph, START, END

api_key = os.environ["BIGMODEL_API_KEY"]


model = ChatOpenAI(
    temperature=0.6,
    model="glm-4.6",
    api_key=api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


## 2. Define state
# The graph’s state is used to store the messages and the number of LLM calls.
# State in LangGraph persists throughout the agent’s execution.

# 1️⃣ How State works in LangGraph (important context)

# LangGraph State is not a class instance that gets mutated.

# Instead:
# 	•	State is a typed schema
# 	•	Each node returns a partial update
# 	•	LangGraph merges node outputs into the global state

# Because of that, LangGraph supports:
# 	•	TypedDict
# 	•	Pydantic models ✅
# 	•	Plain dict

# Pydantic works because LangGraph treats the model as a schema + merge container, not as an ORM-like object.


# only support TypedDict? no, it also support pydantic model, let's use it!
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


## 3. Define model node
# The model node is used to call the LLM and decide whether to call a tool or not.
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    # shared state get partial update
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                # 这里加上了所有的历史消息
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


## 4. Define tool node
# The tool node is used to call the tools and return the results.
def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    # partial state update
    return {"messages": result}


## 5. Define Define end logic
# The conditional edge function is used to route to the tool node or end based upon whether the LLM made a tool call.
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


## 6. Build and compile the agent
# The agent is built using the StateGraph class and compiled using the compile method.
# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")


# Compile the agent
agent = agent_builder.compile()

# Show the agent
from IPython.display import Image, display

display(Image(agent.get_graph(xray=True).draw_mermaid_png()))


# Invoke
from langchain.messages import HumanMessage

messages = [HumanMessage(content="Add 3 and 4.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
