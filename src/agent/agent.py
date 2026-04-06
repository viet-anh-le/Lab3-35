import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t.get('description','no description')}" for t in self.tools]
        )
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        If the user's intent is planning, the agent MUST follow this exact sequence when the user's intent is to plan a trip:

        Step 1: Call weather tool
            - Input: (normalized_location, start_date, end_date)
            - Output: Weather forecast for the trip
            - Purpose: Use weather to decide whether activities should be indoor/outdoor and to inform packing/advice.

        Step 2: Call search_flights
            - Input: (origin, normalized_location, start_date, end_date, preferences?)
            - Output: A short list of candidate flights (price, carrier, depart/arrive times, duration)
            - Purpose: Find feasible travel options and estimate travel time/cost.

        Step 3: Call search_attractions
            - Input: (normalized_location, start_date, end_date, interests?)
            - Output: Ranked attractions/activities with brief reasons and estimated duration per activity
            - Purpose: Propose daily activities and note which are indoor/outdoor (use weather from Step 1).

        Step 4: Aggregate results
            - Combine outputs from Steps 1-3 into a concise context for the LLM.
            - Analyze constraints (weather, flight times, durations) and produce 1-3 itinerary options.
            - For each option provide: daily schedule, transportation notes (flight), estimated costs, and packing/weather advice.

        Step 5: Return Final Answer
            - Input: aggregated context + selected itinerary
            - Output: A human-readable itinerary and short justification. The Final Answer must include the key tool outputs (weather summary, top flights, top attractions) as an appendix or inline summary.

        Use the following format exactly (for the agent to parse your output):
        Thought: <your reasoning here>
        Action: <tool_name>(<arguments>)
        Observation: <result of the tool call>
        ... (repeat Thought/Action/Observation if needed)
        Final Answer: <your final response>
        Notes:
        - <arguments> may be a plain string, JSON object, or positional comma-separated values.
        - Only call tools listed above. If you cannot answer, return a Final Answer.
        """

    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event(
            "AGENT_START", {"input": user_input, "model": getattr(self.llm, "model_name", None)}
        )

        system_prompt = self.get_system_prompt()
        # conversation buffer that we feed to the LLM (system_prompt is separate)
        # Build buffer from stored history (if any) followed by the new user input
        parts = []
        for h in self.history:
            if isinstance(h, dict):
                if "user" in h:
                    parts.append(f"User: {h['user']}")
                if "llm" in h:
                    parts.append(f"Assistant: {h['llm']}")
                if "observation" in h:
                    parts.append(f"Observation: {h['observation']}")
            else:
                parts.append(str(h))

        # append current user input and store it in history for future turns
        parts.append(f"User: {user_input}")
        self.history.append({"user": user_input})
        buffer = "\n".join(parts)
        steps = 0

        while steps < self.max_steps:
            steps += 1
            # 1) ask the LLM for the next Thought/Action/Final Answer
            try:
                result = self.llm.generate(buffer, system_prompt=system_prompt)
            except Exception as e:
                logger.log_event("AGENT_ERROR", {"error": str(e)})
                return f"Agent failed to get response from LLM: {e}"

            text = result.get("content") if isinstance(result, dict) else str(result)
            text = text or ""
            self.history.append({"llm": text})

            # 2) Check for Final Answer
            m_final = re.search(r"Final Answer:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
            if m_final:
                final = m_final.group(1).strip()
                # Collect tool observations separately (do NOT mix into the displayed content)
                obs_list = [
                    h.get("observation")
                    for h in self.history
                    if isinstance(h, dict) and "observation" in h
                ]

                logger.log_event(
                    "AGENT_END",
                    {"steps": steps, "final": final, "included_observations": bool(obs_list)},
                )
                # Return structured output so callers (UI) can choose to display only 'content'
                return {"content": final, "observations": obs_list}

            # 3) Parse Action: tool_name(arg1, arg2)  -- args can be anything inside parentheses
            m = re.search(r"Action:\s*([A-Za-z0-9_]+)\s*\((.*)\)", text, re.IGNORECASE | re.DOTALL)
            if m:
                tool_name = m.group(1).strip()
                raw_args = m.group(2).strip()

                logger.log_event(
                    "AGENT_ACTION", {"tool": tool_name, "raw_args": raw_args, "step": steps}
                )

                try:
                    obs = self._execute_tool(tool_name, raw_args)
                except Exception as e:
                    obs = f"Tool {tool_name} raised error: {e}"

                # normalize observation to string
                try:
                    import json

                    if isinstance(obs, (dict, list)):
                        obs_text = json.dumps(obs, ensure_ascii=False)
                    else:
                        obs_text = str(obs)
                except Exception:
                    obs_text = str(obs)

                # append Observation to buffer so LLM can continue the chain
                buffer = buffer + "\n" + text + "\n" + f"Observation: {obs_text}\n"
                self.history.append({"observation": obs_text})
                # continue loop to get next Thought/Action
                continue

            # 4) If no actionable content found, append LLM output as context and retry
            logger.log_event("AGENT_NO_ACTION", {"text": text, "step": steps})
            buffer = buffer + "\n" + text

        # max steps hit
        logger.log_event("AGENT_END", {"steps": steps, "note": "max_steps_reached"})
        return "Max steps reached without a Final Answer. Last LLM output:\n" + (
            self.history[-1].get("llm") if self.history else ""
        )

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool.get("name") == tool_name:
                # 1) If a callable is provided directly, call it
                fn = tool.get("func") or tool.get("callable")
                if callable(fn):
                    # try to interpret args: JSON, quoted string, or comma-separated
                    parsed = None
                    import json

                    # attempt JSON
                    a = args.strip()
                    if a.startswith("{") and a.endswith(")"):
                        # guard against trailing ) from regex capture (rare)
                        a = a[:-1].strip()
                    try:
                        parsed = json.loads(a)
                    except Exception:
                        # try single quoted or double quoted string
                        if (a.startswith('"') and a.endswith('"')) or (
                            a.startswith("'") and a.endswith("'")
                        ):
                            parsed = a[1:-1]
                        elif a == "":
                            parsed = None
                        else:
                            # comma separated positional
                            parts = [p.strip() for p in a.split(",")] if a else []
                            parsed = parts if len(parts) > 1 else (parts[0] if parts else None)

                    # call with parsed argument(s)
                    if isinstance(parsed, list):
                        return fn(*parsed)
                    elif isinstance(parsed, dict):
                        return fn(parsed)
                    elif parsed is None:
                        return fn()
                    else:
                        return fn(parsed)

                # 2) If module and fn strings are provided, import and call
                module_name = tool.get("module")
                fn_name = tool.get("fn") or tool.get("function")
                if module_name and fn_name:
                    import importlib

                    mod = importlib.import_module(module_name)
                    fn2 = getattr(mod, fn_name)
                    # pass raw arg string to wrapper
                    return fn2(args)

                # 3) If tool provides a 'wrapper' name in the same package
                wrapper = tool.get("wrapper")
                if wrapper:
                    # try to resolve wrapper within tools package
                    import importlib

                    try:
                        mod = importlib.import_module("src.tools." + wrapper)
                        # if module exports a single callable named <wrapper>_wrapper or 'run'
                        if hasattr(mod, "run"):
                            return getattr(mod, "run")(args)
                    except Exception:
                        pass

                return f"Tool {tool_name} found but not callable or missing handler."

        return f"Tool {tool_name} not found."
