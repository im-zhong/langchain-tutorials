# readme

## how to

1. <https://python.langchain.com/docs/how_to/>
2. how to里面有很多东西 看起来非常有帮助

## function call principle

# 大模型function call和function tool原理

_Exported on 6/25/2025 at 08:49:43 GMT+8 from Cursor (1.1.3)_

---

**User**

大模型function call，function tool的具体原理

---

**Cursor**

我来帮你详细解释大模型function call和function tool的具体原理。首先让我查看一下你的代码，了解具体的实现情况。

现在让我查看一下utils.py文件，了解更多上下文：

现在让我查看一下translation.py文件，看看是否有更多相关的实现：

现在让我搜索一下项目中是否有更多关于function call的实现：

基于你的代码和问题，我来详细解释大模型function call和function tool的具体原理：

## 大模型Function Call和Function Tool的原理

### 1. 基本概念

**Function Call** 和 **Function Tool** 是大模型与外部系统交互的核心机制，允许模型调用预定义的函数来执行特定任务。

### 2. 从你的代码看实现原理

在你的 `classification.ipynb` 中，你使用了 `with_structured_output(Classification)` 方法：

```python
class Classification(BaseModel):
    sentiment: str = Field(..., enum=["happy", "neutral", "sad"])
    aggressiveness: int = Field(..., enum=[1, 2, 3, 4, 5])
    language: str = Field(..., enum=["spanish", "english", "french", "german", "italian"])

structured_llm = model.with_structured_output(Classification)
```

### 3. 内部实现机制

#### 3.1 Pydantic模型转换为Function Schema

当你调用 `with_structured_output(Classification)` 时，LangChain内部会：

1. **解析Pydantic模型**：将你的 `Classification` 类转换为OpenAI Function Calling格式的schema
2. **生成Function Definition**：创建类似这样的函数定义：

```json
{
  "name": "Classification",
  "description": "Extract classification information from text",
  "parameters": {
    "type": "object",
    "properties": {
      "sentiment": {
        "type": "string",
        "enum": ["happy", "neutral", "sad"]
      },
      "aggressiveness": {
        "type": "integer",
        "description": "describes how aggressive the statement is, the higher the number the more aggressive",
        "enum": [1, 2, 3, 4, 5]
      },
      "language": {
        "type": "string",
        "enum": ["spanish", "english", "french", "german", "italian"]
      }
    },
    "required": ["sentiment", "aggressiveness", "language"]
  }
}
```

#### 3.2 模型调用过程

1. **发送请求**：将用户输入和函数定义一起发送给大模型
2. **模型推理**：大模型根据输入文本和函数schema进行推理
3. **返回结构化数据**：模型返回符合schema的JSON数据
4. **验证和转换**：LangChain验证返回的数据是否符合Pydantic模型，并转换为Python对象

### 4. Function Tool的扩展机制

#### 4.1 工具定义

Function Tool允许你定义更复杂的工具：

```python
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get the current weather in a given location"""
    # 实际调用天气API
    return f"Weather in {location}: sunny, 25°C"

@tool
def calculate(expression: str) -> float:
    """Calculate the result of a mathematical expression"""
    return eval(expression)
```

#### 4.2 工具调用流程

1. **工具注册**：将工具函数注册到模型
2. **模型选择**：模型根据用户需求选择合适的工具
3. **参数提取**：模型从用户输入中提取工具所需的参数
4. **工具执行**：调用实际的工具函数
5. **结果返回**：将工具执行结果返回给用户

### 5. 底层技术原理

#### 5.1 提示工程

Function Call本质上是一种特殊的提示工程技术：

```
System: You have access to the following functions:
[function definitions]

User: [user input]

Assistant: I'll use the [function_name] function with parameters: [parameters]
```

#### 5.2 模型训练

大模型在训练时学习了：

- 如何理解函数定义
- 如何从文本中提取参数
- 如何选择合适的函数
- 如何格式化输出

#### 5.3 推理过程

1. **输入编码**：将用户输入和函数定义编码为token
2. **注意力机制**：模型关注函数定义和用户输入的相关部分
3. **参数推理**：基于上下文推理出合适的参数值
4. **输出生成**：生成符合函数schema的输出

### 6. 实际应用场景

#### 6.1 结构化数据提取

```python
# 从非结构化文本中提取结构化信息
response = structured_llm.invoke("I'm feeling great today!")
# 返回: Classification(sentiment='happy', aggressiveness=1, language='english')
```

#### 6.2 工具调用

```python
# 调用外部API或执行计算
response = model.invoke("What's the weather in Beijing?")
# 模型会调用get_weather("Beijing")工具
```

#### 6.3 多步骤推理

```python
# 模型可以链式调用多个工具
response = model.invoke("Calculate the area of a circle with radius 5 and tell me the weather")
# 1. 调用calculate("3.14159 * 5 * 5")
# 2. 调用get_weather("current_location")
```

### 7. 优势与特点

1. **类型安全**：通过Pydantic模型确保输出格式正确
2. **可扩展性**：可以轻松添加新的工具和函数
3. **可解释性**：模型会解释为什么选择某个工具
4. **错误处理**：内置参数验证和错误处理机制

这种机制让大模型从纯文本生成器变成了可以执行具体任务的智能助手，是构建AI应用的重要基础技术。

```python
class Classification(BaseModel):
    sentiment: str = Field(..., enum=["happy", "neutral", "sad"])
    aggressiveness: int = Field(..., enum=[1, 2, 3, 4, 5])
    language: str = Field(..., enum=["spanish", "english", "french", "german", "italian"])

structured_llm = model.with_structured_output(Classification)
```

```json
{
  "name": "Classification",
  "description": "Extract classification information from text",
  "parameters": {
    "type": "object",
    "properties": {
      "sentiment": {
        "type": "string",
        "enum": ["happy", "neutral", "sad"]
      },
      "aggressiveness": {
        "type": "integer",
        "description": "describes how aggressive the statement is, the higher the number the more aggressive",
        "enum": [1, 2, 3, 4, 5]
      },
      "language": {
        "type": "string",
        "enum": ["spanish", "english", "french", "german", "italian"]
      }
    },
    "required": ["sentiment", "aggressiveness", "language"]
  }
}
```

```python
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get the current weather in a given location"""
    # 实际调用天气API
    return f"Weather in {location}: sunny, 25°C"

@tool
def calculate(expression: str) -> float:
    """Calculate the result of a mathematical expression"""
    return eval(expression)
```

```plaintext
System: You have access to the following functions:
[function definitions]

User: [user input]

Assistant: I'll use the [function_name] function with parameters: [parameters]
```

```python
# 从非结构化文本中提取结构化信息
response = structured_llm.invoke("I'm feeling great today!")
# 返回: Classification(sentiment='happy', aggressiveness=1, language='english')
```

```python
# 调用外部API或执行计算
response = model.invoke("What's the weather in Beijing?")
# 模型会调用get_weather("Beijing")工具
```

```python
# 模型可以链式调用多个工具
response = model.invoke("Calculate the area of a circle with radius 5 and tell me the weather")
# 1. 调用calculate("3.14159 * 5 * 5")
# 2. 调用get_weather("current_location")
```
