import os
import json
import asyncio
from datetime import datetime

import httpx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from agents import (
    function_tool, 
    Agent, 
    Runner, 
    ModelSettings, 
    handoff, 
    HandoffInputData
)
from agents.extensions import handoff_filters

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

# ── Handoff filters ─────────────────────────────────────────────────────────
def finance_handoff_filter(handoff_data: HandoffInputData) -> HandoffInputData:
    # We could choose to filter history or modify the messages here
    print("[HANDOFF] Finance handoff filter called")
    return handoff_data

def spanish_handoff_filter(handoff_data: HandoffInputData) -> HandoffInputData:
    # Remove tool-related messages for simplicity
    print("[HANDOFF] Spanish handoff filter called")
    return handoff_filters.remove_all_tools(handoff_data)

# ── agent definitions ────────────────────────────────────────────────────────
# Primary utility assistant
utility_agent = Agent(
    name="UtilityAssistant",
    instructions="""
    You are an AI assistant with access to numerical, finance, web-search, and
    weather tools. Analyze the user request, decide which tool(s)
    help, call them, then reply concisely.
    
    If the user asks for detailed financial advice or complex financial calculations,
    hand off to the Financial Specialist.
    
    If the user speaks Spanish, hand off to the Spanish-speaking assistant.
    """,
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

# Financial specialist agent
finance_agent = Agent(
    name="FinancialSpecialist",
    instructions="""
    You are a specialized financial advisor AI with expertise in stocks, 
    investments, mortgages, and financial planning. Provide detailed, accurate
    financial advice using available tools. Be precise and professional.
    """,
    model="o4-mini",
    model_settings=ModelSettings(tool_choice="auto"),
    tools=[
        get_stock_price,
        calculate_mortgage,
    ],
    handoff_description="A financial specialist for complex financial queries."
)

# Spanish-speaking agent
spanish_agent = Agent(
    name="SpanishAssistant",
    instructions="""
    Eres un asistente AI que habla español y tiene acceso a herramientas numéricas,
    financieras, de búsqueda web y del clima. Analiza la solicitud del usuario,
    decide qué herramienta(s) ayuda(n), llámalas y luego responde de manera concisa.
    """,
    model="o4-mini",
    model_settings=ModelSettings(tool_choice="auto"),
    tools=[
        add_numbers,
        get_weather,
        get_stock_price,
        search_web,
        calculate_mortgage,
    ],
    handoff_description="A Spanish-speaking assistant for Spanish language queries."
)

# Add handoffs to the primary agent
utility_agent = Agent(
    name=utility_agent.name,
    instructions=utility_agent.instructions,
    model=utility_agent.model,
    model_settings=utility_agent.model_settings,
    tools=utility_agent.tools,
    handoffs=[
        handoff(finance_agent, input_filter=finance_handoff_filter),
        handoff(spanish_agent, input_filter=spanish_handoff_filter),
    ],
)

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Session storage for continuing conversations
conversations = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "")
    session_id = data.get("session_id", "default")
    
    print(f"\n[REQUEST] Session {session_id}: Received message: {user_msg}")

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Get previous conversation or create new one
        if session_id not in conversations:
            print(f"[SESSION] Creating new conversation for session {session_id}")
            conversations[session_id] = []
        
        # Add user message to conversation
        conversations[session_id].append({"role": "user", "content": user_msg})
        
        # Run the agent
        print(f"[AGENT] Running agent for session {session_id}...")
        result = Runner.run_sync(
            utility_agent, 
            input=conversations[session_id]
        )
        
        # Store the result in conversation history
        conversations[session_id] = result.to_input_list()
        
        # Extract the final assistant message
        final_message = result.final_output
        print(f"[AGENT] Agent response: {final_message}")
        
        # Check if handoff occurred
        handoff_info = ""
        if hasattr(result, 'handoff_info') and result.handoff_info:
            handoff_agent = result.handoff_info.get('agent_name', 'Unknown')
            handoff_info = f"Handed off to: {handoff_agent}"
            print(f"[HANDOFF] {handoff_info}")
        
        return jsonify({
            "response": final_message,
            "handoff_info": handoff_info,
            "session_id": session_id
        })
    
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {error_msg}")
        return jsonify({"error": error_msg}), 500

if __name__ == "__main__":
    print("[SERVER] Starting Flask server for handoffs example...")
    app.run(debug=True, port=5000) 
