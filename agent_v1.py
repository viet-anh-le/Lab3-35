import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgentV1BadPrompt:
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 10):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        DELIBERATELY BAD system prompt with vague instructions.
        Will cause:
        - Tool skipping
        - Hallucinations
        - Format confusion
        - Inconsistent reasoning
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        
        return f"""You are a travel assistant. You have access to some tools:

{tool_descriptions}

You can use these tools if needed. Try to be helpful and answer questions about travel.
Feel free to use your knowledge or the tools - whatever works best.
Just provide good travel advice."""

    def run(self, user_input: str) -> str:
        """
        Main ReAct loop with poor prompt engineering.
        """
        logger.log_event("AGENT_START", {
            "input": user_input, 
            "model": self.llm.model_name,
            "agent_version": "v1",
            "prompt_quality": "poor"
        })
        
        messages = [{"role": "user", "content": user_input}]
        steps = 0
        final_answer = None

        while steps < self.max_steps:
            # Generate LLM response
            response = self.llm.generate(
                prompt=user_input if steps == 0 else self._format_conversation(messages),
                system_prompt=self.get_system_prompt()
            )
            
            response_text = response.get("content", "")
            self.history.append({"role": "assistant", "content": response_text})
            messages.append({"role": "assistant", "content": response_text})
            
            logger.log_event("LLM_RESPONSE", {
                "step": steps,
                "response_length": len(response_text),
                "tokens": response.get("usage", {})
            })
            
            # Check for Final Answer (loose pattern)
            final_match = re.search(r"(?:Answer|Result|Response):\s*(.+?)(?:\n\n|\Z)", response_text, re.DOTALL | re.IGNORECASE)
            if final_match:
                final_answer = final_match.group(1).strip()
                logger.log_event("FINAL_ANSWER_FOUND", {
                    "step": steps,
                    "answer": final_answer[:200],
                    "directly_from_llm": True
                })
                break
            
            # Try to parse Action (very loose pattern)
            action_match = re.search(r"(?:Action|Tool):\s*(\w+)(?:\(|:)(.+?)(?:\)|\.)", response_text, re.IGNORECASE)
            
            if not action_match:
                # If no action found, just return what we have
                if len(response_text.strip()) > 50:
                    logger.log_event("NO_ACTION_FOUND", {
                        "step": steps,
                        "treating_as_final": True
                    })
                    final_answer = response_text.strip()
                    break
                steps += 1
                continue
            
            tool_name = action_match.group(1)
            args_str = action_match.group(2)
            
            logger.log_event("ACTION_PARSED", {
                "step": steps,
                "tool": tool_name,
                "args": args_str
            })
            
            # Execute the tool
            try:
                observation = self._execute_tool(tool_name, args_str)
                logger.log_event("TOOL_EXECUTED", {
                    "step": steps,
                    "tool": tool_name,
                    "observation_length": len(observation)
                })
            except Exception as e:
                observation = f"Couldn't get {tool_name} - {str(e)}"
                logger.log_event("TOOL_ERROR", {
                    "step": steps,
                    "tool": tool_name,
                    "error": str(e)
                })
            
            # Append observation
            observation_msg = f"Result: {observation}"
            messages.append({"role": "user", "content": observation_msg})
            
            steps += 1

        if not final_answer:
            final_answer = self.history[-1]["content"] if self.history else "No response"
        
        logger.log_event("AGENT_END", {
            "steps": steps,
            "has_final_answer": bool(final_answer),
            "answer_preview": final_answer[:100] if final_answer else ""
        })
        
        return final_answer

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation history for LLM"""
        formatted = []
        for msg in messages:
            formatted.append(f"{msg['role'].upper()}: {msg['content']}")
        return "\n".join(formatted)

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """Execute a tool by name and arguments"""
        # Try to find and execute the tool
        tool = next((t for t in self.tools if t['name'] == tool_name), None)
        
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Parse arguments - very basic parsing
        try:
            args_dict = {}
            for arg_pair in re.findall(r"(\w+)\s*=\s*(['\"]?)(.+?)\2(?:,|$)", args):
                key, _, value = arg_pair
                args_dict[key] = value
            
            result = tool['function'](**args_dict)
            return json.dumps(result) if isinstance(result, dict) else str(result)
        except Exception as e:
            raise Exception(f"Error executing {tool_name}: {str(e)}")

    def get_version_info(self) -> Dict[str, Any]:
        """Return metadata about this agent version"""
        return {
            "version": "v1",
            "name": "ReActAgentV1BadPrompt",
            "description": "ReAct agent with poor prompt engineering",
            "has_tools": True,
            "has_reasoning": True,
            "prompt_quality": "POOR - vague, permissive, allows hallucinations",
            "max_steps": self.max_steps,
            "purpose": "Demonstrate impact of prompt engineering on tool-using agents"
        }
