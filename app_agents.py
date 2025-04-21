import os
import json
import asyncio
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
    print(f"[TOOL] add_numbers called with a={a}, b={b}")
    result = str(a + b)
    print(f"[TOOL] add_numbers result: {result}")
    return result

@function_tool
def get_weather(location: str | None = None) -> str:
    print(f"[TOOL] get_weather called with location={location or 'default'}")
    result = f"The weather in {location or 'the default location'} is sunny and 75°F."
    print(f"[TOOL] get_weather result: {result}")
    return result

@function_tool
def get_stock_price(ticker: str) -> str:
    print(f"[TOOL] get_stock_price called with ticker={ticker}")
    prices = {
        "AAPL": 187.45, "MSFT": 425.22, "GOOGL": 175.33,
        "AMZN": 182.87, "META": 478.22, "TSLA": 175.34,
    }
    price = prices.get(ticker.upper(), 100.00)
    result = f"The current stock price of {ticker.upper()} is ${price}"
    print(f"[TOOL] get_stock_price result: {result}")
    return result

@function_tool
def search_web(query: str) -> str:
    print(f"[TOOL] search_web called with query={query}")
    today = datetime.now().strftime("%B %d, %Y")
    if "news" in query.lower():
        stub = ("1. Global markets rally as inflation eases\n"
                "2. Tech industry sees surge in AI investments\n"
                "3. New climate agreement reached at summit")
    elif "recipe" in query.lower():
        stub = ("1. Easy pasta carbonara recipe—ready in 15 min\n"
                "2. Healthy breakfast smoothies\n"
                "3. Perfect chocolate‑chip cookies")
    else:
        stub = ("1. Top results for your search\n"
                "2. Related information from reliable sources\n"
                "3. Wikipedia entries related to your query")
    result = f"Web search results for '{query}' as of {today}:\n{stub}"
    print(f"[TOOL] search_web result: {result}")
    return result

@function_tool
def calculate_mortgage(principal: float, interest_rate: float, years: int) -> str:
    print(f"[TOOL] calculate_mortgage called with principal={principal}, interest_rate={interest_rate}, years={years}")
    r = interest_rate / 100 / 12
    n = years * 12
    payment = principal / n if r == 0 else principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    result = (f"For a ${principal:,.0f} mortgage at {interest_rate}% over {years} years, "
            f"monthly payment ≈ ${payment:,.2f}")
    print(f"[TOOL] calculate_mortgage result: {result}")
    return result

# ── agent and runner ─────────────────────────────────────────────────────────
assistant_instructions = """
You are an AI assistant with access to numerical, finance, web‑search, and
weather tools. Analyse the user request, decide which tool(s)
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
    ],
)

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# --- inside /chat route ---
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    print(f"\n[REQUEST] Received message: {user_msg}")

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("[AGENT] Running agent...")
        # run the agent once and get a RunResult
        result = Runner.run_sync(agent, user_msg)
        print(f"[AGENT] Agent response: {result.final_output}")
        return jsonify({"response": result.final_output})
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {error_msg}")
        return jsonify({"error": error_msg}), 500

if __name__ == "__main__":
    print("[SERVER] Starting Flask server...")
    app.run(debug=True)

