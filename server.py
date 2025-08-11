from fastmcp import FastMCP
from file_system import register_file_system_tools
from process import register_process_tools
from system_resource import register_system_resource_tools
from network import register_network_tools

# Create the main MCP server instance
mcp = FastMCP("System Monitoring & File Helper")

# Register all tool modules
register_file_system_tools(mcp)
register_process_tools(mcp)
register_system_resource_tools(mcp)
register_network_tools(mcp)
register_development_tools(mcp)

if __name__ == "__main__":
    mcp.run()

