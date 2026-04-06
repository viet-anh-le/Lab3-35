import requests
from typing import Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient
import json

# Initialize Tavily client and load environment variables
def initialize_client() -> TavilyClient:
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    return TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


client = initialize_client()


def attraction_tool_wrapper(tool_input: str) -> Dict[str, Any]:
    """Expects tool_input as JSON string."""
    payload = parse_input(tool_input)
    city = payload["city"]
    return fetch_attractions(city)

def parse_input(tool_input: str) -> Dict[str, Any]:
    """Parse the input JSON string into a dictionary."""
    return json.loads(tool_input) if isinstance(tool_input, str) else tool_input

def fetch_attractions(city: str) -> Dict[str, Any]:
    """
    Fetch top attractions for a given city using Tavily API.
    """
    response = client.search(
        query=f"Top địa điểm nhất định phải đến tại {city}",
        limit=5,
    )
    return format_response(city, response)

def format_response(city: str, response: Dict[str, Any]) -> Dict[str, Any]:
    """Format the API response into a structured dictionary."""
    print(response['results'])
    contents = []
    for item in response.get("results", []):
        contents.append({
           "content": item.get("content"),
        })
    return {
        "city": city,
        "attractions": contents
    }
    
    
if main := __name__ == "__main__":
    # Example usage
    city = "Hà Nội"
    tool_input = json.dumps({"city": city})
    result = attraction_tool_wrapper(tool_input)
    print(json.dumps(result, indent=2, ensure_ascii=False))