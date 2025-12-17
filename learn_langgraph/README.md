# New LangGraph Project

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

This template demonstrates a simple application implemented using [LangGraph](https://github.com/langchain-ai/langgraph), designed for showing how to get started with [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/#langgraph-server) and using [LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/), a visual debugging IDE.

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

The core logic defined in `src/agent/graph.py`, showcases an single-step application that responds with a fixed string and the configuration provided.

You can extend this graph to orchestrate more complex agentic workflows that can be visualized and debugged in LangGraph Studio.

## Getting Started

1. Install dependencies, along with the [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/), which will be used to run the server.

```bash
cd path/to/your/app
pip install -e . "langgraph-cli[inmem]"
```

2. (Optional) Customize the code and project as needed. Create a `.env` file if you need to use secrets.

```bash
cp .env.example .env
```

If you want to enable LangSmith tracing, add your LangSmith API key to the `.env` file.

```text
# .env
LANGSMITH_API_KEY=lsv2...
```

3. Start the LangGraph Server.

```shell
langgraph dev
```

For more information on getting started with LangGraph Server, [see here](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/).

## How to customize

1. **Define runtime context**: Modify the `Context` class in the `graph.py` file to expose the arguments you want to configure per assistant. For example, in a chatbot application you may want to define a dynamic system prompt or LLM to use. For more information on runtime context in LangGraph, [see here](https://langchain-ai.github.io/langgraph/agents/context/?h=context#static-runtime-context).

2. **Extend the graph**: The core logic of the application is defined in [graph.py](./src/agent/graph.py). You can modify this file to add new nodes, edges, or change the flow of information.

## Development

While iterating on your graph in LangGraph Studio, you can edit past state and rerun your app from previous states to debug specific nodes. Local changes will be automatically applied via hot reload.

Follow-up requests extend the same thread. You can create an entirely new thread, clearing previous history, using the `+` button in the top right.

For more advanced features and examples, refer to the [LangGraph documentation](https://langchain-ai.github.io/langgraph/). These resources can help you adapt this template for your specific use case and build more sophisticated conversational agents.

LangGraph Studio also integrates with [LangSmith](https://smith.langchain.com/) for more in-depth tracing and collaboration with teammates, allowing you to analyze and optimize your chatbot's performance.

## Email agent

![alt text](email-agent.png)

- Read Email: Extract and parse the email content
- Classify Intent: Use an LLM to categorize urgency and topic, then route to appropriate action (LLM structured output?)
- Doc Search: Query your knowledge base for relevant information
- Bug Track: Create or update issue in tracking system
- Draft Reply: Generate an appropriate response
- Human Review: Escalate to human agent for approval or handling
- Send Reply: Dispatch the email response

## Step 2: Identify what each step needs to do

- LLM steps: When a step needs to understand, analyze, generate text, or make reasoning decisions
- Data steps: When a step needs to retrieve information from external sources
- Action steps: When a step needs to perform an external action
- User input steps: When a step needs human intervention

## Step 3: Design your state. Keep state raw, format prompts on-demand

State is the shared memory accessible to all nodes in your agent
Think of it as the notebook your agent uses to keep track of everything it learns and decides as it works through the process.

## Step 4: Build your nodes

Now we implement each step as a function.
A node in LangGraph is just a Python function that takes the current state and returns updates to it.
*nodes take state, do work, and return updates.*

| Error Type            | Who Fixes It | Strategy                         | When to Use |
|----------------------|-------------|----------------------------------|-------------|
| Transient errors     | System      | Automatic retry policy           | Temporary failures such as network issues or rate limits that usually resolve on retry |
| LLM-recoverable errors | LLM         | Store error in state and loop back | Tool failures or parsing issues where the LLM can see the error and adjust its approach |
| User-fixable errors  | Human       | Pause execution with `interrupt()` | Missing information or unclear instructions that require user input |
| Unexpected errors    | Developer   | Let the error bubble up          | Unknown or critical issues that require debugging |

