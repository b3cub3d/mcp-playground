import os
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Heroku sits behind a reverse proxy and sets Host to "<app>.herokuapp.com".
# The MCP Python SDK enables DNS-rebinding protection in some configurations,
# which can reject Heroku's Host header with HTTP 421. For this demo server,
# disable it so remote clients can connect.
mcp = FastMCP(
    "hello-world",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}! This is a remote MCP server running on Heroku."

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

app = mcp.streamable_http_app()