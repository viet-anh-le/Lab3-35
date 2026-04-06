import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    v2 ReAct Agent with STRICT, WELL-ENGINEERED PROMPT.
    Implements full ReAct reasoning with mandatory tool execution and memory.
    
    Designed to demonstrate best practices in prompt engineering for tool-using agents.
    Contrasts with v1 which has identical architecture but poor prompt.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 10):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        EXTREMELY STRICT system prompt that FORCES tool usage.
        No hallucinations. No guessing. Tools first. Always.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        
        return f"""YOU ARE A TOOL-USING AGENT. YOU MUST USE TOOLS!!!

YOU HAVE EXACTLY THESE TOOLS (and ONLY these):
{tool_descriptions}

=== STRICT MANDATORY FORMAT ===
You WILL respond using ONLY this format:

Thought: [What information do I need? Which tool helps me get it?]
Action: tool_name(param1=value, param2=value)
Observation: [System will fill this in after tool execution]

Then repeat until you have ALL needed information.

ONLY when you have gathered information from tools, write:
Final Answer: [Complete answer based on tool results]

=== ABSOLUTE RULES (ZERO EXCEPTIONS) ===
1. FIRST RESPONSE MUST CALL A TOOL - No exceptions!
2. If asked about weather → ALWAYS call get_weather()
3. If asked about destination → ALWAYS call get_destination_info()
4. If asked about prices/flights → ALWAYS call get_flight_price()
5. If asked about hotels → ALWAYS call get_hotel_price()
6. If asked about activities → ALWAYS call check_availability()
7. NEVER guess or make up information - ONLY use tool results
8. NEVER put placeholder text like [information here]
9. Action format MUST be EXACTLY: action_name(key1=value1, key2=value2)
10. Do NOT add quotes around parameter values unless necessary
11. Do NOT apologize or explain why you can't do things - USE TOOLS
12. After each Observation, you must make a new Thought about next steps
13. Keep calling tools until you have COMPLETE information
14. "Final Answer" is forbidden until tools have been called

=== EXAMPLE: GOOD ===
User: "What's the weather in Paris on 2024-04-15?"
Thought: I need to call the weather tool to get accurate information about Paris.
Action: get_weather(city=Paris, date=2024-04-15)
Observation: [System: {{"status": "success", "city": "Paris", "temperature_celsius": 15, ...}}]
Thought: I now have the weather information. I can answer the user.
Final Answer: The weather in Paris on April 15, 2024 is partly cloudy with 15°C temperature.

=== EXAMPLE: UNACCEPTABLE ===
"Paris in April is usually pleasant with temperatures around 10-15 degrees..."
This is WRONG - you made it up without calling a tool!

=== ERROR HANDLING ===
If a tool fails, try a different tool or different parameters.
If all relevant tools fail, say: "I cannot find this information using available tools."

NOW START. USE TOOLS FIRST. NO HALLUCINATIONS."""

    def run(self, user_input: str) -> str:
        """
        Main ReAct loop implementation.
        Generates thoughts, executes actions, and processes observations.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
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
            
            # Check for Final Answer
            final_match = re.search(r"Final Answer:\s*(.+?)(?:\n\n|\Z)", response_text, re.DOTALL)
            if final_match:
                final_answer = final_match.group(1).strip()
                logger.log_event("FINAL_ANSWER_FOUND", {"step": steps, "answer": final_answer[:200]})
                break
            
            # Parse and execute Action
            action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", response_text)
            
            if not action_match:
                logger.log_event("NO_ACTION_FOUND", {"step": steps, "response": response_text[:200]})
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
                observation = f"Error executing {tool_name}: {str(e)}"
                logger.log_event("TOOL_ERROR", {
                    "step": steps,
                    "tool": tool_name,
                    "error": str(e)
                })
            
            # Append observation to conversation
            observation_msg = f"Observation: {observation}"
            messages.append({"role": "user", "content": observation_msg})
            
            steps += 1
        
        if final_answer is None:
            final_answer = "I couldn't find a complete answer. Please try again with more specific details."
            logger.log_event("MAX_STEPS_REACHED", {"steps": steps})
        
        logger.log_event("AGENT_END", {
            "steps": steps,
            "has_final_answer": final_answer is not None,
            "answer_preview": final_answer[:150] if final_answer else None
        })
        
        return final_answer

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format message history into a single prompt string."""
        formatted = ""
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            formatted += f"{role}: {content}\n\n"
        return formatted

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Execute a tool by name with parsed arguments.
        Handles argument parsing from string format.
        """
        # Find the tool
        tool_func = None
        for tool in self.tools:
            if tool['name'] == tool_name:
                tool_func = tool.get('function')
                tool_args = tool.get('args', [])
                break
        
        if not tool_func:
            return json.dumps({"status": "error", "message": f"Tool '{tool_name}' not found"})
        
        # Parse arguments: "origin=NYC, destination=Paris, departure_date=2024-06-15"
        try:
            args_dict = {}
            for arg_pair in args_str.split(','):
                arg_pair = arg_pair.strip()
                if '=' in arg_pair:
                    key, value = arg_pair.split('=', 1)
                    args_dict[key.strip()] = value.strip().strip('"\'')
            
            # Call the tool with parsed arguments
            result = tool_func(**args_dict)
            return result
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Error parsing/executing tool: {str(e)}"})

    def get_version_info(self) -> Dict[str, Any]:
        """Return metadata about this agent version"""
        return {
            "version": "v2",
            "name": "ReActAgent",
            "description": "ReAct agent with strict prompt engineering",
            "has_tools": True,
            "has_reasoning": True,
            "prompt_quality": "EXCELLENT - strict, mandatory tool forcing, no hallucinations",
            "max_steps": self.max_steps,
            "purpose": "Production-ready travel agent with best-practice prompting"
        }