import os
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

# Heroku (and most reverse proxies) send a real Host header like
# "<app>.herokuapp.com". The MCP Python SDK's streamable-http transport applies
# host validation; allow Heroku + local dev explicitly.
try:
    from starlette.middleware.trustedhost import TrustedHostMiddleware

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1",
            "[::1]",
            "*.herokuapp.com",
        ],
    )
except Exception:
    # If the underlying app/middleware isn't available, we fall back to the
    # default app behavior rather than crashing at import time.
    pass