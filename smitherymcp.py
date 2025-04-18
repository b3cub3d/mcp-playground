import os
api_key = os.environ.get('SMITHERY_API_KEY', '2ca10fad-6bd5-47ee-af62-eba4ceca69a3')
# base_url = "https://server.smithery.ai/@lekt9/yahoo-finance-mcp/ws"
# base_url = "https://server.smithery.ai/@Alex2Yang97/yahoo-finance-mcp/ws"
base_url = "wss://server.smithery.ai/@Otman404/finance-mcp-server/ws"

import smithery
import mcp
from mcp.client.websocket import websocket_client
import asyncio

# Create Smithery URL with server endpoint
url = smithery.create_smithery_url(base_url, {}) + "&api_key=" + api_key
print(url)

async def main():
    # Connect to the server using websocket client
    async with websocket_client(url) as streams:
        async with mcp.ClientSession(*streams) as session:
            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {', '.join([t.name for t in tools_result.tools])}")

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=30))  # Add a timeout of 30 seconds
    except asyncio.TimeoutError:
        print("Operation timed out. The websocket connection may be hanging.")