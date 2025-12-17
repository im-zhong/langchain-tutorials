"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

# https://github.com/langchain-ai/new-langgraph-project
# https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph

## Thinking in LangGraph
# - When you build an agent with LangGraph, you will first break it apart into discrete steps called [nodes].
# - Then, you will describe the different [decisions and transitions] from each of your nodes.
# - Finally, you connect nodes together through a [shared state] that each node can read from and write to.

## Start with the process you want to automate
# The agent should:

# - Read incoming customer emails
# - Classify them by urgency and topic
# - Search relevant documentation to answer questions
# - Draft appropriate responses
# - Escalate complex issues to human agents
# - Schedule follow-ups when needed

# Example scenarios to handle:

# 1. Simple product question: "How do I reset my password?"
# 2. Bug report: "The export feature crashes when I select PDF format"
# 3. Urgent billing issue: "I was charged twice for my subscription!"
# 4. Feature request: "Can you add dark mode to the mobile app?"
# 5. Complex technical issue: "Our API integration fails intermittently with 504 errors"

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from typing_extensions import TypedDict
from langgraph.types import interrupt, Command, RetryPolicy
from langchain_deepseek import ChatDeepSeek
from langchain.messages import HumanMessage


# need a llm, we just use deepseek
def get_deepseek_chat_model() -> ChatDeepSeek:
    return ChatDeepSeek(
        model="deepseek-chat",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key="sk-f433ba63a16a4c89b2637b4c3b035da1",
    )


llm = get_deepseek_chat_model()


class Context(TypedDict):
    """Context parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str


# Define the structure for email classification
class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str


# state contains only raw data:
# - no prompt templates,
# - no formatted strings,
# - no instructions.
# - The classification output is stored as a single dictionary, straight from the LLM.
class EmailAgentState(TypedDict):
    # Raw email data
    email_content: str
    sender_email: str
    email_id: str

    # Classification result
    classification: EmailClassification | None

    # Raw search/API results
    search_results: list[str] | None  # List of raw document chunks
    customer_history: dict | None  # Raw customer data from CRM

    # Generated content
    draft_response: str | None
    messages: (
        list[str] | None
    )  # 这里的类型也不对呀，read_email里面是list[Message], 这里是list[str]


# Now we implement each step as a function.
# A node in LangGraph is just a Python function that takes the current state and returns updates to it.


# 这里应该是一个Data step，要从邮箱里面获取邮件
def read_email(state: EmailAgentState) -> dict:
    """Extract and parse email content"""
    # In production, this would connect to your email service
    return {
        "messages": [
            HumanMessage(content=f"Processing email: {state['email_content']}")
        ]
    }


# LLM step of Classify intent
# - Static context (prompt): Classification categories, urgency definitions, response format
# - Dynamic context (from state): Email content, sender information
# - Desired outcome: Structured classification that determines routing
def classify_intent(
    state: EmailAgentState,
) -> Command[
    Literal["search_documentation", "human_review", "draft_response", "bug_tracking"]
]:  # 要在返回类型里面写清楚可能的下一个节点
    """Use LLM to classify email intent and urgency, then route accordingly"""

    # Create structured LLM that returns EmailClassification dict
    structured_llm = llm.with_structured_output(EmailClassification, method="json_mode")

    # Format the prompt on-demand, not stored in state
    classification_prompt = f"""
    Analyze this customer email and classify it in json:

    Email: {state["email_content"]}
    From: {state["sender_email"]}

    Provide classification including intent, urgency, topic, and summary.
    """

    # Get structured response directly as dict
    classification = structured_llm.invoke(classification_prompt)

    # Determine next node based on classification
    if classification["intent"] == "billing" or classification["urgency"] == "critical":
        goto = "human_review"
    elif classification["intent"] in ["question", "feature"]:
        goto = "search_documentation"
    elif classification["intent"] == "bug":
        goto = "bug_tracking"
    else:
        # TODO: 讲道理，如果大模型遇到不能分辨intent的邮件，应该转另一个流程吧，而不是直接到下一步，都没有人工控制
        goto = "draft_response"

    # Store classification as a single dict in state
    # 原来如此！是这样在节点内部做分支选择的
    # update的这一部分就是简化的函数的返回的部分，用来合并并更新shared state
    return Command(update={"classification": classification}, goto=goto)


# Data step: Document search
# 可以看到，所有的node的输入参数都是state，输出都是command with next nodes
# - Parameters: Query built from intent and topic
# - Retry strategy: Yes, with exponential backoff for transient failures
# - Caching: Could cache common queries to reduce API calls ?
def search_documentation(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """Search knowledge base for relevant information"""

    # Build search query from classification
    classification = state.get("classification", {})
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"

    try:
        # Implement your search logic here
        # Store raw search results, not formatted text
        search_results = [
            "Reset password via Settings > Security > Change Password",
            "Password must be at least 12 characters",
            "Include uppercase, lowercase, numbers, and symbols",
        ]
    except SearchAPIError as e:
        # For recoverable search errors, store error and continue
        search_results = [f"Search temporarily unavailable: {str(e)}"]

    return Command(
        update={"search_results": search_results},  # Store raw results or error
        goto="draft_response",
    )


# Action step: Bug track
# - When to execute node: Always when intent is “bug”
# - Retry strategy: Yes, critical to not lose bug reports
# - Returns: Ticket ID to include in response
def bug_tracking(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """Create or update bug tracking ticket"""

    # Create ticket in your bug tracking system
    # 我明白了，这里应该是调用issue服务的api，创建一个新的issue，所以是action step
    ticket_id = "BUG-12345"  # Would be created via API

    return Command(
        update={
            "search_results": [f"Bug ticket {ticket_id} created"],
            # 还可以指定当前的step，为什么呢？是不是没有必要？
            # 而且state里面也没有这个filed呀
            "current_step": "bug_tracked",
        },
        goto="draft_response",
    )


# LLM step: Draft reply
# - Static context (prompt): Tone guidelines, company policies, response templates
# - Dynamic context (from state): Classification results, search results, customer history
# - Desired outcome: Professional email response ready for review
# 依然是这样的输入参数和返回值
# 当然，langgraph的node也是支持更多的参数的
# # Yes. LangGraph will “inject” what you declare in the node signature:
# def call_model(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
def draft_response(
    state: EmailAgentState,
) -> Command[Literal["human_review", "send_reply"]]:
    """Generate response using context and route based on quality"""

    classification = state.get("classification", {})

    # Format context from raw state data on-demand
    context_sections = []

    if state.get("search_results"):
        # Format search results for the prompt
        formatted_docs = "\n".join([f"- {doc}" for doc in state["search_results"]])
        context_sections.append(f"Relevant documentation:\n{formatted_docs}")

    if state.get("customer_history"):
        # Format customer data for the prompt
        context_sections.append(
            f"Customer tier: {state['customer_history'].get('tier', 'standard')}"
        )

    # Build the prompt with formatted context
    draft_prompt = f"""
    Draft a response to this customer email:
    {state["email_content"]}

    Email intent: {classification.get("intent", "unknown")}
    Urgency level: {classification.get("urgency", "medium")}

    {chr(10).join(context_sections)}

    Guidelines:
    - Be professional and helpful
    - Address their specific concern
    - Use the provided documentation when relevant
    """

    response = llm.invoke(draft_prompt)

    # Determine if human review needed based on urgency and intent
    needs_review = (
        classification.get("urgency") in ["high", "critical"]
        or classification.get("intent") == "complex"
    )

    # Route to appropriate next node
    goto = "human_review" if needs_review else "send_reply"

    return Command(
        update={"draft_response": response.content},  # Store only the raw response
        goto=goto,
    )


##
def human_review(state: EmailAgentState) -> Command[Literal["send_reply", END]]:
    """Pause for human review using interrupt and route based on decision"""

    classification = state.get("classification", {})

    # interrupt() must come first - any code before it will re-run on resume
    human_decision = interrupt(
        {
            "email_id": state.get("email_id", ""),
            "original_email": state.get("email_content", ""),
            "draft_response": state.get("draft_response", ""),
            "urgency": classification.get("urgency"),
            "intent": classification.get("intent"),
            "action": "Please review and approve/edit this response",
        }
    )

    # Now process the human's decision
    if human_decision.get("approved"):
        return Command(
            update={
                "draft_response": human_decision.get(
                    "edited_response", state.get("draft_response", "")
                )
            },
            goto="send_reply",
        )
    else:
        # Rejection means human will handle directly
        return Command(update={}, goto=END)


# Action step
def send_reply(state: EmailAgentState) -> dict:
    """Send the email response"""
    # Integrate with email service
    # print(f"Sending reply: {state['draft_response'][:100]}...")
    # return {}
    ## handle errors:
    # Unexpected errors
    # Let them bubble up for debugging. Don’t catch what you can’t handle:
    try:
        email_service.send(state["draft_response"])
    except Exception:
        raise  # Surface unexpected errors


## handle errors
# LLM-recoverable errors (tool failures, parsing issues)
def execute_tool(state: State) -> Command[Literal["agent", "execute_tool"]]:
    try:
        result = run_tool(state["tool_call"])
        return Command(update={"tool_result": result}, goto="agent")
    except ToolError as e:
        # 这里应该是我们自己创建了一个往回跳的loop吧，是需要我们自己处理的
        # Let the LLM see what went wrong and try again
        return Command(update={"tool_result": f"Tool error: {str(e)}"}, goto="agent")


## handle errors
# User-fixable errors (missing information, unclear instructions)
## Data steps:
# - Parameters: Customer email or ID from state
# - Retry strategy: Yes, but with fallback to basic info if unavailable
# - Caching: Yes, with time-to-live to balance freshness and performance
def lookup_customer_history(state: State) -> Command[Literal["draft_response"]]:
    if not state.get("customer_id"):
        user_input = interrupt(
            {
                "message": "Customer ID needed",
                "request": "Please provide the customer's account ID to look up their subscription history",
            }
        )
        # !!!这里创建了一个loop
        return Command(
            update={"customer_id": user_input["customer_id"]},
            goto="lookup_customer_history",
        )
    # Now proceed with the lookup
    customer_data = fetch_customer_history(state["customer_id"])
    return Command(update={"customer_history": customer_data}, goto="draft_response")


## Write it together
# - To enable human-in-the-loop with interrupt(), we need to compile with a checkpointer to save state between runs:
# - Now we connect our nodes into a working graph. Since our nodes handle their own routing decisions, we only need a few essential edges.
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy

# Create the graph
workflow = StateGraph(EmailAgentState)

# 要添加的node一个不少
# Add nodes with appropriate error handling
workflow.add_node("read_email", read_email)
workflow.add_node("classify_intent", classify_intent)

# Add retry policy for nodes that might have transient failures
workflow.add_node(
    "search_documentation",
    search_documentation,
    ## handle errors
    # Transient errors (network issues, rate limits)
    # Add a retry policy to automatically retry network issues and rate limits:
    retry_policy=RetryPolicy(max_attempts=3),
)
workflow.add_node("bug_tracking", bug_tracking)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_reply", send_reply)

# 就是edge不用在额外添加了，因为node自己都写好了
# Add only the essential edges
workflow.add_edge(START, "read_email")
workflow.add_edge("read_email", "classify_intent")
workflow.add_edge("send_reply", END)

# Compile with checkpointer for persistence, in case run graph with Local_Server --> Please compile without checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


## initial calling example
# Test with an urgent billing issue
initial_state = {
    "email_content": "I was charged twice for my subscription! This is urgent!",
    "sender_email": "customer@example.com",
    "email_id": "email_123",
    "messages": [],
}

# Run with a thread_id for persistence
config = {"configurable": {"thread_id": "customer_123"}}
result = app.invoke(initial_state, config)
# The graph will pause at human_review
print(f"human review interrupt:{result['__interrupt__']}")

# When ready, provide human input to resume
from langgraph.types import Command


# TODO: 关于human in the loop这块还需要额外的研究
# The graph pauses when it hits interrupt(), saves everything to the checkpointer, and waits.
# It can resume days later, picking up exactly where it left off.
# The thread_id ensures all state for this conversation is preserved together.
human_response = Command(
    resume={
        "approved": True,
        "edited_response": "We sincerely apologize for the double charge. I've initiated an immediate refund...",
    }
)

# Resume execution
final_result = app.invoke(human_response, config)
print(f"Email sent successfully!")


## template code


@dataclass
class State:
    """Input state for the agent.

    Defines the initial structure of incoming data.
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """

    changeme: str = "example"


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """
    return {
        "changeme": "output from call_model. "
        f"Configured with {(runtime.context or {}).get('my_configurable_param')}"
    }


# Define the graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node(call_model)
    .add_edge("__start__", "call_model")
    .compile(name="New Graph")
)
