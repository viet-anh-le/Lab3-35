#!/usr/bin/env python3
import json

# Read the log file and find all weather tool executions from the latest tests
with open("logs/2026-04-06.log", "r") as f:
    lines = f.readlines()

# Find TOOL_EXECUTED events for get_weather after timestamp 09:02 (new tests)
print("=" * 80)
print("WEATHER TOOL EXECUTIONS (Latest Test Run - After 09:02)")
print("=" * 80)

for i, line in enumerate(lines):
    try:
        log_entry = json.loads(line)
        if log_entry.get("event") == "TOOL_EXECUTED" and log_entry.get("data", {}).get("tool") == "get_weather":
            timestamp = log_entry.get("timestamp", "")
            if "09:02" in timestamp or "09:03" in timestamp:  # New tests
                obs_len = log_entry.get("data", {}).get("observation_length")
                print(f"\nTimestamp: {timestamp}")
                print(f"Observation Length: {obs_len} bytes")
                
                # Try to find the corresponding observation in the next few lines
                if i + 1 < len(lines):
                    # Usually the observation is right after the tool execution
                    print(f"(Weather returned {obs_len} bytes)")
                    
    except json.JSONDecodeError:
        pass

print("\n" + "=" * 80)
print("SUMMARY: Check if observation_length = 56 (error) or > 200 (real data)")
print("=" * 80)
