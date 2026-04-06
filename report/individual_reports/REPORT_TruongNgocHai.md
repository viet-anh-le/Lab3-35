# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trương Ngọc Hải
- **Student ID**: 2A202600332
- **Date**: 2026-04-06
- **GitHub Team**: [Repo Lab3-team 35 here](https://github.com/viet-anh-le/Lab3-35.git)

---

## I. Technical Contribution (15 Points)

In this project, my main technical contribution was **System Evaluation,
Telemetry Analysis, and Technical Documentation**. I was responsible for
designing test scenarios, collecting system logs, and conducting **Root
Cause Analysis (RCA)** to evaluate the agent's performance.

- **Modules Evaluated**: Managed the test suite and analyzed telemetry
  logs from `src/tools/travel_tools.py` and the ReAct workflow.
- **Testing Highlights**: I directly designed and executed
  **Experiment 3: ChatBot vs v1 vs v2**. By measuring metrics such as
  **Response Time**, **Tool Usage Rate**, and **Hallucination Rate**,
  I provided quantitative evidence that guided the team's debugging
  decisions.
- **Documentation**: I compiled the team's final report, consolidating
  system metrics and restructuring the reasoning workflow into
  **Cost-Benefit Analysis tables** to demonstrate that the trade-off
  between execution time (**+59%**) and accuracy (**100% factual
  correctness**) is entirely reasonable for production environments.

---

## II. Debugging Case Study (10 Points)

Through continuous log monitoring and system measurement, I identified
and analyzed a critical logical flaw in the agent workflow.

- **Problem Description**: In complex test cases (**Test 3--5**),
  instead of calling APIs to retrieve Tokyo travel data, the system
  returned fabricated information or malformed placeholder text such
  as `[information here]`.

- **Log Source**: Extracted from Telemetry Evidence (_Query 1 -
  Weather_):

  ```json
  "agent_version": "v1",
  "prompt_quality": "poor",
  "NO_ACTION_FOUND", {"treating_as_final": true}
  ```

  _(The LLM decided to skip the `get_weather` tool and generated fake
  weather data instead.)_

- **Diagnosis**: Through comparative analysis, I determined that the
  root cause did **not** lie in the Python code itself, but rather in
  the overly permissive **System Prompt v1**. The agent incorrectly
  overestimated the reliability of its internal knowledge compared to
  external tool calls, leading to an estimated **\~50% tool skip
  rate**.

- **Solution**: Based on my debugging report, the team restructured
  the **System Prompt** into **STRICT MODE**, where tool usage is
  mandatory before answering. After the update, I reran the full test
  suite and verified that the **tool usage rate reached 100%**, while
  the **hallucination rate dropped to 0**.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

From the perspective of someone directly involved in system evaluation,
I observed several fundamental differences:

- **Reasoning**: While a traditional chatbot generates answers through
  static next-token probability estimation, the agent uses the
  **Thought** block for explicit planning. Log observations showed
  that the agent can recognize missing information autonomously (e.g.,
  realizing that flight prices are required before estimating a trip
  budget).
- **Reliability**: Enforcing tool calls increased the average token
  cost to approximately **1,133 tokens/query** (around **\$0.0015**)
  and made the system **1.9× slower** than the v1 agent. However, in
  domains requiring strict factual correctness, such as **Travel** or
  **Finance**, this cost is extremely cheap compared to the benefit of
  completely eliminating hallucinations.
- **Observation**: The **Observation** data acts as a **state update
  mechanism**. It helps the LLM decide the next action, functioning
  similarly to a **state machine**, rather than a purely stateless
  text generation function.

---

## IV. Future Improvements (5 Points)

To further improve this **Travel Agent** system, especially in a **Big
Data** environment with distributed workloads, I propose the following:

- **Scalability**: Replace the current sequential API calling workflow
  with a distributed architecture. Specifically, **Apache Kafka** can
  be integrated to orchestrate tool-call messages. Once the agent
  produces an action, the request can be pushed into a Kafka topic,
  where independent workers process the API calls and return
  observations, significantly improving scalability for thousands of
  concurrent requests.
- **Safety**: Build a **Supervisor Framework** using a smaller
  language model as an output validation gateway before returning
  responses to the frontend, ensuring the output always follows the
  correct JSON schema.
- **Performance**: Apply a **Data Lake / MinIO combined with Spark**
  architecture to analyze logs and user history, enabling better
  personalized context for the ReAct workflow instead of relying
  solely on public APIs.
