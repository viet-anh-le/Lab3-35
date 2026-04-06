import argparse
from html import parser
from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools.search_attractions import attraction_tool_wrapper
from src.tools.search_flights import flight_search_tool_wrapper
from src.tools.weather import weather_tool_wrapper
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os
from src.core.gemini_provider import GeminiProvider

def main():

    load_dotenv()  # Load environment variables from .env file
    # Initialize the LLM provider

    llm = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY", ""))

    # Define tools with updated descriptions and arguments
    tools = [
        {
            "name": "search_attractions",
            "description": "Find the top 5 attractions in a specified city. Arguments: {\"city\": \"City name\"}",
            "func": attraction_tool_wrapper,
        },
        {
            "name": "search_flights",
            "description": "Search for flights between two cities on a specific date. Arguments: {\"departure_city\": \"City of departure\", \"destination_city\": \"City of arrival\", \"departure_date\": \"Date of travel (YYYY-MM-DD)\"}",
            "func": flight_search_tool_wrapper,
        },
        {
            "name": "weather_forecast",
            "description": "Get the weather forecast for a city within a date range. Arguments: {\"city\": \"City name\", \"start_date\": \"Start date (YYYY-MM-DD)\", \"end_date\": \"End date (YYYY-MM-DD)\"}",
            "func": weather_tool_wrapper,
        },
    ]

    # Initialize the agent
    agent = ReActAgent(llm=llm, tools=tools)

    # Update the system prompt to enforce stricter rules
    agent.get_system_prompt = lambda: f"""
    You are an intelligent assistant. You have access to the following tools:
    {chr(10).join([f"- {t['name']}: {t['description']}" for t in tools])}

    Use the following format exactly (for the agent to parse your output):
    Thought: <your reasoning here>
    Action: <tool_name>(<arguments as JSON>)
    Observation: <result of the tool call>
    ... (repeat Thought/Action/Observation if needed)
    Final Answer: <your final response>

    Rules:
    1. Always use JSON format for arguments in tool calls.
    2. Only call tools listed above. If you cannot answer, return a Final Answer.
    3. Ensure all required arguments are provided and valid before calling a tool.
    4. Do not make assumptions about missing arguments; ask the user for clarification.
    """

    print("Chatbot is ready. Type your messages below. Type 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = agent.run(user_input)
        print(f"Bot: {response}")

if __name__ == "__main__":
    main()