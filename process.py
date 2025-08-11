import json
import psutil
from datetime import datetime
from fastmcp import FastMCP

def _format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def register_process_tools(mcp: FastMCP):
    """Register all process management related tools"""
    
    @mcp.tool
    def get_process_tree(pid: int) -> str:
        """Show process tree for a given PID (parent/child relationships)"""
        try:
            process = psutil.Process(pid)
            
            def build_tree(proc, level=0):
                indent = "  " * level
                try:
                    name = proc.name()
                    cpu = proc.cpu_percent()
                    memory = proc.memory_info().rss
                    result = f"{indent}├─ {proc.pid} {name} (CPU: {cpu}%, Memory: {_format_size(memory)})\n"
                    
                    children = proc.children()
                    for child in children:
                        result += build_tree(child, level + 1)
                    
                    return result
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return f"{indent}├─ {proc.pid} <access denied>\n"
            
            result = f"Process Tree for PID {pid}:\n"
            result += build_tree(process)
            
            return result
        except psutil.NoSuchProcess:
            return f"Error: Process with PID {pid} not found"
        except Exception as e:
            return f"Error getting process tree: {str(e)}"

    @mcp.tool
    def get_top_cpu_processes(limit: int = 5) -> str:
        """Get top N processes by CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            result = f"Top {limit} processes by CPU usage:\n"
            result += f"{'PID':<8} {'CPU%':<8} {'Name'}\n"
            result += "-" * 40 + "\n"
            
            for proc in processes[:limit]:
                pid = proc['pid']
                cpu = proc['cpu_percent'] or 0
                name = proc['name'] or 'N/A'
                result += f"{pid:<8} {cpu:<8.1f} {name}\n"
            
            return result
        except Exception as e:
            return f"Error getting top CPU processes: {str(e)}"

    @mcp.tool
    def get_top_memory_processes(limit: int = 5) -> str:
        """Get top N processes by memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    info = proc.info
                    info['memory_rss'] = info['memory_info'].rss if info['memory_info'] else 0
                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_rss'], reverse=True)
            
            result = f"Top {limit} processes by memory usage:\n"
            result += f"{'PID':<8} {'Memory':<12} {'Name'}\n"
            result += "-" * 40 + "\n"
            
            for proc in processes[:limit]:
                pid = proc['pid']
                memory = _format_size(proc['memory_rss'])
                name = proc['name'] or 'N/A'
                result += f"{pid:<8} {memory:<12} {name}\n"
            
            return result
        except Exception as e:
            return f"Error getting top memory processes: {str(e)}"

    @mcp.tool
    def check_if_process_running(name: str) -> str:
        """Check if a process with given name is currently running"""
        try:
            running_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if name.lower() in proc.info['name'].lower():
                        running_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if running_processes:
                result = f"Found {len(running_processes)} process(es) matching '{name}':\n"
                for proc in running_processes:
                    result += f"  PID {proc['pid']}: {proc['name']}\n"
                return result
            else:
                return f"No processes found matching '{name}'"
        except Exception as e:
            return f"Error checking if process is running: {str(e)}"

    @mcp.tool
    def list_processes() -> str:
        """List all running processes with PID, name, and CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                try:
                    info = proc.info
                    info['memory_rss'] = info['memory_info'].rss if info['memory_info'] else 0
                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by PID
            processes.sort(key=lambda x: x['pid'])
            
            result = f"Running Processes ({len(processes)} total):\n"
            result += f"{'PID':<8} {'CPU%':<8} {'Memory':<12} {'Status':<12} {'Name'}\n"
            result += "-" * 60 + "\n"
            
            for proc in processes:
                pid = proc['pid']
                cpu = proc['cpu_percent'] or 0
                memory = _format_size(proc['memory_rss'])
                status = proc['status'] or 'N/A'
                name = proc['name'] or 'N/A'
                result += f"{pid:<8} {cpu:<8.1f} {memory:<12} {status:<12} {name}\n"
            
            return result
        except Exception as e:
            return f"Error listing processes: {str(e)}"

    @mcp.tool
    def get_process_info(pid: int) -> str:
        """Get detailed info about a specific process by PID"""
        try:
            process = psutil.Process(pid)
            
            info = {
                "pid": process.pid,
                "name": process.name(),
                "exe": process.exe(),
                "cwd": process.cwd(),
                "status": process.status(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": {
                    "rss": _format_size(process.memory_info().rss),
                    "vms": _format_size(process.memory_info().vms)
                },
                "num_threads": process.num_threads(),
                "username": process.username()
            }
            
            # Get parent process info
            try:
                parent = process.parent()
                if parent:
                    info["parent"] = {"pid": parent.pid, "name": parent.name()}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                info["parent"] = None
            
            # Get command line arguments
            try:
                info["cmdline"] = " ".join(process.cmdline())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                info["cmdline"] = "N/A"
            
            return json.dumps(info, indent=2)
        except psutil.NoSuchProcess:
            return f"Error: Process with PID {pid} not found"
        except psutil.AccessDenied:
            return f"Error: Access denied for process with PID {pid}"
        except Exception as e:
            return f"Error getting process info: {str(e)}"

    @mcp.tool
    def find_process_by_name(name: str) -> str:
        """Find processes by name (partial match)"""
        try:
            matching_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                try:
                    if name.lower() in proc.info['name'].lower():
                        info = proc.info
                        info['memory_rss'] = info['memory_info'].rss if info['memory_info'] else 0
                        matching_processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if not matching_processes:
                return f"No processes found matching '{name}'"
            
            result = f"Found {len(matching_processes)} process(es) matching '{name}':\n"
            result += f"{'PID':<8} {'CPU%':<8} {'Memory':<12} {'Status':<12} {'Name'}\n"
            result += "-" * 60 + "\n"
            
            for proc in matching_processes:
                pid = proc['pid']
                cpu = proc['cpu_percent'] or 0
                memory = _format_size(proc['memory_rss'])
                status = proc['status'] or 'N/A'
                name = proc['name'] or 'N/A'
                result += f"{pid:<8} {cpu:<8.1f} {memory:<12} {status:<12} {name}\n"
            
            return result
        except Exception as e:
            return f"Error finding processes: {str(e)}"
