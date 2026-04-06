# Workflow - Lab 3: Travel ReAct Agent

## 1. Tổng quan dự án

Dự án xây dựng một **ReAct Agent** (Reasoning + Acting) cho lĩnh vực du lịch. Agent sử dụng vòng lặp **Thought → Action → Observation** để trả lời các câu hỏi phức tạp bằng cách gọi tool thực tế thay vì hallucinate.

### Kiến trúc tổng thể

```
User Query
    │
    ▼
┌──────────────────────────┐
│      ReAct Agent          │
│  (src/agent/agent.py)     │
│                           │
│  Thought → Action →       │
│  Observation → ... →      │
│  Final Answer             │
└─────────┬────────────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌─────────┐ ┌───────────────────┐
│   LLM   │ │      Tools        │
│Provider  │ │    (4 tools)      │
└─────────┘ └───────────────────┘
    │               │
    ▼               ▼
┌─────────┐ ┌───────────────────┐
│ OpenAI  │ │ weather           │
│ Gemini  │ │ search_attractions│
│ Local   │ │ search_flights    │
│ (Phi-3) │ │ planning          │
└─────────┘ └───────────────────┘
    │
    ▼
┌──────────────────────────┐
│      Telemetry            │
│  Logger + Metrics         │
│  (logs/*.log - JSON)      │
└──────────────────────────┘
```

---

## 2. Cấu trúc thư mục

```
Lab3-35/
├── src/
│   ├── agent/
│   │   └── agent.py              # ReAct Agent - vòng lặp chính
│   ├── core/
│   │   ├── llm_provider.py       # Abstract Base Class cho LLM
│   │   ├── openai_provider.py    # OpenAI implementation
│   │   ├── gemini_provider.py    # Google Gemini implementation
│   │   └── local_provider.py     # Local model (llama-cpp)
│   ├── tools/
│   │   ├── weather.py            # weather - Dự báo thời tiết
│   │   ├── search_attractions.py # search_attractions - Tìm địa điểm tham quan
│   │   ├── search_flights.py     # search_flights - Tìm chuyến bay
│   │   └── planning.py           # planning - Lên kế hoạch du lịch
│   └── telemetry/
│       ├── logger.py             # Structured JSON logger
│       └── metrics.py            # Performance tracking (tokens, latency, cost)
├── tests/
│   ├── test_travel_agent.py      # 5 test cases (easy → hard)
│   └── test_local.py             # Test local model
├── logs/                         # JSON log files (auto-generated)
├── report/                       # Báo cáo lab
├── .env                          # API keys (không commit)
├── .env.example                  # Template cho .env
├── requirements.txt              # Dependencies
└── README.md                     # Hướng dẫn sử dụng
```

---

## 3. Workflow chi tiết

### 3.1. Setup ban đầu

```bash
# 1. Clone repo
git clone <repo-url>
cd Lab3-35

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Cấu hình API keys
cp .env.example .env
# Sửa .env: thêm OPENAI_API_KEY, GEMINI_API_KEY, WEATHER_API_KEY
```

### 3.2. Luồng xử lý của ReAct Agent

```
┌─────────────────────────────────────────────────────┐
│                    User Input                        │
│  "What's the weather in Paris on 2026-04-10?"       │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Step 1: LLM generates Thought + Action              │
│                                                       │
│  Thought: I need to call the weather tool for Paris.  │
│  Action: weather({"city":"Paris","start_date":"2026-04-10","end_date":"2026-04-10"}) │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Step 2: Agent parses Action bằng regex               │
│                                                       │
│  tool_name = "weather"                                │
│  args = {"city": "Paris", "start_date": "2026-04-10", "end_date": "2026-04-10"} │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Step 3: Execute tool → gọi weatherapi.com            │
│                                                       │
│  Observation: {"status": "success", "city": "Paris",  │
│    "temperature_celsius": 15, "condition": "Cloudy"}  │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Step 4: LLM nhận Observation → tạo Final Answer      │
│                                                       │
│  Final Answer: The weather in Paris on April 10 is    │
│  cloudy with a temperature of 15°C.                   │
└──────────────────────────────────────────────────────┘
```

**Với multi-step query**, vòng lặp lặp lại nhiều lần (tối đa `max_steps=10`):

```
User: "Plan a budget trip to Tokyo, check weather, flights from Hanoi, and attractions"

→ Thought 1 → Action: search_attractions({"city":"Tokyo"})                          → Observation 1
→ Thought 2 → Action: weather({"city":"Tokyo","start_date":"...","end_date":"..."})  → Observation 2
→ Thought 3 → Action: search_flights({"departure_city":"Hanoi","destination_city":"Tokyo","departure_date":"..."}) → Observation 3
→ Thought 4 → Action: planning({"destination":"Tokyo","start_date":"...","end_date":"...","budget":"low"})         → Observation 4
→ Final Answer: [Tổng hợp tất cả thông tin từ 4 tools]
```

### 3.3. Các Tools có sẵn

| Tool | Input | Mô tả |
|------|-------|--------|
| `weather` | city, start_date, end_date | Dự báo thời tiết theo khoảng ngày (nhiệt độ, mưa, độ ẩm) |
| `search_attractions` | city | Tìm kiếm địa điểm tham quan nổi bật tại thành phố |
| `search_flights` | departure_city, destination_city, departure_date | Tìm thông tin chuyến bay và giá vé |
| `planning` | destination, start_date, end_date, interests, budget | Lên kế hoạch du lịch chi tiết theo từng ngày |

### 3.4. Provider switching

Agent hỗ trợ chuyển đổi giữa các LLM provider:

```python
# OpenAI
from src.core.openai_provider import OpenAIProvider
llm = OpenAIProvider(model_name="gpt-4o", api_key=OPENAI_API_KEY)

# Gemini
from src.core.gemini_provider import GeminiProvider
llm = GeminiProvider(model_name="gemini-1.5-flash", api_key=GEMINI_API_KEY)

# Local (Phi-3 via llama-cpp)
from src.core.local_provider import LocalProvider
llm = LocalProvider(model_path="./models/Phi-3-mini-4k-instruct-q4.gguf")
```

Tất cả đều implement interface `LLMProvider` (abstract class) với 2 method: `generate()` và `stream()`.

---

## 4. Chạy test

```bash
# Chạy toàn bộ test suite (5 test cases)
pytest tests/test_travel_agent.py -v -s

# Chạy test riêng lẻ
pytest tests/test_travel_agent.py::TestTravelAgent::test_case_1_simple_weather_query -v -s

# Test weather API trực tiếp
python test_weather_api.py
```

### 5 Test Cases

| # | Tên | Độ khó | Mô tả |
|---|------|--------|--------|
| 1 | Simple Weather Query | Easy | Hỏi thời tiết → 1 tool call |
| 2 | Destination Info | Easy | Hỏi thông tin điểm đến → 1 tool call |
| 3 | Multi-Step Trip Planning | Medium | search_attractions + weather + planning → 3+ tool calls |
| 4 | Budget Trip Calculation | Medium | search_flights + planning → 2+ tool calls |
| 5 | Complex Trip with Constraints | Hard | weather + search_attractions + search_flights + planning → 4 tool calls |

---

## 5. Telemetry & Logging

Mọi action đều được log dưới dạng JSON structured:

```json
{
  "timestamp": "2026-04-06T09:00:00.000Z",
  "event": "TOOL_EXECUTED",
  "data": {
    "step": 0,
    "tool": "weather",
    "observation_length": 245
  }
}
```

**Các event types:**
- `AGENT_START` - Agent bắt đầu xử lý query
- `LLM_RESPONSE` - LLM trả về response (step, tokens)
- `ACTION_PARSED` - Parse được Action từ response
- `TOOL_EXECUTED` - Tool thực thi thành công
- `TOOL_ERROR` - Tool gặp lỗi
- `NO_ACTION_FOUND` - Không parse được Action
- `FINAL_ANSWER_FOUND` - Tìm thấy Final Answer
- `MAX_STEPS_REACHED` - Đạt giới hạn bước
- `AGENT_END` - Kết thúc

Log files lưu tại `logs/YYYY-MM-DD.log`.

---

## 6. Luồng phát triển

```
1. Đọc README.md và SCORING.md để hiểu yêu cầu
           │
           ▼
2. Setup .env với API keys
           │
           ▼
3. Implement/cải thiện ReAct loop (src/agent/agent.py)
   - System prompt
   - Action parsing (regex)
   - Tool execution
   - Observation handling
           │
           ▼
4. Thêm/sửa tools (src/tools/)
   - Kết nối API thật
   - Xử lý error
           │
           ▼
5. Chạy test suite
   pytest tests/test_travel_agent.py -v -s
           │
           ▼
6. Phân tích logs (logs/*.log)
   - Tìm hallucination
   - Tìm parsing errors
   - Đo performance
           │
           ▼
7. Viết báo cáo (report/)
   - So sánh Chatbot vs ReAct Agent
   - Failure analysis từ logs
```

---

## 7. Lưu ý quan trọng

- **API Keys**: Không commit `.env` vào git. Dùng `.env.example` làm template.
- **Rate limits**: weatherapi.com free tier giới hạn 14 ngày forecast, Tavily free tier giới hạn số request/ngày.
- **Max steps**: Agent giới hạn 10 bước. Nếu query phức tạp cần nhiều hơn, tăng `max_steps`.
- **Planning tool**: Sử dụng OpenAI GPT-4o, chi phí token cao với lịch trình dài ngày.
- **Regex parsing**: Action phải đúng format `tool_name({"key":"value"})`. LLM đôi khi sinh sai format → cần cải thiện parsing hoặc prompt.
