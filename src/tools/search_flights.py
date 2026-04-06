import os
import json
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient

# Initialize Tavily client and load environment variables
def initialize_client() -> TavilyClient:
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    return TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

client = initialize_client()

def flight_search_tool_wrapper(tool_input: str) -> Dict[str, Any]:
    """
    Expects tool_input as JSON string containing:
    - departure_city: City of departure
    - destination_city: City of arrival
    - departure_date: Date of travel
    """
    payload = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
    departure_city = payload.get("departure_city")
    destination_city = payload.get("destination_city")
    departure_date = payload.get("departure_date")
    
    return fetch_flights(departure_city, destination_city, departure_date)

def fetch_flights(departure_city: str, destination_city: str, departure_date: str) -> Dict[str, Any]:
    """
    Search for flight information using Tavily API.
    """
    query = f"Vé máy bay từ {departure_city} đến {destination_city} ngày {departure_date} giá rẻ"
    
    response = client.search(
        query=query,
        search_depth="advanced",
        limit=5
    )
    
    return {
        "departure_city": departure_city,
        "destination_city": destination_city,
        "departure_date": departure_date,
        "flight_results": response.get("results", [])
    }
