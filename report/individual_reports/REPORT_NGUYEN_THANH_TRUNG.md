# Individual Report: Travel Agent ReAct Lab - Lab 3

- **Student Name**: Nguyễn Thành Trung
- **Student ID**: 2A202600451
- **Date**: 2026-04-06
- **GitHub Team**: [Repo Lab3-team 35 here](https://github.com/viet-anh-le/Lab3-35.git)

---

## I. Technical Contribution 

### Modules I Implemented:
- [x] `src/tools/planning.py` - Travel planning tool using OpenAI GPT-4o
- [x] `src/chatbot.py` - Chatbot baseline script (Phase 2)
- [x] `docs/workflow.md` - Full workflow documentation with architecture diagrams
- [x] `.gitignore` - Updated to exclude venv directory
- [x] `requirements.txt` - Configured project dependencies

### Code Highlights:

**1. Travel Planning Tool (`src/tools/planning.py`)**

Commit: `5f7d045` - *feat: add travel planning tool using OpenAI*

I implemented the AI-powered travel planning tool that uses OpenAI GPT-4o to generate detailed day-by-day itineraries. This tool is unique among the team's tools because it leverages an LLM as a tool itself — an "agent calling an agent" pattern.

```python
def create_travel_plan(
    destination: str,
    start_date: str,
    end_date: str,
    interests: str = "",
    budget: str = "medium",
) -> Dict[str, Any]:
    """Use OpenAI to generate a detailed travel itinerary."""
    prompt = (
        f"Hãy lên kế hoạch du lịch chi tiết theo từng ngày cho chuyến đi đến {destination} "
        f"từ ngày {start_date} đến ngày {end_date}..."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[...],
        temperature=0.7,
    )
    # Returns structured dict with plan, usage stats, and metadata
```

Key design decisions:
- Vietnamese language prompts for local context relevance
- `temperature=0.7` to balance creativity and consistency in itinerary generation
- Wrapper function `planning_tool_wrapper()` accepts JSON string input — compatible with the ReAct agent's tool execution pipeline
- Returns token usage stats for cost tracking via telemetry

**2. Chatbot Baseline (`src/chatbot.py`)**

Commits: `2cbd06e` → `34d5e8f` (implemented then moved to `src/`)

I built the chatbot baseline script for Phase 2 of the lab. This script runs a pure LLM chatbot (no tools, no ReAct) against 5 complex test cases to demonstrate its limitations:

```python
TEST_CASES = [
    # Test 1: Requires real-time weather data
    "What's the weather like in Tokyo on 2026-04-10? Should I pack an umbrella?",
    # Test 2: Requires real flight price lookup
    "Find me the cheapest flight from NYC to Paris departing on 2026-05-01.",
    # Test 3: Multi-step - needs flight + hotel + weather
    "I want to travel from Bangkok to London on 2026-05-15. ...",
    # Test 4: Multi-step with calculation
    "Plan a 5-day trip to Tokyo. I need: flight from NYC, budget hotel, ...",
    # Test 5: Requires current data + reasoning
    "Compare the weather in Paris vs Bangkok on 2026-04-15. ...",
]
```

The script includes automated issue detection that flags:
- `ADMITTED LIMITATION` — when the chatbot says "I don't have access" or "as an AI"
- `VAGUE/ESTIMATED DATA` — when it uses words like "approximately", "typically"
- `HALLUCINATED PRICES` — when it outputs dollar amounts without a real data source

This baseline is critical because it provides the **control group** for the Chatbot vs ReAct Agent comparison.

**3. Workflow Documentation (`docs/workflow.md`)**

Commit: `82e1903` - *docs: add workflow documentation* (281 lines)

I authored comprehensive workflow documentation including:
- ASCII architecture diagram of the full system
- Directory structure with role of each module
- Step-by-step ReAct loop flow with visual diagrams
- Tool reference table (4 tools with input/output specs)
- Provider switching examples (OpenAI/Gemini/Local)
- Test case descriptions with difficulty levels
- Telemetry event types reference
- Development workflow guide

### How My Code Interacts with the ReAct Loop:

The `planning.py` tool is called by the ReAct agent when the user asks for trip planning. The agent's `_execute_tool()` method in `agent.py` finds the `create_travel_plan` function by name, parses the arguments from the LLM's `Action:` output, and calls the function. The returned JSON becomes the `Observation` that gets fed back into the next LLM prompt. Because the planning tool returns a detailed itinerary, the agent typically uses it as the **last tool call** before generating its `Final Answer`.

The `chatbot.py` baseline uses the same `OpenAIProvider` but bypasses the entire ReAct loop — it sends user queries directly to the LLM with a simple system prompt. This shared provider makes the comparison fair: same model, same API, different reasoning architecture.

---

## II. Debugging Case Study 

### Problem Description: Chatbot Baseline Path Resolution Error

**Initial Issue:** After implementing `chatbot.py` at the project root, running `python chatbot.py` failed because the import `from src.core.openai_provider import OpenAIProvider` could not resolve correctly when the script was later moved to `src/chatbot.py`.

The `.env` path resolution was also broken:
```python
# Original (at root): worked fine
env_path = Path(__file__).resolve().parent / ".env"

# After moving to src/: .env not found because parent is now src/, not root
```

### Diagnosis:

This was a **file organization issue**, not an LLM issue. The script was originally written for the project root but needed to live in `src/` for cleaner structure. Two things broke:
1. The `dotenv` path pointed to `src/.env` instead of the project root `.env`
2. The module imports assumed a specific working directory

From the git log:
- Commit `2cbd06e`: Created `chatbot.py` at root — worked
- Commit `34d5e8f`: Moved to `src/chatbot.py` — needed path fix

### Solution Implemented:

The `.env` path was adjusted to navigate up one level from `src/`:
```python
env_path = Path(__file__).resolve().parent.parent / ".env"
```

And the script should be run from the project root directory:
```bash
python -m src.chatbot
# or
cd Lab3-35 && python src/chatbot.py
```

### Key Learning:
"File organization matters in Python projects. When moving scripts between directories, all relative paths (imports, .env loading, file references) must be updated. This is easy to miss because tests pass locally when your working directory happens to be correct."

---

### Debugging Case Study 2: Planning Tool — LLM Hallucination in Itinerary

**Problem:** During testing of the `create_travel_plan` tool, the GPT-4o model sometimes generated itineraries with fictitious restaurant names and inaccurate cost estimates in VND. For example, it suggested "Nhà hàng Sushi Master Tokyo" — a restaurant that doesn't exist.

**Diagnosis:**
- Root cause: The planning tool relies on the LLM's training data, not real-time search. Unlike `get_weather` or `get_flight_price` (which call real APIs via Tavily/weatherapi.com), the planning tool has no grounding mechanism.
- The `temperature=0.7` setting encouraged creative but potentially inaccurate outputs.

**Solution:**
- This is a known limitation documented in `workflow.md`. In a production system, the planning tool should cross-reference its suggestions with tools like `search_attractions` and `check_availability` to ground the itinerary in real data.
- For the lab scope, this limitation is acceptable because the planning tool's purpose is to demonstrate "LLM-as-a-tool" pattern, and the hallucination itself becomes a teaching point for the Failure Analysis phase.

**Key Learning:**
"Chaining an LLM tool inside a ReAct agent creates a double-hallucination risk: the outer agent can hallucinate tool calls, and the inner LLM tool can hallucinate content. Production systems need grounding at every layer."

---

## III. Personal Insights: ReAct Agent vs Chatbot 

### 1. How did the `Thought` block help the agent?

Building the chatbot baseline gave me a clear view of what happens **without** structured reasoning. The chatbot receives a complex query like "Plan a 5-day trip to Tokyo with flights, hotels, and activities" and tries to answer everything in one shot. The result is a wall of text filled with generic, unverifiable information.

The ReAct agent, in contrast, uses the `Thought` block to decompose this into discrete steps:
- Thought 1: "I need flight prices first" → calls `get_flight_price`
- Thought 2: "Now I need hotel options" → calls `get_hotel_price`  
- Thought 3: "Let me check weather" → calls `get_weather`
- Thought 4: "Now I can build a plan with real data" → calls `create_travel_plan`

Each `Thought` acts as a **checkpoint** that forces the model to plan its next action rather than guess. This is why the system prompt in `agent.py` enforces "FIRST RESPONSE MUST CALL A TOOL - No exceptions!" — removing the shortcut makes the agent actually reason.

### 2. Where did the Agent perform WORSE than the Chatbot?

From my chatbot baseline testing, I observed that the simple chatbot is actually **faster and cheaper** for simple questions:

| Scenario | Chatbot | ReAct Agent |
|----------|---------|-------------|
| "What's Paris like?" | ~100 tokens, 1 API call | ~900 tokens, 2+ API calls |
| Latency | ~1s | ~5-8s (multiple tool calls) |
| Simple factual Q&A | Good enough | Overkill |

The chatbot wins when:
- The question doesn't need real-time data
- It's a simple, single-step query
- Speed/cost matters more than accuracy

**Implication for production:** A smart system should use a **router** — classify incoming queries as simple vs complex, and only route complex multi-step queries through the ReAct pipeline.

### 3. How did `Observation` feedback influence the next steps?

The Observation is the critical difference between "generating text" and "reasoning with evidence." In the ReAct loop:

```
Action: get_flight_price(origin=NYC, destination=Tokyo, departure_date=2026-05-15)
Observation: {"status": "success", "route": "NYC -> Tokyo", "search_result": "Prices range from $650-$900..."}
```

This Observation becomes part of the context for the next Thought. The agent now **knows** the flight costs $650-900 and can make informed decisions about the remaining budget for hotels and activities. Without this:
- A chatbot would guess "$800 for a flight" (hallucination)
- The ReAct agent uses the actual $650-900 range from Tavily search

Each Observation constrains the search space and grounds subsequent reasoning in facts. This is exactly why my `planning.py` tool is most effective when called **after** other tools — it can incorporate real weather, flight, and hotel data into the itinerary.

---

## IV. Future Improvements 

### 1. Grounding the Planning Tool with RAG

My `create_travel_plan` tool currently relies on GPT-4o's training data. To reduce hallucination:
```python
# Future: Inject real tool results into planning prompt
def create_grounded_plan(destination, dates, weather_data, flight_data, hotel_data):
    prompt = f"""Create itinerary for {destination}.
    REAL weather: {weather_data}
    REAL flights: {flight_data}  
    REAL hotels: {hotel_data}
    Only recommend places that actually exist."""
```
This turns the planning tool from "creative writing" to "evidence-based synthesis."

### 2. Async Parallel Tool Execution

Currently, the ReAct loop calls tools sequentially. For independent tools (weather + flights + hotels), parallel execution would cut latency:
```python
import asyncio

async def run_parallel_tools(tools_to_call):
    results = await asyncio.gather(
        get_weather(city="Tokyo", date="2026-05-15"),
        get_flight_price(origin="NYC", destination="Tokyo", departure_date="2026-05-15"),
        get_hotel_price(city="Tokyo", check_in_date="2026-05-15", check_out_date="2026-05-20")
    )
    return results
# 3 API calls in ~2s instead of ~6s sequential
```

### 3. Query Router for Cost Optimization

Based on my chatbot baseline findings:
```python
def route_query(user_input: str) -> str:
    """Classify query complexity to choose the right pipeline."""
    # Simple: "What's Paris like?" → chatbot (cheap, fast)
    # Complex: "Plan 5-day trip with budget" → ReAct agent (accurate, grounded)
    complexity = classify_complexity(user_input)
    if complexity == "simple":
        return chatbot_respond(user_input)
    else:
        return react_agent.run(user_input)
```
This saves ~80% of token costs for simple queries while maintaining accuracy for complex ones.

### 4. Multi-turn Memory with Conversation State

```python
class StatefulAgent(ReActAgent):
    def __init__(self, ...):
        self.conversation_memory = {}  # Cache previous tool results
    
    def run(self, user_input):
        # Check if we already have relevant data
        if "Tokyo weather" in self.conversation_memory:
            # Skip tool call, reuse cached observation
            pass
```
This enables follow-up queries like "What if I change to a luxury hotel?" without re-fetching weather and flights.

---

## V. Conclusion

Building the chatbot baseline and the planning tool gave me a front-row seat to the core tension in LLM systems: **speed vs accuracy**. The chatbot is fast but unreliable; the ReAct agent is slower but grounded in real data.

My main takeaway: **Tools are not just API wrappers — they are trust boundaries.** Every tool call is a point where the system switches from "generating plausible text" to "retrieving verified facts." The planning tool I built sits in an interesting middle ground — it's an LLM tool that generates content, which means it needs its own grounding layer to be production-ready.

The explicit Thought-Action-Observation cycle makes the agent's reasoning transparent and debuggable. When something goes wrong, I can read the logs and pinpoint exactly which step failed. With a chatbot, a wrong answer is just... a wrong answer, with no trace to diagnose.

---

> **Git Evidence Summary:**
> | Commit | Description |
> |--------|-------------|
> | `5f7d045` | feat: add travel planning tool using OpenAI |
> | `82e1903` | docs: add workflow documentation |
> | `7aa82ce` | feat: update .gitignore to exclude venv |
> | `fbdc23d` | feat: configure workspace settings |
> | `2cbd06e` | feat: implement chatbot baseline script |
> | `34d5e8f` | fix: change location -> src |
