import os
import json
from datetime import datetime

import httpx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from agents import function_tool, Agent, Runner, ModelSettings

# ── config ────────────────────────────────────────────────────────────────────
load_dotenv()

# ── tool definitions ─────────────────────────────────────────────────────────
@function_tool
def add_numbers(a: float, b: float) -> str:
    "Add two numbers and return the sum"
    return str(a + b)

@function_tool
def get_weather(location: str | None = None) -> str:
    return f"The weather in {location or 'the default location'} is sunny and 75°F."

@function_tool
def get_stock_price(ticker: str) -> str:
    prices = {
        "AAPL": 187.45, "MSFT": 425.22, "GOOGL": 175.33,
        "AMZN": 182.87, "META": 478.22, "TSLA": 175.34,
    }
    price = prices.get(ticker.upper(), 100.00)
    return f"The current stock price of {ticker.upper()} is ${price}"

@function_tool
def search_web(query: str) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    if "news" in query.lower():
        stub = ("1. Global markets rally as inflation eases\n"
                "2. Tech industry sees surge in AI investments\n"
                "3. New climate agreement reached at summit")
    elif "recipe" in query.lower():
        stub = ("1. Easy pasta carbonara recipe—ready in 15 min\n"
                "2. Healthy breakfast smoothies\n"
                "3. Perfect chocolate‑chip cookies")
    else:
        stub = ("1. Top results for your search\n"
                "2. Related information from reliable sources\n"
                "3. Wikipedia entries related to your query")
    return f"Web search results for '{query}' as of {today}:\n{stub}"

@function_tool
def calculate_mortgage(principal: float, interest_rate: float, years: int) -> str:
    r = interest_rate / 100 / 12
    n = years * 12
    payment = principal / n if r == 0 else principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return (f"For a ${principal:,.0f} mortgage at {interest_rate}% over {years} years, "
            f"monthly payment ≈ ${payment:,.2f}")

@function_tool
def get_current_time(timezone: str | None = None) -> str:
    payload = {"name": "get_current_time", "arguments": {}}
    if timezone:
        payload["arguments"]["timezone"] = timezone
    r = httpx.post(f"{MCP_URL}/tool", json=payload, timeout=10.0)
    r.raise_for_status()
    d = r.json()
    return (f"Current time in {d['timezone']}: {d['datetime']} "
            f"(DST active: {d['is_dst']})")

@function_tool
def convert_time(source_timezone: str, time: str, target_timezone: str) -> str:
    payload = {
        "name": "convert_time",
        "arguments": {
            "source_timezone": source_timezone,
            "time": time,
            "target_timezone": target_timezone,
        },
    }
    r = httpx.post(f"{MCP_URL}/tool", json=payload, timeout=10.0)
    r.raise_for_status()
    d = r.json()
    return (f"{time} in {source_timezone} equals {d['target']['datetime']} in "
            f"{target_timezone} (Δ {d['time_difference']})")

# ── agent and runner ─────────────────────────────────────────────────────────
assistant_instructions = """
You are an AI assistant with access to numerical, finance, web‑search,
weather and time tools. Analyse the user request, decide which tool(s)
help, call them, then reply concisely.
"""

agent = Agent(
    name="UtilityAssistant",
    instructions=assistant_instructions,
    model="o4-mini",
    model_settings=ModelSettings(tool_choice="auto"),
    tools=[
        add_numbers,
        get_weather,
        get_stock_price,
        search_web,
        calculate_mortgage,
        get_current_time,
        convert_time,
    ],
)

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# --- inside /chat route ---
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    # run the agent once and get a RunResult
    result = Runner.run_sync(agent, user_msg)      # ← correct usage
    return jsonify({"response": result.final_output})

if __name__ == "__main__":
    app.run(debug=True)

