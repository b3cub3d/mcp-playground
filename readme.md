# Flask Chat App with OpenAI and MCP Tools

A Flask application that integrates with OpenAI's language models and implements Model Control Protocol (MCP) tools for enhancing AI capabilities.

## Features

- Connects to OpenAI's API to process user messages
- Implements MCP tools for the AI to use:
  - `add_numbers`: A tool that adds two numbers
  - `get_weather`: A tool that returns weather information (currently hardcoded)
- Reasoning loop that allows the AI to call tools, receive results, and continue reasoning
- Final response generation based on the reasoning process

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Run the application:
   ```
   python app.py
   ```

## Usage

Send a POST request to the `/chat` endpoint with a JSON payload containing a message:

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 42 plus 7? Also, what's the weather like?"}'
```

The server will:
1. Send the message to OpenAI
2. Let the AI use the MCP tools as needed (add_numbers, get_weather)
3. Return the AI's final response that incorporates the tool results

```json
{
  "response": "42 plus 7 equals 49. As for the weather, it's sunny and 75°F in the default location."
}
```

## Extending

You can add more MCP tools by:
1. Adding a new function implementation
2. Registering it in the `tools` list with appropriate schema
3. Adding a case for it in the `execute_tool` function
