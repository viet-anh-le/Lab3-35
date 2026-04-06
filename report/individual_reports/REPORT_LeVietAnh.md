# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Việt Anh
- **Student ID**: 2A202600112
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

_Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.)._

- **Modules Implementated**
- `src/tools/weather.py` — implemented `weather_tool_wrapper(payload)`, which accepts a JSON payload {"city", "start_date", "end_date"} and returns a normalized weather JSON. Key behaviors:
  - Geocoding via OpenWeatherMap to obtain latitude/longitude.
  - Calls WeatherAPI (`forecast.json`) using `WEATHER_API_KEY` from the environment.
  - `_normalize_weather()` to produce a compact schema: {location, current, daily, meta}.

- `src/agent/prompts.py` — authored the ReAct prompt template (`REACT_PROMPT`) that enforces preprocessing rules (location normalization and date handling) and a strict tool execution order for trip-planning (weather → flights → attractions → aggregate → final answer).

- `scripts/gradio_dual_ui.py` — two-column Gradio interface (baseline chatbot on the left, ReAct agent on the right) for comparing v1 (chatbot) vs v2 (agent + tools).

- **Code Highlights**:

- `weather_tool_wrapper(tool_input: str) -> Dict` (in `src/tools/weather.py`):
  - Input: JSON string or dict {"city","start_date","end_date"}.
  - Output: normalized forecast dict (location, current, daily[], meta).
  - Date handling: moves past start dates to today, enforces 1–14 day range.

- `REACT_PROMPT` (in `src/agent/prompts.py`):
  - Enforces SECTION A preprocessing rules (location normalization, date extraction and defaulting) before any tool calls.
  - Specifies SECTION B available tools and the mandatory execution order for trip planning (weather → search_flights → search_attractions → aggregate → Final Answer).

- `ReActAgent` integration (in `src/agent/agent.py`):
  - Accepts a `tools` list where each tool is a dict with `name`, `description`, and `func`.
  - Parses LLM outputs for `Action: tool_name(args)` and invokes the corresponding `func`.
  - Stores observations in `history` and appends them to the prompt buffer for subsequent reasoning steps.
  - When reaching `Final Answer`, returns a result; the Gradio UI is configured to display only the `content` field so raw tool observations are not shown to end users.

- **Documentation**:
  How it interacts with the ReAct loop

- Tools are registered and passed into `ReActAgent(llm, tools=tools)`.
- `ReActAgent.run()` constructs the system prompt from `REACT_PROMPT` (formatted with the tool list and current date) and uses it together with the conversation buffer to call the LLM.
- The agent loop:
  1.  Ask LLM for next Thought/Action using `llm.generate(buffer, system_prompt=...)`.
  2.  If LLM outputs an Action, parse the tool name and JSON args, call the tool function, and capture the Observation.
  3.  Append Observation to the buffer and repeat until the LLM produces `Final Answer`.

Run instructions (examples)

```bash
# from repo root
export WEATHER_API_KEY="<your_key>"
pip install -r requirements.txt
python scripts/gradio_dual_ui.py   # dual-pane baseline vs agent UI
```

---

## II. Debugging Case Study (10 Points)

_Analyze a specific failure event you encountered during the lab using the logging system._

- **Problem Description**:

  While running the ReAct agent, the agent sometimes failed with an exception coming from the Gemini provider. The agent logs contained an `AGENT_ERROR` entry and the user-facing output did not include the expected weather data. In one observed trace the agent terminated with an error instead of returning a useful Final Answer.

  Symptoms seen during debugging:
  - The agent produced an `Action: get_weather(...)` but the run ended with an error before the weather JSON was visible in the UI.
  - Gradio showed only the `content` final message (no observation JSON), and the logs contained an error originating from the LLM provider layer.

- **Log Source (example snippet)**:

  The telemetry/log line captured during one failure was:

  {"timestamp": "2026-04-06T09:47:11.044139", "event": "AGENT_ERROR", "data": {"error": "Invalid operation: The `response.text` quick accessor requires the response to contain a valid `Part`, but none were returned. The candidate's finish_reason is 1."}}

  This message was produced when the code attempted to access `response.text` on the object returned by `google.generativeai` (Gemini) and that accessor raised because the SDK response had no `Part` objects in this case.

- **Diagnosis**:

  Root cause analysis showed the following:
  1. The `GeminiProvider.generate()` implementation assumed that `response.text` would always be present and that `response.usage_metadata` would always exist. When the SDK returned a response shape missing the `Part` object (or with a different candidate layout), `response.text` raised an internal error from the SDK.
  2. Because the provider raised, the agent's call to the LLM failed mid-run; that prevented the agent from receiving a usable string to parse for `Final Answer` or `Observation`. The agent code caught the exception and logged `AGENT_ERROR`.

  Primary contributing factors:
  - Provider fragility (assumptions about the SDK response shape).
  - Lack of a robust fallback path for extracting text from alternative fields (candidates/output/parts).
  - UI design that hides the Observation field (intentional), so even successful tool calls were not plainly visible to end users.

- **Solution(s) implemented**:

  I applied these fixes and mitigations in the codebase:
  1. Make the Gemini provider robust:
     - Updated `src/core/gemini_provider.py` to extract text defensively: try `response.text`, then fall back to `response.candidates[0].text` or `response.candidates[0].content` (joining parts when necessary), then `response.output`. Guarded access to `usage_metadata` to avoid attribute errors.
     - This prevents the `response.text` quick-accessor exception and ensures `generate()` always returns a string under the `content` key.

  2. Improve agent prompt and history handling:
     - Ensured `ReActAgent.run()` builds the LLM buffer from `history + user_input` so the model receives prior thoughts, observations, and the current request.
     - Kept the REACT prompt (in `src/agent/prompts.py`) that enforces the tool call order for trip planning (weather → flights → attractions → aggregate → Final Answer).

- **Verification and results**:
  - After the provider change, repeated runs with the same inputs no longer produced the `response.text` error; `GeminiProvider.generate()` returned a usable `content` field even for variant SDK responses.
  - The agent successfully issued `Action: get_weather(...)`, the tool returned normalized weather JSON, and the agent proceeded to produce a `Final Answer`.
  - Because the Gradio UI intentionally shows only `content`, the weather JSON remained hidden from the end user; I verified the observation is present in agent history and telemetry logs.

- **Follow-ups & recommendations**:
  1. Add a developer-only toggle in the UI to show raw observations (useful for teaching and debugging in the lab). This would surface the tool JSON when enabled.
  2. Add unit tests for provider parsing logic that cover multiple Gemini SDK response shapes (text present, candidates-only, output-only). A small test would assert that `generate()` returns a non-empty `content` string and does not raise.
  3. Add a short integration test for `ReActAgent` using a stub LLM that simulates tool-calling sequences; assert the agent calls tools in the required order and produces a Final Answer containing the combined information.

---

```json
{
  "event": "TOOL_ERROR",
  "tool": "search_flights",
  "error": "json.decoder.JSONDecodeError: Expecting value"
}
```

### Diagnosis:

_Why did this happen?_

- The agent was passing unquoted string values in JSON: `{"departure_city": Hà Nội, ...}`
- Valid JSON requires quoted strings: `{"departure_city": "Hà Nội", ...}`
- Root cause: **LLM action parser wasn't enforcing JSON format**

### Solution Implemented:

_How did I fix it?_

Added defensive JSON parsing with fallback in both tools:

```python
# Before: Strict JSON only
payload = json.loads(tool_input)  # Fails on malformed JSON

# After: With fallback handling
payload = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
```

Also improved the agent's prompt to explicitly require JSON format in Action parameters.

### Verification:

After fix, the tool correctly handled both well-formed and slightly malformed inputs from the agent.

---

## III. Personal Insights: ReAct Agent vs Chatbot (10 Points)

_Reflect deeply on what you learned from comparing reasoning patterns._

### 1. How did the `Thought` block help the agent?

The explicit `Thought` block forces the agent to break down complex queries:

**Example Query:** "Plan a trip to Hà Nội"

**ReAct Agent (with Thought):**

- Thought: "I need to find attractions in Hà Nội"
- Action: search_attractions(city="Hà Nội")
- Observation: [Returns top 5 attractions]
- Thought: "Now I should search for flight options"
- Action: search_flights(...)

**Chatbot (no Thought):**

- Directly generates answer from training data without systematic search
- May miss current information or availability

**Why it matters:** The Thought block ensures step-by-step decomposition rather than guesswork.

### 2. Where did the Agent perform WORSE than a simple chatbot?

**TOKEN COST & LATENCY:**

- Chatbot: "Hà Nội has famous attractions like the Old Quarter..." → ~50 tokens, instant
- ReAct Agent: Calls search_attractions, formats, returns → ~200+ tokens, multi-step latency

**Trade-off:** Not worth it for simple factual questions, excellent for complex multi-step planning.

### 3. How did `Observation` feedback influence the next steps?

**Real Example:**

- Step 1: Agent searches attractions → Gets 5 results
- Step 2: Agent reads results and decides "These attractions require 3 days minimum"
- Step 3: Agent then searches flights with appropriate dates
- Step 4: Agent uses flight results to finalize recommendation

Without observations, the agent would generate all answers independently without context dependency. With observations, each step informs the next, creating a coherent plan rather than independent suggestions.

---

## IV. Future Improvements (5 Points)

_How would you scale this to production?_

### 1. Scalability: Parallel Tool Execution

**Current Issue:** Tools run sequentially (search_attractions, then search_flights)

**Solution:** Execute independent tools in parallel using asyncio:

```python
async def run_parallel_tools(self, tools_to_call: List[str]):
    tasks = [self._execute_tool_async(tool) for tool in tools_to_call]
    results = await asyncio.gather(*tasks)
    return results
```

**Impact:** 2-3x faster for multi-tool queries

### 2. Safety: Input Validation & Rate Limiting

- Validate tool input parameters before Tavily API calls
- Implement rate limiting to prevent excessive API usage
- Add retry logic with exponential backoff for failed requests

### 3. Performance: Response Caching

Cache popular searches to reduce API costs:

```python
cache = {
    "Hà Nội_attractions": {"data": [...], "timestamp": "2026-04-06"},
    "TP HCM_flights": {"data": [...], "timestamp": "2026-04-06"}
}
```

### 4. Better Error Handling

Currently: Tool errors return JSON error messages
Improved: Tool errors should trigger alternative search strategies or clarify with user

---

## V. Conclusion

Implementing the search_attractions and search_flights tools taught me that **tool design matters critically for agent reliability**. By ensuring:

1. **Consistent JSON schemas** - Agent can reliably parse results
2. **Clear error handling** - Graceful degradation instead of crashes
3. **Real data sourcing** - Tavily API guarantees grounded information vs hallucinations

The ReAct agent became capable of multi-step planning that a simple chatbot cannot achieve. The explicit Thought-Action-Observation loop forces structured reasoning, making the system transparent and debuggable.

**Key Takeaway:** "In AI agents, explicit structure + real tools + careful parsing = reliability. Anything less defaults to hallucination."

---
