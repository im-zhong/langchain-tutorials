# 2025/6/25
# zhangzhong
# 既展示agent的决策过程，又可以stream token - 解决方案

from dotenv import load_dotenv

load_dotenv()

from langchain_deepseek import ChatDeepSeek
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import threading
import time

# 初始化
model = ChatDeepSeek(model="deepseek-chat", temperature=0)
search = TavilySearch(max_results=2)
tools = [search]
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)


def stream_with_decisions_and_tokens(input_message):
    """
    同时展示agent决策过程和流式token输出
    """
    print("🤖 开始处理...\n")

    # 用于同步两个流
    decision_complete = threading.Event()
    token_complete = threading.Event()

    def show_decisions():
        """展示决策过程"""
        try:
            for step in agent_executor.stream(
                {"messages": [input_message]}, stream_mode="values"
            ):
                latest_message = step["messages"][-1]

                # 检测工具调用
                if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
                    print(f"\n🔧 决策: 调用工具 {latest_message.tool_calls[0]['name']}")
                    print(f"   参数: {latest_message.tool_calls[0]['args']}")

                # 检测工具结果
                elif (
                    hasattr(latest_message, "tool_call_id")
                    and latest_message.tool_call_id
                ):
                    print(f"\n📊 工具执行完成: {latest_message.tool_name}")

                # 检测AI思考
                elif hasattr(latest_message, "content") and latest_message.content:
                    if "AI Message" in str(latest_message):
                        print(f"\n💭 AI正在思考...")

        except Exception as e:
            print(f"❌ 决策监控错误: {e}")
        finally:
            decision_complete.set()

    def stream_tokens():
        """流式输出token"""
        try:
            print("\n📝 实时响应:")
            for step, metadata in agent_executor.stream(
                {"messages": [input_message]}, stream_mode="messages"
            ):
                if metadata["langgraph_node"] == "agent":
                    # 流式输出AI的token
                    print(step.text(), end="", flush=True)

                elif metadata["langgraph_node"] == "tool":
                    # 工具执行提示
                    print(f"\n⚡ 执行工具: {step.tool_name}")

        except Exception as e:
            print(f"❌ Token流式输出错误: {e}")
        finally:
            token_complete.set()

    # 启动两个线程
    decision_thread = threading.Thread(target=show_decisions)
    token_thread = threading.Thread(target=stream_tokens)

    decision_thread.start()
    token_thread.start()

    # 等待两个线程完成
    decision_thread.join()
    token_thread.join()

    print("\n✅ 处理完成！")


# 使用示例
if __name__ == "__main__":
    # 测试问题
    test_questions = [
        {"role": "user", "content": "What's the weather in Beijing?"},
        {"role": "user", "content": "Tell me about the latest AI developments"},
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {question['content']}")
        print(f"{'='*60}")

        stream_with_decisions_and_tokens(question)
        time.sleep(2)
