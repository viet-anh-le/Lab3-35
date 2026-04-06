#!/usr/bin/env python3
import json
import re

# Read the log file line by line and extract weather observations
with open("logs/2026-04-06.log", "r") as f:
    content = f.read()

# Find all log lines after 09:02 (new tests)
lines = [line for line in content.split('\n') if '09:02' in line or '09:03' in line]

print("=" * 100)
print("WEATHER API RESPONSES (Latest Tests)")
print("=" * 100)

# Look for the LLM responses that come after weather tool calls
# The agent's responses show what the weather tool returned
for line in lines[-50:]:
    if '"step"' in line and 'weather' not in line.lower() and 'response_length' in line:
        try:
            entry = json.loads(line)
            response = entry.get('data', {}).get('response', '')
            if 'weather' in response.lower() or 'unavailable' in response.lower():
                timestamp = entry.get('timestamp', '')
                resp_preview = response[:300] if response else "NO RESPONSE"
                print(f"\nTimestamp: {timestamp}")
                print(f"Response Preview: {resp_preview}...")
        except:
            pass

# Also check for "Observation" text in responses - that shows what tools returned
print("\n" + "=" * 100)
print("LOOKING FOR ACTUAL OBSERVATIONS IN RESPONSES")
print("=" * 100)

for i, line in enumerate(lines[-50:]):
    try:
        if 'Observation' in line:
            print(f"\nFound at index {i}: {line[:200]}...")
    except:
        pass

# Look for errors
print("\n" + "=" * 100) 
print("CHECKING FOR ERROR PATTERNS")
print("=" * 100)
for line in lines[-100:]:
    if 'no forecast' in line.lower() or 'unavailable' in line.lower():
        print(f"Found error: {line[:200]}")
