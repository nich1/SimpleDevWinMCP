import socket
import subprocess
import platform
import psutil
from fastmcp import FastMCP

def register_network_tools(mcp: FastMCP):
    """Register all network related tools"""
    
    @mcp.tool
    def ping_host(hostname: str) -> str:
        """Ping a hostname and return response time"""
        try:
            # Use appropriate ping command based on OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "4", hostname]
            else:
                cmd = ["ping", "-c", "4", hostname]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return f"Ping to '{hostname}' successful:\n{result.stdout}"
            else:
                return f"Ping to '{hostname}' failed:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Ping to '{hostname}' timed out"
        except Exception as e:
            return f"Error pinging host: {str(e)}"

    @mcp.tool
    def get_network_interfaces() -> str:
        """List all network interfaces and their IP addresses"""
        try:
            interfaces = psutil.net_if_addrs()
            result = "Network Interfaces:\n"
            
            for interface, addresses in interfaces.items():
                result += f"\n{interface}:\n"
                for addr in addresses:
                    if addr.family == socket.AF_INET:  # IPv4
                        result += f"  IPv4: {addr.address}"
                        if addr.netmask:
                            result += f" (netmask: {addr.netmask})"
                        result += "\n"
                    elif addr.family == socket.AF_INET6:  # IPv6
                        result += f"  IPv6: {addr.address}\n"
                    elif hasattr(socket, 'AF_PACKET') and addr.family == socket.AF_PACKET:  # MAC
                        result += f"  MAC: {addr.address}\n"
            
            return result
        except Exception as e:
            return f"Error getting network interfaces: {str(e)}"

    @mcp.tool
    def check_port_open(host: str, port: int) -> str:
        """Check if a specific port is open on a host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return f"Port {port} on {host} is OPEN"
            else:
                return f"Port {port} on {host} is CLOSED or filtered"
        except Exception as e:
            return f"Error checking port: {str(e)}"

    @mcp.tool
    def get_active_connections() -> str:
        """Show active network connections"""
        try:
            connections = psutil.net_connections(kind='inet')
            result = "Active Network Connections:\n"
            result += f"{'Protocol':<8} {'Local Address':<22} {'Remote Address':<22} {'Status':<12} {'PID':<8}\n"
            result += "-" * 80 + "\n"
            
            for conn in connections:
                protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                status = conn.status if conn.status else "N/A"
                pid = str(conn.pid) if conn.pid else "N/A"
                
                result += f"{protocol:<8} {local:<22} {remote:<22} {status:<12} {pid:<8}\n"
            
            return result
        except Exception as e:
            return f"Error getting active connections: {str(e)}"
