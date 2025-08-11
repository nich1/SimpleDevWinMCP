import os
import subprocess
import json
import psutil
import socket
import platform
from pathlib import Path
from fastmcp import FastMCP

def register_development_tools(mcp: FastMCP):
    """Register all development related tools"""
    
    # Git Tools
    @mcp.tool
    def git_status(directory: str = ".") -> str:
        """Check Git repository status"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "-b"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                if "not a git repository" in result.stderr.lower():
                    return f"Directory '{directory}' is not a Git repository"
                return f"Git error: {result.stderr}"
            
            lines = result.stdout.strip().split('\n')
            if not lines or lines == ['']:
                return f"Git repository in '{directory}' is clean (no changes)"
            
            # Parse the output
            branch_line = lines[0] if lines[0].startswith('##') else "## Unknown branch"
            branch_info = branch_line[3:]  # Remove '## '
            
            changes = []
            for line in lines[1:]:
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    status_desc = {
                        '??': 'Untracked',
                        'A ': 'Added',
                        'M ': 'Modified',
                        ' M': 'Modified (not staged)',
                        'D ': 'Deleted',
                        ' D': 'Deleted (not staged)',
                        'R ': 'Renamed',
                        'C ': 'Copied',
                        'AM': 'Added & Modified'
                    }.get(status, f'Status: {status}')
                    changes.append(f"  {status_desc}: {filename}")
            
            result_text = f"Git Status for '{directory}':\n"
            result_text += f"Branch: {branch_info}\n\n"
            if changes:
                result_text += "Changes:\n" + "\n".join(changes)
            else:
                result_text += "No changes detected"
            
            return result_text
            
        except subprocess.TimeoutExpired:
            return "Git command timed out"
        except FileNotFoundError:
            return "Git is not installed or not in PATH"
        except Exception as e:
            return f"Error checking Git status: {str(e)}"

    @mcp.tool
    def git_log(directory: str = ".", limit: int = 5) -> str:
        """Show Git commit history"""
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--oneline", "--graph", "--decorate"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                if "not a git repository" in result.stderr.lower():
                    return f"Directory '{directory}' is not a Git repository"
                return f"Git error: {result.stderr}"
            
            if not result.stdout.strip():
                return f"No commits found in repository '{directory}'"
            
            return f"Git Log for '{directory}' (last {limit} commits):\n\n{result.stdout}"
            
        except subprocess.TimeoutExpired:
            return "Git log command timed out"
        except FileNotFoundError:
            return "Git is not installed or not in PATH"
        except Exception as e:
            return f"Error getting Git log: {str(e)}"

    @mcp.tool
    def git_branches(directory: str = ".") -> str:
        """List Git branches"""
        try:
            # Get local branches
            local_result = subprocess.run(
                ["git", "branch"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if local_result.returncode != 0:
                if "not a git repository" in local_result.stderr.lower():
                    return f"Directory '{directory}' is not a Git repository"
                return f"Git error: {local_result.stderr}"
            
            # Get remote branches
            remote_result = subprocess.run(
                ["git", "branch", "-r"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            result_text = f"Git Branches for '{directory}':\n\n"
            
            # Parse local branches
            if local_result.stdout.strip():
                result_text += "Local branches:\n"
                for line in local_result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('*'):
                        result_text += f"  {line} (current)\n"
                    else:
                        result_text += f"  {line}\n"
            
            # Parse remote branches
            if remote_result.returncode == 0 and remote_result.stdout.strip():
                result_text += "\nRemote branches:\n"
                for line in remote_result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('origin/HEAD'):
                        result_text += f"  {line}\n"
            
            return result_text
            
        except subprocess.TimeoutExpired:
            return "Git branches command timed out"
        except FileNotFoundError:
            return "Git is not installed or not in PATH"
        except Exception as e:
            return f"Error getting Git branches: {str(e)}"

    @mcp.tool
    def git_diff(directory: str = ".", file_path: str = "") -> str:
        """Show Git differences"""
        try:
            cmd = ["git", "diff"]
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                if "not a git repository" in result.stderr.lower():
                    return f"Directory '{directory}' is not a Git repository"
                return f"Git error: {result.stderr}"
            
            if not result.stdout.strip():
                target = f" for file '{file_path}'" if file_path else ""
                return f"No differences found{target} in repository '{directory}'"
            
            target = f" for file '{file_path}'" if file_path else ""
            return f"Git Diff{target} for '{directory}':\n\n{result.stdout}"
            
        except subprocess.TimeoutExpired:
            return "Git diff command timed out"
        except FileNotFoundError:
            return "Git is not installed or not in PATH"
        except Exception as e:
            return f"Error getting Git diff: {str(e)}"

    @mcp.tool
    def git_config(directory: str = ".") -> str:
        """Show Git configuration"""
        try:
            result = subprocess.run(
                ["git", "config", "--list"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return f"Git config error: {result.stderr}"
            
            if not result.stdout.strip():
                return "No Git configuration found"
            
            # Parse and organize config
            config_lines = result.stdout.strip().split('\n')
            important_configs = []
            other_configs = []
            
            important_keys = ['user.name', 'user.email', 'core.editor', 'init.defaultbranch', 'remote.origin.url']
            
            for line in config_lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    if any(important in key for important in important_keys):
                        important_configs.append(f"  {key} = {value}")
                    else:
                        other_configs.append(f"  {key} = {value}")
            
            result_text = f"Git Configuration for '{directory}':\n\n"
            
            if important_configs:
                result_text += "Key Settings:\n" + "\n".join(important_configs) + "\n\n"
            
            if other_configs:
                result_text += f"Other Settings ({len(other_configs)} total):\n" + "\n".join(other_configs[:10])
                if len(other_configs) > 10:
                    result_text += f"\n  ... and {len(other_configs) - 10} more"
            
            return result_text
            
        except subprocess.TimeoutExpired:
            return "Git config command timed out"
        except FileNotFoundError:
            return "Git is not installed or not in PATH"
        except Exception as e:
            return f"Error getting Git config: {str(e)}"

    # Port Management Tools
    @mcp.tool
    def kill_process_on_port(port: int) -> str:
        """Kill process running on a specific port"""
        try:
            killed_processes = []
            
            # Find processes using the port
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr and conn.laddr.port == port:
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            process_info = f"PID {conn.pid} ({process.name()})"
                            process.terminate()
                            
                            # Wait a bit for graceful termination
                            try:
                                process.wait(timeout=3)
                                killed_processes.append(f"Terminated: {process_info}")
                            except psutil.TimeoutExpired:
                                # Force kill if it doesn't terminate gracefully
                                process.kill()
                                killed_processes.append(f"Force killed: {process_info}")
                                
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                            killed_processes.append(f"Could not kill PID {conn.pid}: {str(e)}")
            
            if not killed_processes:
                return f"No processes found running on port {port}"
            
            return f"Port {port} cleanup results:\n" + "\n".join(killed_processes)
            
        except Exception as e:
            return f"Error killing processes on port {port}: {str(e)}"

    @mcp.tool
    def find_running_dev_servers(check_common_ports: bool = True) -> str:
        """Find running development servers"""
        try:
            # Common development ports
            dev_ports = [3000, 3001, 4200, 5000, 5173, 8000, 8080, 8888, 9000] if check_common_ports else []
            
            running_servers = []
            all_connections = psutil.net_connections(kind='inet')
            
            # Group by port for better organization
            port_processes = {}
            
            for conn in all_connections:
                if conn.laddr and conn.status == 'LISTEN':
                    port = conn.laddr.port
                    
                    # Check all listening ports or just common dev ports
                    if not check_common_ports or port in dev_ports:
                        if port not in port_processes:
                            port_processes[port] = []
                        
                        if conn.pid:
                            try:
                                process = psutil.Process(conn.pid)
                                process_name = process.name()
                                
                                # Try to get more details for common dev servers
                                try:
                                    cmdline = ' '.join(process.cmdline())
                                    # Truncate very long command lines
                                    if len(cmdline) > 100:
                                        cmdline = cmdline[:97] + "..."
                                except:
                                    cmdline = process_name
                                
                                port_processes[port].append({
                                    'pid': conn.pid,
                                    'name': process_name,
                                    'cmdline': cmdline,
                                    'address': conn.laddr.ip
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                port_processes[port].append({
                                    'pid': conn.pid,
                                    'name': 'Unknown',
                                    'cmdline': 'Access denied',
                                    'address': conn.laddr.ip
                                })
            
            if not port_processes:
                port_type = "common development" if check_common_ports else "any"
                return f"No processes found listening on {port_type} ports"
            
            result = "Running Development Servers:\n\n"
            
            for port in sorted(port_processes.keys()):
                processes = port_processes[port]
                result += f"Port {port}:\n"
                
                for proc in processes:
                    result += f"  PID {proc['pid']} - {proc['name']}\n"
                    result += f"    Address: {proc['address']}:{port}\n"
                    if proc['cmdline'] != proc['name']:
                        result += f"    Command: {proc['cmdline']}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error finding running development servers: {str(e)}"

    @mcp.tool
    def check_common_dev_ports() -> str:
        """Check status of common development ports"""
        try:
            common_ports = {
                3000: "React/Node.js dev server",
                3001: "Alternative React dev server", 
                4200: "Angular dev server",
                5000: "Flask/Express dev server",
                5173: "Vite dev server",
                8000: "Django/Python dev server",
                8080: "Tomcat/Alternative web server",
                8888: "Jupyter Notebook",
                9000: "Various dev tools"
            }
            
            result = "Common Development Ports Status:\n\n"
            
            active_connections = {}
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr and conn.status == 'LISTEN':
                    port = conn.laddr.port
                    if port in common_ports:
                        if port not in active_connections:
                            active_connections[port] = []
                        
                        process_info = "Unknown process"
                        if conn.pid:
                            try:
                                process = psutil.Process(conn.pid)
                                process_info = f"{process.name()} (PID {conn.pid})"
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                process_info = f"PID {conn.pid} (access denied)"
                        
                        active_connections[port].append({
                            'address': conn.laddr.ip,
                            'process': process_info
                        })
            
            for port in sorted(common_ports.keys()):
                description = common_ports[port]
                status = "🔴 CLOSED"
                details = ""
                
                if port in active_connections:
                    status = "🟢 OPEN"
                    details = "\n"
                    for conn in active_connections[port]:
                        details += f"    • {conn['address']}:{port} - {conn['process']}\n"
                
                result += f"Port {port:4d} ({description}): {status}{details}\n"
            
            return result
            
        except Exception as e:
            return f"Error checking development ports: {str(e)}"
