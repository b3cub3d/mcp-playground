from mcp.server.fastmcp import FastMCP, StreamableHttpApp

mcp = FastMCP("hello-world")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}! This is a remote MCP server running on Heroku."

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
