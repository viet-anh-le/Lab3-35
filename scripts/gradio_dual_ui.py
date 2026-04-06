#!/usr/bin/env python3
"""Dual-pane Gradio UI: left = baseline chatbot, right = agent with tools.

Run:
  pip install -r requirements.txt
  export GEMINI_API_KEY=... or export OPENAI_API_KEY=...
  python scripts/gradio_dual_ui.py

The left pane sends user messages directly to the LLM provider.
The right pane sends messages to the ReActAgent which can call tools.
"""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import gradio as gr

from src.core.llm_provider import LLMProvider
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.weather import weather_tool_wrapper
from src.tools.search_attractions import attraction_tool_wrapper
from src.tools.search_flights import flight_search_tool_wrapper

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def choose_provider() -> LLMProvider:
    genai_key = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if genai_key:
        try:
            return GeminiProvider(api_key=genai_key)
        except Exception:
            pass
    if openai_key:
        try:
            return OpenAIProvider(api_key=openai_key)
        except Exception:
            pass

    # fallback stub
    class StubProvider(LLMProvider):
        def __init__(self):
            super().__init__(model_name="stub")

        def generate(self, prompt: str, system_prompt: Optional[str] = None):
            return {
                "content": "(stub) No API key configured; cannot call external LLM.",
                "usage": {},
                "latency_ms": 1,
            }

        def stream(self, prompt: str, system_prompt: Optional[str] = None):
            yield "(stub)"

    return StubProvider()


def build_tools():
    return [
        {
            "name": "search_attractions",
            "description": 'Find the top 5 attractions in a specified city. Arguments: {"city": "City name"}',
            "func": attraction_tool_wrapper,
        },
        {
            "name": "search_flights",
            "description": 'Search for flights between two cities on a specific date. Arguments: {"departure_city": "City of departure", "destination_city": "City of arrival", "departure_date": "Date of travel (YYYY-MM-DD)"}',
            "func": flight_search_tool_wrapper,
        },
        {
            "name": "weather_forecast",
            "description": 'Get the weather forecast for a city within a date range. Arguments: {"city": "City name", "start_date": "Start date (YYYY-MM-DD)", "end_date": "End date (YYYY-MM-DD)"}',
            "func": weather_tool_wrapper,
        },
    ]


def main():
    provider = choose_provider()
    tools = build_tools()
    agent = ReActAgent(llm=provider, tools=tools, max_steps=6)

    # Simple helper to call provider.generate and extract content
    def call_provider(prompt: str) -> str:
        try:
            r = provider.generate(prompt)
            if isinstance(r, dict):
                return r.get("content", str(r))
            return str(r)
        except Exception as e:
            return f"Provider error: {e}"

    header_md = "# Dual Chat UI — Baseline Chatbot (left) vs Agent (right)\nChoose the pane and ask questions. The agent can call tools (weather, flights, attractions)."
    footer_md = "---\nBuilt for the Day-3 lab.\n" + (
        f"Using provider: {getattr(provider, 'model_name', 'stub')}"
    )

    with gr.Blocks(title="Dual Chat UI") as demo:
        gr.Markdown(header_md)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Baseline Chatbot")
                baseline_chat = gr.Chatbot(elem_id="baseline_chat")
                baseline_input = gr.Textbox(
                    placeholder="Message to baseline chatbot and press Enter"
                )

                def respond_baseline(message, history):
                    history = history or []
                    # ensure messages as dicts
                    history.append({"role": "user", "content": message})
                    out = call_provider(message)
                    history.append({"role": "assistant", "content": out})
                    return history, ""

                baseline_input.submit(
                    respond_baseline,
                    [baseline_input, baseline_chat],
                    [baseline_chat, baseline_input],
                )

            with gr.Column(scale=1):
                gr.Markdown("## Agent (can use tools)")
                agent_chat = gr.Chatbot(elem_id="agent_chat")
                agent_input = gr.Textbox(placeholder="Message to agent and press Enter")

                def respond_agent(message, history):
                    history = history or []
                    history.append({"role": "user", "content": message})
                    try:
                        out = agent.run(message)
                        # If the agent returns a dict (e.g., with 'content' and other fields),
                        # display only the 'content' field in the UI.
                        if isinstance(out, dict):
                            display_out = out.get("content", "")
                        else:
                            display_out = str(out)
                    except Exception as e:
                        display_out = f"Agent error: {e}"
                    history.append({"role": "assistant", "content": display_out})
                    return history, ""

                agent_input.submit(
                    respond_agent, [agent_input, agent_chat], [agent_chat, agent_input]
                )

        gr.Markdown(footer_md)

    demo.launch()


if __name__ == "__main__":
    main()
