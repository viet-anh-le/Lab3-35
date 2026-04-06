import json
import requests
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# API Keys
WEATHER_API_KEY = "ffaa750549e748fe9a391020260604"
TAVILY_API_KEY = "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"

# ============ REAL API: Flight Search ============
def get_flight_price(origin: str, destination: str, departure_date: str) -> str:
    """
    Search for real flight prices using Tavily API.
    Input: origin, destination (city names), departure_date (YYYY-MM-DD)
    Returns: JSON with price, airlines, and booking info
    """
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"cheapest flights {origin} to {destination} {departure_date}",
        "include_answer": True,
        "max_results": 5
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get("answer"):
        answer = data["answer"]
        return json.dumps({
            "status": "success",
            "route": f"{origin} -> {destination}",
            "date": departure_date,
            "search_result": answer[:500],
            "source": "Tavily API"
        })
    else:
        return json.dumps({"status": "error", "message": "No flight data found"})


# ============ MOCK: Hotel Price (kept for planning purposes) ============
def get_hotel_price(city: str, check_in_date: str, check_out_date: str, guests: int = 1) -> str:
    """
    Search for hotel prices in a city.
    Input: city, check_in_date (YYYY-MM-DD), check_out_date (YYYY-MM-DD), guests
    Returns: JSON with hotel prices and availability
    """
    hotel_db = {
        "Paris": {"luxury": 250, "standard": 120, "budget": 50},
        "Tokyo": {"luxury": 300, "standard": 150, "budget": 60},
        "Bangkok": {"luxury": 180, "standard": 90, "budget": 40},
        "NYC": {"luxury": 350, "standard": 200, "budget": 100},
        "London": {"luxury": 280, "standard": 140, "budget": 70},
    }
    
    if city in hotel_db:
        hotels = hotel_db[city]
        return json.dumps({
            "status": "success",
            "city": city,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": guests,
            "options": {
                "luxury": f"${hotels['luxury']}/night",
                "standard": f"${hotels['standard']}/night",
                "budget": f"${hotels['budget']}/night"
            }
        })
    else:
        return json.dumps({"status": "error", "message": f"Hotels not found in {city}"})


# ============ REAL API: Destination Info (Tavily) ============
def get_destination_info(city: str) -> str:
    """
    Get real destination information using Tavily API.
    Input: city name
    Returns: JSON with attractions, travel info, culture
    """
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"top attractions visa requirements currency language {city} travel guide",
        "include_answer": True,
        "max_results": 3
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get("answer"):
        answer = data["answer"]
        return json.dumps({
            "status": "success",
            "city": city,
            "travel_guide": answer[:600],
            "source": "Tavily API"
        })
    else:
        return json.dumps({"status": "error", "message": f"No info found for {city}"})


# ============ REAL API: Activities & Tours (Tavily) ============
def check_availability(activity: str, date: str, city: str) -> str:
    """
    Check availability of tours and activities using Tavily API.
    Input: activity name, date (YYYY-MM-DD), city
    Returns: JSON with availability and booking info
    """
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"{activity} tours activities {city} {date} booking availability pricing",
        "include_answer": True,
        "max_results": 5
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get("answer"):
        answer = data["answer"]
        return json.dumps({
            "status": "success",
            "activity": activity,
            "city": city,
            "date": date,
            "availability_info": answer[:400],
            "source": "Tavily API"
        })
    else:
        return json.dumps({
            "status": "error",
            "message": f"Activity '{activity}' search returned no results"
        })


# ============ REAL API: Weather (weatherapi.com) ============
def get_weather(city: str, date: str) -> str:
    """
    Get real weather forecast using weatherapi.com API.
    Input: city, date (YYYY-MM-DD)
    Returns: JSON with temperature, conditions, packing advice
    """
    url = f"http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "aqi": "no",
        "days": 10
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Check for API errors
    if data.get("error"):
        error_msg = data["error"].get("message", "Unknown API error")
        return json.dumps({"status": "error", "message": f"weatherapi.com error: {error_msg}"})
    
    if data.get("forecast"):
        forecast_days = data["forecast"]["forecastday"]
        
        # Find the specific date if available
        target_forecast = None
        for day in forecast_days:
            if day["date"] == date:
                target_forecast = day
                break
        
        if not target_forecast:
            target_forecast = forecast_days[0]
        
        day_data = target_forecast["day"]
        temp = day_data["avgtemp_c"]
        condition = day_data["condition"]["text"]
        packing = "Light clothing" if temp > 20 else "Bring a jacket" if temp > 10 else "Warm coat needed"
        
        return json.dumps({
            "status": "success",
            "city": city,
            "date": target_forecast.get("date", date),
            "temperature_celsius": round(temp, 1),
            "condition": condition,
            "humidity_percent": day_data.get("avghumidity", 60),
            "chance_of_rain": day_data.get("daily_chance_of_rain", 0),
            "packing_advice": packing,
            "source": "weatherapi.com"
        })
    else:
        return json.dumps({"status": "error", "message": f"No forecast data found for {city}"})


# ============ AI-POWERED: Travel Planning (OpenAI GPT-4o) ============
def planning_tool_wrapper(tool_input: str) -> Dict[str, Any]:
    """
    High-level wrapper for the planning tool.
    Expects tool_input as JSON string containing:
    - destination: Destination city
    - start_date: Start date of the trip
    - end_date: End date of the trip
    - interests: (optional) Traveler interests, e.g. "food, culture, nature"
    - budget: (optional) Budget level, e.g. "low", "medium", "high"
    """
    payload = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
    destination = payload["destination"]
    start_date = payload["start_date"]
    end_date = payload["end_date"]
    interests = payload.get("interests", "")
    budget = payload.get("budget", "medium")
    return create_travel_plan(destination, start_date, end_date, interests, budget)


def create_travel_plan(
    destination: str,
    start_date: str,
    end_date: str,
    interests: str = "",
    budget: str = "medium",
) -> Dict[str, Any]:
    """
    Use OpenAI GPT-4o to generate a detailed travel itinerary.
    Input: destination, date range, interests (optional), budget level (optional)
    Returns: JSON with day-by-day itinerary, cost estimates, and travel tips
    """
    
    interest_line = f"\nInterests: {interests}" if interests else ""
    budget_line = f"\nBudget level: {budget}"

    prompt = (
        f"Create a detailed day-by-day travel itinerary for a trip to {destination} "
        f"from {start_date} to {end_date}.{interest_line}{budget_line}\n\n"
        "Requirements:\n"
        "- Detailed schedule for each day (morning, afternoon, evening, night)\n"
        "- Specific attractions, restaurants, and activities\n"
        "- Cost estimates for each activity\n"
        "- Transportation tips between locations\n"
        "- Based on actual local knowledge\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert travel planner. "
                    "Create detailed, practical, and engaging itineraries that fit the traveler's interests and budget."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    plan_text = response.choices[0].message.content
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    return {
        "status": "success",
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "interests": interests if interests else "general",
        "budget": budget,
        "itinerary": plan_text,
        "usage": usage,
        "source": "OpenAI GPT-4o"
    }


def create_travel_plan_simple(destination: str, duration_days: int, interests: str = "", budget: str = "medium") -> str:
    """
    Simplified planning tool interface that returns JSON string.
    Input: destination, duration in days, interests (optional), budget (optional)
    Returns: JSON string with travel plan
    """
    import datetime
    today = datetime.date.today()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + datetime.timedelta(days=duration_days)).strftime("%Y-%m-%d")
    
    result = create_travel_plan(destination, start_date, end_date, interests, budget)
    return json.dumps(result)


# List of all tools available to the agent
TRAVEL_TOOLS = [
    {
        "name": "get_flight_price",
        "description": "Search for flight prices between two cities. Takes origin, destination, and departure_date (YYYY-MM-DD). Returns price and airline options.",
        "function": get_flight_price,
        "args": ["origin", "destination", "departure_date"]
    },
    {
        "name": "get_hotel_price",
        "description": "Search for hotel prices in a city. Takes city, check_in_date (YYYY-MM-DD), check_out_date (YYYY-MM-DD), and number of guests. Returns prices for different hotel categories.",
        "function": get_hotel_price,
        "args": ["city", "check_in_date", "check_out_date", "guests"]
    },
    {
        "name": "get_destination_info",
        "description": "Get information about a travel destination including attractions, visa requirements, currency, and language. Takes city name.",
        "function": get_destination_info,
        "args": ["city"]
    },
    {
        "name": "check_availability",
        "description": "Check availability of tours and activities in a city. Takes activity name, date (YYYY-MM-DD), and city. Returns available time slots and pricing.",
        "function": check_availability,
        "args": ["activity", "date", "city"]
    },
    {
        "name": "get_weather",
        "description": "Get weather forecast for a destination. Takes city and date (YYYY-MM-DD). Returns temperature, conditions, humidity, and packing advice.",
        "function": get_weather,
        "args": ["city", "date"]
    },
    {
        "name": "create_travel_plan",
        "description": "Create a comprehensive day-by-day travel itinerary using AI. Takes destination, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), and optional interests and budget level. Returns detailed itinerary with costs and transportation tips.",
        "function": create_travel_plan,
        "args": ["destination", "start_date", "end_date", "interests", "budget"]
    }
]
