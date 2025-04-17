from flask import Flask, request, jsonify
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# Example complex query that should use all tools: 
# "What is the weather in San Francisco, CA? Also, what is the current price of Apple (AAPL) stock? Additionally, find information on the latest news about the stock market. Finally, calculate the monthly mortgage payment for a $500,000 loan with a 3.5% interest rate over 30 years."

# MCP Tool definitions
def add_numbers(a, b):
    """Add two numbers and return the result."""
    print(f"[TOOL] add_numbers executed with args: a={a}, b={b}")
    result = a + b
    print(f"[TOOL] add_numbers result: {result}")
    return result

def get_weather(location=None):
    """Get weather for a location (currently returns hardcoded response)."""
    print(f"[TOOL] get_weather executed with location: {location if location else 'default'}")
    result = f"The weather in {location if location else 'the default location'} is sunny and 75°F."
    print(f"[TOOL] get_weather result: {result}")
    return result

def get_stock_price(ticker):
    """Get the current stock price for a given ticker symbol."""
    print(f"[TOOL] get_stock_price executed for ticker: {ticker}")
    # Simulate different prices for different stocks
    prices = {
        "AAPL": 187.45,
        "MSFT": 425.22,
        "GOOGL": 175.33,
        "AMZN": 182.87,
        "META": 478.22,
        "TSLA": 175.34,
    }
    price = prices.get(ticker.upper(), 100.00)  # Default price if ticker not found
    result = f"The current stock price of {ticker.upper()} is ${price}"
    print(f"[TOOL] get_stock_price result: {result}")
    return result

def search_web(query):
    """Simulates a web search and returns results."""
    print(f"[TOOL] search_web executed with query: {query}")
    current_date = datetime.now().strftime("%B %d, %Y")
    result = f"Web search results for '{query}' as of {current_date}:\n"
    
    # Simulate different search results based on keywords
    if "news" in query.lower():
        result += "1. Latest headlines: Global markets rally as inflation eases\n"
        result += "2. Tech industry sees surge in AI investments\n"
        result += "3. New climate agreement reached at international summit"
    elif "recipe" in query.lower():
        result += "1. Easy pasta carbonara recipe: Ready in 15 minutes\n"
        result += "2. Healthy smoothie recipes for breakfast\n"
        result += "3. The perfect chocolate chip cookie recipe"
    else:
        result += "1. Top results for your search\n"
        result += "2. Related information from reliable sources\n"
        result += "3. Wikipedia entries related to your query"
    
    print(f"[TOOL] search_web result: {result}")
    return result

def calculate_mortgage(principal, interest_rate, years):
    """Calculate monthly mortgage payment."""
    print(f"[TOOL] calculate_mortgage executed with args: principal={principal}, interest_rate={interest_rate}, years={years}")
    
    # Convert annual interest rate to monthly rate
    monthly_rate = interest_rate / 100 / 12
    # Total number of payments
    payments = years * 12
    
    # Calculate monthly payment using the mortgage formula
    if monthly_rate == 0:
        # Edge case: if interest rate is 0, it's just the principal divided by months
        monthly_payment = principal / payments
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** payments) / ((1 + monthly_rate) ** payments - 1)
    
    result = f"For a ${principal:,.2f} mortgage with {interest_rate}% interest over {years} years, your monthly payment would be ${monthly_payment:.2f}"
    print(f"[TOOL] calculate_mortgage result: {result}")
    return result

# MCP Tool registry
tools = [
    {
        "type": "function",
        "function": {
            "name": "add_numbers",
            "description": "Add two numbers together",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The first number"},
                    "b": {"type": "number", "description": "The second number"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city and state, e.g. San Francisco, CA"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current price of a stock by its ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "The stock ticker symbol, e.g. AAPL for Apple"}
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information on a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_mortgage",
            "description": "Calculate monthly mortgage payment based on principal, interest rate, and term",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {"type": "number", "description": "The mortgage principal amount in dollars"},
                    "interest_rate": {"type": "number", "description": "Annual interest rate as a percentage (e.g., 5.5 for 5.5%)"},
                    "years": {"type": "integer", "description": "The mortgage term in years"}
                },
                "required": ["principal", "interest_rate", "years"]
            }
        }
    }
]

# Tool dispatcher
def execute_tool(tool_name, tool_args):
    print(f"[DISPATCHER] Executing tool: {tool_name} with args: {tool_args}")
    if tool_name == "add_numbers":
        result = add_numbers(**tool_args)
    elif tool_name == "get_weather":
        result = get_weather(**tool_args)
    elif tool_name == "get_stock_price":
        result = get_stock_price(**tool_args)
    elif tool_name == "search_web":
        result = search_web(**tool_args)
    elif tool_name == "calculate_mortgage":
        result = calculate_mortgage(**tool_args)
    else:
        result = f"Unknown tool: {tool_name}"
        print(f"[DISPATCHER] {result}")
    
    print(f"[DISPATCHER] Tool execution complete: {result}")
    return result

@app.route('/chat', methods=['POST'])
def chat():
    # Get the chat message from the request
    message = request.json.get('message', '')
    
    # Print the message to the console
    print(f"\n[REQUEST] Received message: {message}")
    
    # Initialize conversation with a system message and the user's message
    messages = [
        {"role": "developer", "content": """You are an AI assistant with access to various tools. Your goal is to help users by providing accurate information and performing calculations as needed.

When presented with a request:
1. Analyze what the user is asking for
2. Determine which tools (if any) would be helpful to answer the query
3. Use the tools in a logical sequence to gather information
4. Synthesize the results into a clear, helpful response

Available tools:
- add_numbers: For mathematical addition
- get_weather: To check weather conditions
- get_stock_price: To check current stock prices
- search_web: To find information on the web
- calculate_mortgage: To calculate monthly mortgage payments

Be conversational but concise. Prioritize accuracy and relevance in your responses."""},
        {"role": "user", "content": message}
    ]
    print(f"[CONVERSATION] Starting with user message: {message}")
    
    # Start reasoning loop
    loop_count = 0
    while True:
        loop_count += 1
        print(f"\n[LOOP {loop_count}] Calling OpenAI API")
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="o4-mini",  # Using the model you specified
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        
        response_message = response.choices[0].message
        print(f"[LOOP {loop_count}] Received response from OpenAI")
        
        # Add the assistant's response to the conversation
        messages.append(response_message.model_dump())
        
        # Check if the model wants to call a function
        if response_message.tool_calls:
            print(f"[LOOP {loop_count}] Model requested {len(response_message.tool_calls)} tool call(s)")
            
            # Loop through each tool call
            for i, tool_call in enumerate(response_message.tool_calls):
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"[LOOP {loop_count}] Tool call {i+1}: {function_name} with args: {function_args}")
                
                # Execute the function
                function_response = execute_tool(function_name, function_args)
                
                # Append the function response to the messages
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })
                
                print(f"[LOOP {loop_count}] Added tool response to conversation: {function_response}")
            
            print(f"[LOOP {loop_count}] All tool calls processed, continuing reasoning loop")
            # Continue the loop to get the next assistant response
            continue
        
        # If we get here, the assistant has completed its reasoning
        print(f"[LOOP {loop_count}] Model completed reasoning with final response")
        print(f"[RESPONSE] {response_message.content}")
        
        # Return the final response to the user
        return jsonify({"response": response_message.content})

if __name__ == '__main__':
    app.run(debug=True) 