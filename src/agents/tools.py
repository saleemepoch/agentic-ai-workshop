"""
Tools available to agent nodes.

Currently, agent nodes call LLM and retrieval functions directly.
This module is a placeholder for future tool definitions if we
move to a tool-calling agent pattern (where the LLM decides which
tools to invoke rather than the graph structure dictating it).

Interview talking points:
- Why aren't we using LangGraph's tool-calling pattern? Because the
  recruitment workflow has a known structure — we know the steps in
  advance. Tool-calling agents are better for open-ended tasks where
  the agent needs to decide what to do next. Our graph structure IS
  the decision logic.
- When would you use tool-calling? When the workflow isn't predetermined.
  E.g., a research agent that might need to search the web, query a
  database, or call an API depending on what it finds.
"""
