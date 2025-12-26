from fastmcp import FastMCP

mcp = FastMCP("add-mcp-http")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers and return the result"""
    return a + b
