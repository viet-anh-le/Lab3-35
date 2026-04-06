import os
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ChatBot:
    """
    CHATBOT - Baseline chatbot that only uses OpenAI API.
    NO tools, NO external APIs, NO reasoning framework.
    Purpose: Comparison baseline against v1 & v2 ReAct agents.
    
    This demonstrates what happens when you just ask GPT directly
    without structured reasoning or tool usage.
    """
    
    def __init__(self, llm: LLMProvider, max_steps: int = 1):
        self.llm = llm
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Simple system prompt - minimal instructions.
        Just ask the model to be helpful with travel planning.
        No tools, no special formatting, no reasoning framework.
        """
        return """You are a helpful travel planning assistant. 
        Answer questions about travel destinations, hotels, flights, weather, and activities.
        Be informative and provide practical advice.
        """

    def run(self, user_input: str) -> str:
        """
        v1 SIMPLE AGENT: Direct LLM call without structured reasoning.
        
        Flow:
        1. Take user input
        2. Call LLM directly with system prompt
        3. Return response immediately
        4. NO tool calling, NO multi-step reasoning
        """
        logger.log_event("AGENT_START", {
            "input": user_input, 
            "model": self.llm.model_name,
            "agent_version": "baseline",
            "agent_name": "ChatBot",
            "has_tools": False
        })
        
        # Single LLM call using the generate method
        result = self.llm.generate(
            prompt=user_input,
            system_prompt=self.get_system_prompt()
        )
        
        response = result.get("content", "")
        usage = result.get("usage", {})
        
        logger.log_event("LLM_RESPONSE", {
            "response_length": len(response),
            "tokens": usage
        })
        
        # Log final answer
        logger.log_event("FINAL_ANSWER_FOUND", {
            "answer": response[:200],
            "direct_answer": True
        })
        
        logger.log_event("AGENT_END", {
            "steps": 1,
            "has_final_answer": True,
            "answer_preview": response[:100]
        })
        
        return response

    def get_version_info(self) -> Dict[str, Any]:
        """Return metadata about this agent version"""
        return {
            "version": "baseline",
            "name": "ChatBot",
            "description": "Simple chatbot - direct OpenAI calls only",
            "has_tools": False,
            "has_reasoning": False,
            "max_steps": 1,
            "purpose": "Comparison baseline against ReAct agents (v1, v2)"
        }

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                # TODO: Implement dynamic function calling or simple if/else
                return f"Result of {tool_name}"
        return f"Tool {tool_name} not found."
