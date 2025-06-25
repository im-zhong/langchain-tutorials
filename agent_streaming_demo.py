# 2025/6/25
# zhangzhong
# 演示如何同时实现agent决策过程展示和token流式输出

from dotenv import load_dotenv

load_dotenv()

from langchain_deepseek import ChatDeepSeek
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import asyncio
import threading
import time
from queue import Queue

# 初始化模型和工具
model = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

search = TavilySearch(max_results=2)
tools = [search]

# 创建agent
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)


class StreamingAgent:
    """结合决策过程展示和token流式输出的Agent类"""

    def __init__(self, agent_executor):
        self.agent_executor = agent_executor
        self.decision_queue = Queue()
        self.token_queue = Queue()

    def stream_with_decision_and_tokens(self, input_message):
        """同时展示决策过程和流式token输出"""

        print("🤖 开始处理请求...\n")

        # 启动决策过程监控线程
        decision_thread = threading.Thread(
            target=self._monitor_decisions, args=(input_message,)
        )
        decision_thread.start()

        # 启动token流式输出线程
        token_thread = threading.Thread(
            target=self._stream_tokens, args=(input_message,)
        )
        token_thread.start()

        # 等待两个线程完成
        decision_thread.join()
        token_thread.join()

        print("\n✅ 处理完成！")

    def _monitor_decisions(self, input_message):
        """监控agent的决策过程"""
        try:
            for step in self.agent_executor.stream(
                {"messages": [input_message]}, stream_mode="values"
            ):
                latest_message = step["messages"][-1]

                # 分析消息类型并展示决策过程
                if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
                    print(f"\n🔧 决策: 调用工具 {latest_message.tool_calls[0]['name']}")
                    print(f"   参数: {latest_message.tool_calls[0]['args']}")
                    print(f"   调用ID: {latest_message.tool_calls[0]['id']}")

                elif (
                    hasattr(latest_message, "tool_call_id")
                    and latest_message.tool_call_id
                ):
                    print(f"\n📊 工具执行结果:")
                    print(f"   工具: {latest_message.tool_name}")
                    print(f"   结果: {str(latest_message.content)[:100]}...")

                elif hasattr(latest_message, "content") and latest_message.content:
                    if "AI Message" in str(latest_message):
                        print(f"\n💭 AI思考过程: {str(latest_message.content)[:50]}...")

                time.sleep(0.1)  # 避免输出过快

        except Exception as e:
            print(f"❌ 决策监控错误: {e}")

    def _stream_tokens(self, input_message):
        """流式输出token"""
        try:
            print("\n📝 实时响应:")
            for step, metadata in self.agent_executor.stream(
                {"messages": [input_message]}, stream_mode="messages"
            ):
                if metadata["langgraph_node"] == "agent":
                    # 流式输出AI的token
                    print(step.text(), end="", flush=True)

                elif metadata["langgraph_node"] == "tool":
                    # 工具执行时的提示
                    print(f"\n⚡ 正在执行工具: {step.tool_name}")

        except Exception as e:
            print(f"❌ Token流式输出错误: {e}")


# 使用示例
def demo_basic_streaming():
    """基础流式输出演示"""
    print("=== 基础流式输出演示 ===")
    input_message = {"role": "user", "content": "Search for the weather in SF"}

    print("1. 只显示决策过程:")
    for step in agent_executor.stream(
        {"messages": [input_message]}, stream_mode="values"
    ):
        step["messages"][-1].pretty_print()
        break  # 只显示第一步

    print("\n2. 只显示token流式输出:")
    for step, metadata in agent_executor.stream(
        {"messages": [input_message]}, stream_mode="messages"
    ):
        if metadata["langgraph_node"] == "agent":
            print(step.text(), end="", flush=True)
        break  # 只显示第一步


def demo_combined_streaming():
    """结合决策过程和token流式输出"""
    print("\n=== 结合决策过程和token流式输出 ===")

    streaming_agent = StreamingAgent(agent_executor)

    # 测试不同的问题
    test_questions = [
        {"role": "user", "content": "What's the weather in Beijing?"},
        {"role": "user", "content": "Tell me about the latest AI developments"},
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"测试 {i}: {question['content']}")
        print(f"{'='*50}")

        streaming_agent.stream_with_decision_and_tokens(question)
        time.sleep(2)  # 间隔


def demo_async_streaming():
    """异步流式输出演示"""
    print("\n=== 异步流式输出演示 ===")

    async def async_stream():
        input_message = {
            "role": "user",
            "content": "Search for Python programming tutorials",
        }

        async for step in agent_executor.astream(
            {"messages": [input_message]}, stream_mode="messages"
        ):
            if step[1]["langgraph_node"] == "agent":
                print(step[0].text(), end="", flush=True)

    asyncio.run(async_stream())


if __name__ == "__main__":
    print("🚀 LangGraph Agent 流式输出演示")
    print("=" * 60)

    # 运行演示
    demo_basic_streaming()
    demo_combined_streaming()
    demo_async_streaming()
