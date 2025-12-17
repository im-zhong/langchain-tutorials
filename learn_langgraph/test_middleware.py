# https://docs.langchain.com/oss/python/langchain/middleware/built-in#content-moderation
# 现在有middleware了
# Middleware	Description
# Summarization	Automatically summarize conversation history when approaching token limits.
# Human-in-the-loop	Pause execution for human approval of tool calls.
# Model call limit	Limit the number of model calls to prevent excessive costs.
# Tool call limit	Control tool execution by limiting call counts.
# Model fallback	Automatically fallback to alternative models when primary fails.
# PII detection	Detect and handle Personally Identifiable Information (PII).
# To-do list	Equip agents with task planning and tracking capabilities.
# LLM tool selector	Use an LLM to select relevant tools before calling main model.
# Tool retry	Automatically retry failed tool calls with exponential backoff.
# Model retry	Automatically retry failed model calls with exponential backoff.
# LLM tool emulator	Emulate tool execution using an LLM for testing purposes.
# Context editing	Manage conversation context by trimming or clearing tool uses.
# Shell tool	Expose a persistent shell session to agents for command execution.
# File search	Provide Glob and Grep search tools over filesystem files.
