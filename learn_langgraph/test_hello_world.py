# 2025/12/13
# zhangzhong
# https://docs.langchain.com/oss/python/langgraph/overview

## Thinking in LangGraph
# https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
# 还写了个这个，thinking in python， like
# When you build an agent with LangGraph, you will first break it apart into discrete steps called nodes.
# Then, you will describe the different decisions and transitions from each of your nodes.
# Finally, you connect nodes together through a shared state that each node can read from and write to.
#
# 1. Step 1: Map out your workflow as discrete steps, Each step will become a node (a function that does one specific thing)\
# 2. Step 2: Identify what each step need to do
#   - LLM step: When a step needs to understand, analyze, generate text, or make reasoning decisions:
#   - Data step: When a step needs to retrieve information from external sources:
#   - Action step: When a step needs to perform an external action:
#   - User input steps: Human in the loop, When a step needs human intervention:
# 3. Design your state: State is the [shared memory] accessible to all nodes in your agent. Think of it as the notebook your agent uses to keep track of everything it learns and decides as it works through the process.
#   - Keep state raw, format prompts on-demand
# 4. Build your nodes: Now we implement each step as a function.
#   - A node in LangGraph is just a Python function that takes the current state and returns updates to it.
##！！！Handle errors apprapriately
# Error Type	Who Fixes It	Strategy	When to Use
# Transient errors (network issues, rate limits)	System (automatic)	Retry policy	Temporary failures that usually resolve on retry
# LLM-recoverable errors (tool failures, parsing issues)	LLM	Store error in state and loop back	LLM can see the error and adjust its approach
# User-fixable errors (missing information, unclear instructions)	Human	Pause with interrupt()	Need user input to proceed
# Unexpected errors	Developer	Let them bubble up	Unknown issues that need debugging
## !!! 卧槽！我突然意识到如果把这个 thinking in langgraph扔给codex，是不是可以把langgraph设计的更好！试一下！
# langgraph还有goto！

## Lang Graph Core benefits
# - LangGraph provides low-level supporting infrastructure for any long-running, stateful workflow or agent. LangGraph does not abstract prompts or architecture, and provides the following central benefits:
# - Durable execution: Build agents that persist through failures and can run for extended periods, resuming from where they left off.
# - Human-in-the-loop: Incorporate human oversight by inspecting and modifying agent state at any point.
# - Comprehensive memory: Create stateful agents with both short-term working memory for ongoing reasoning and long-term memory across sessions.
# - Debugging with LangSmith: Gain deep visibility into complex agent behavior with visualization tools that trace execution paths, capture state transitions, and provide detailed runtime metrics.
# - Production-ready deployment: Deploy sophisticated agent systems confidently with scalable infrastructure designed to handle the unique challenges of stateful, long-running workflows.


# MessagesState is LangGraph’s built-in state schema for chat-style workflows.
# It’s a TypedDict with a single key: messages: list[AnyMessage],
# annotated with add_messages so LangGraph automatically appends new messages rather than overwriting when nodes return {"messages": [...]}.
from langgraph.graph import StateGraph, MessagesState, START, END
from IPython.display import Image, display


def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}


def test_lang_graph_hello_world():
    # Build the smallest possible LangGraph:
    # - MessagesState tracks chat turns.
    # - Nodes are callables that take state and return an updated state dict.
    graph = StateGraph(MessagesState)

    # Register our single node. Its name defaults to the function name
    # ("mock_llm"), which we use when wiring edges below.
    graph.add_node(mock_llm)

    # Tell the graph to start at START, route to our node, then finish at END.
    # Edges must form a path from START to END or compile() will fail.
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)

    # compile() freezes the topology and returns a runnable app with .invoke().
    graph = graph.compile()

    # Kick off one pass through the graph with an initial user message.
    # The mock LLM node appends its reply and returns the new state.
    # 这里也可以看到，invoke的输入一个initial state，最终的返回应该也是一个state
    graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})

    display(Image(graph.get_graph().draw_mermaid_png()))
