#!/usr/bin/env python3
from src.tools.travel_tools import get_weather
import json

print("Testing weather API with future date (2026-04-10):")
print("=" * 80)

result_str = get_weather("Paris", "2026-04-10")
result = json.loads(result_str)

print(f"Status: {result.get('status')}")
print(f"Result: {json.dumps(result, indent=2)}")

print("\n" + "=" * 80)
print("Length: {} bytes".format(len(result_str)))
