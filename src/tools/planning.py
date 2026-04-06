import os
import json
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def planning_tool_wrapper(tool_input: str) -> Dict[str, Any]:
    """Expects tool_input as JSON string containing:
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
    """Use OpenAI to generate a detailed travel itinerary."""

    interest_line = f"\nSở thích của du khách: {interests}" if interests else ""
    budget_line = f"\nMức ngân sách: {budget}"

    prompt = (
        f"Hãy lên kế hoạch du lịch chi tiết theo từng ngày cho chuyến đi đến {destination} "
        f"từ ngày {start_date} đến ngày {end_date}.{interest_line}{budget_line}\n\n"
        "Yêu cầu:\n"
        "- Lịch trình theo từng ngày (sáng, trưa, chiều, tối)\n"
        "- Gợi ý địa điểm tham quan, nhà hàng, hoạt động cụ thể\n"
        "- Ước tính chi phí cho mỗi hoạt động (VND)\n"
        "- Mẹo di chuyển giữa các điểm\n"
        "- Trả lời bằng tiếng Việt\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là chuyên gia lập kế hoạch du lịch. "
                    "Hãy tạo lịch trình chi tiết, thực tế và hữu ích."
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
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "interests": interests,
        "budget": budget,
        "plan": plan_text,
        "usage": usage,
    }
