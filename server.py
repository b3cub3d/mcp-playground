from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello-world")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}! This is a remote MCP server running on Heroku."

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

app = mcp.streamable_http_app()