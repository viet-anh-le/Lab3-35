"""
Phase 2: Chatbot Baseline
A simple LLM chatbot WITHOUT tools or ReAct reasoning.
This demonstrates the limitations of pure prompt-based approaches
when faced with multi-step, data-dependent questions.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider

# Load environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


SYSTEM_PROMPT = """You are a helpful travel assistant chatbot.
Answer the user's travel questions to the best of your ability.
Be specific with numbers, dates, and prices when asked."""


# Complex test cases that require real-time data or multi-step reasoning
TEST_CASES = [
    # Test 1: Requires real-time weather data
    "What's the weather like in Tokyo on 2026-04-10? Should I pack an umbrella?",

    # Test 2: Requires real flight price lookup
    "Find me the cheapest flight from NYC to Paris departing on 2026-05-01.",

    # Test 3: Multi-step - needs flight + hotel + weather
    "I want to travel from Bangkok to London on 2026-05-15. "
    "What's the flight price, hotel cost for 3 nights, and weather forecast?",

    # Test 4: Multi-step with calculation
    "Plan a 5-day trip to Tokyo. I need: flight from NYC, budget hotel, "
    "and check if a sushi-making class is available on 2026-05-20. "
    "What's the total estimated cost?",

    # Test 5: Requires current data + reasoning
    "Compare the weather in Paris vs Bangkok on 2026-04-15. "
    "Which destination is better for outdoor activities? "
    "Also show me hotel prices for both cities.",
]


def run_chatbot_baseline():
    """Run the simple chatbot against all test cases."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("ERROR: Please set OPENAI_API_KEY in your .env file")
        return

    provider = OpenAIProvider(model_name="gpt-4o", api_key=api_key)

    print("=" * 70)
    print("PHASE 2: CHATBOT BASELINE (No Tools, No ReAct)")
    print("=" * 70)
    print(f"Model: {provider.model_name}")
    print(f"System: Pure chatbot - no access to real-time data or tools")
    print("=" * 70)

    results = []

    for i, query in enumerate(TEST_CASES, 1):
        print(f"\n{'─' * 70}")
        print(f"TEST CASE {i}:")
        print(f"  Q: {query}")
        print(f"{'─' * 70}")

        start_time = time.time()

        try:
            response = provider.generate(
                prompt=query,
                system_prompt=SYSTEM_PROMPT
            )

            latency = int((time.time() - start_time) * 1000)
            answer = response.get("content", "No response")
            tokens = response.get("usage", {})

            print(f"\n  CHATBOT ANSWER:")
            print(f"  {answer[:600]}")
            if len(answer) > 600:
                print(f"  ... [truncated, {len(answer)} chars total]")

            print(f"\n  --- Metrics ---")
            print(f"  Latency: {latency}ms")
            print(f"  Tokens: {tokens.get('total_tokens', 'N/A')}")

            # Analysis
            issues = []
            if any(word in answer.lower() for word in ["i don't have access", "i cannot", "as an ai"]):
                issues.append("ADMITTED LIMITATION")
            if any(word in answer.lower() for word in ["approximately", "typically", "around", "usually", "generally"]):
                issues.append("VAGUE/ESTIMATED DATA (not real-time)")
            if "$" in answer and "exact" not in answer.lower():
                issues.append("HALLUCINATED PRICES (no real data source)")

            status = "FAIL - " + ", ".join(issues) if issues else "NEEDS VERIFICATION"
            print(f"  Status: {status}")

            results.append({
                "test": i,
                "status": status,
                "latency_ms": latency,
                "tokens": tokens.get("total_tokens", 0)
            })

        except Exception as e:
            print(f"\n  ERROR: {str(e)}")
            results.append({"test": i, "status": f"ERROR: {str(e)}", "latency_ms": 0, "tokens": 0})

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY: CHATBOT BASELINE RESULTS")
    print(f"{'=' * 70}")
    print(f"{'Test':<6} {'Status':<45} {'Latency':<10} {'Tokens':<8}")
    print(f"{'─' * 70}")
    for r in results:
        print(f"{r['test']:<6} {r['status']:<45} {r['latency_ms']}ms{'':<4} {r['tokens']}")

    print(f"\n{'=' * 70}")
    print("KEY OBSERVATION:")
    print("  The chatbot CANNOT access real-time data (weather, flights, prices).")
    print("  It either hallucinates specific numbers or admits it doesn't know.")
    print("  Multi-step queries get vague, generic responses.")
    print("  --> This is WHY we need a ReAct Agent with tools!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_chatbot_baseline()
