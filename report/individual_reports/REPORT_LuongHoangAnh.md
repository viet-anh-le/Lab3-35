# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Luong Hoang Anh
- **Student ID**: 2A202600472
- **Date**: 2026-04-06
- **Github Repo**: https://github.com/viet-anh-le/Lab3-35.git

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/agent/agent.py` (The ReAct Reasoning Engine)
- **Code Highlights**: 
    - **Regex-based Parser**: Implemented `re.search(r"Action:\s*(\w+)\((.*?)\)")` to extract tool names and arguments from raw LLM text.
    - **Strict System Prompt (v2)**: Engineered a "Zero-Tolerance" prompt that mandates tool usage and forbids placeholders.
    - **Execution Loop**: Built the `while steps < self.max_steps` controller to orchestrate the Thought → Action → Observation flow.
- **Documentation**: My code serves as the brain. It forces the LLM to justify its logic in a `Thought` block before execution. Without this rigid loop, the agent reverts to a basic, unreliable chatbot that guesses rather than verifies.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: The Agent suffered from severe hallucinations, providing fake weather data instead of calling the `get_weather` tool.
- **Log Source**: `logs/2026-04-06.log` – Event: `NO_ACTION_FOUND`.
- **Diagnosis**: The **v1 System Prompt** was far too "permissive." Using phrases like "You can use tools" gave the LLM the ego to think it already knew the answer. It’s a classic failure of weak prompt instruction.
- **Solution**: Switched to **System Prompt v2 (STRICT)**. I added: `"YOU MUST USE TOOLS FIRST - No exceptions!"` and explicit routing rules. This forced tool usage from 50% to 100%.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: The `Thought` block acts as a "forced pause." It makes the agent decompose complex tasks into logical steps. This prevents the "jumping to conclusions" behavior seen in standard chatbots.
2.  **Reliability**: The Agent actually performs *worse* on trivial questions (e.g., "What is the capital of France?"). The ReAct loop adds unnecessary latency and cost for facts the LLM already knows perfectly.
3.  **Observation**: Environment feedback is the "reality check." If a tool returns an error, the Agent sees the `Observation` and uses the next `Thought` to pivot or fix the query instead of crashing.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Implement **Asynchronous Tool Calling** to execute multiple independent tools (like weather and flights) simultaneously to reduce wait times.
- **Safety**: Add a **Guardrail Validator** layer to sanitize tool arguments before execution, preventing the LLM from injecting "trash" data into the system.
- **Performance**: Use **Semantic Caching** for common Thought-Action pairs to save API costs and provide near-instant responses for repeat queries.

---