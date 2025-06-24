# 2025/6/24
# zhangzhong
# https://python.langchain.com/docs/tutorials/llm_chain/


import getpass
import os

try:
    # load environment variables from .env file (requires `python-dotenv`)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

os.environ["LANGSMITH_TRACING"] = "true"
if "LANGSMITH_API_KEY" not in os.environ:
    os.environ["LANGSMITH_API_KEY"] = getpass.getpass(
        prompt="Enter your LangSmith API key (optional): "
    )
if "LANGSMITH_PROJECT" not in os.environ:
    os.environ["LANGSMITH_PROJECT"] = getpass.getpass(
        prompt='Enter your LangSmith Project Name (default = "default"): '
    )
    if not os.environ.get("LANGSMITH_PROJECT"):
        os.environ["LANGSMITH_PROJECT"] = "default"


# https://python.langchain.com/docs/integrations/chat/deepseek/
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


if not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")

model = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)


messages = [
    SystemMessage("Translate the following from English into Italian"),
    HumanMessage("hi!"),
]

response = model.invoke(messages)
print(response)


# stream
for token in model.stream(messages):
    print(token.content, end="|", flush=True)


# prompt template
system_template = "Translate the following from English into {language}"
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", system_template),
        ("human", "{text}"),
    ]
)

prompt = prompt_template.invoke({"language": "Italian", "text": "hi!"})
print(prompt.to_messages())

response = model.invoke(prompt)
print(response)
