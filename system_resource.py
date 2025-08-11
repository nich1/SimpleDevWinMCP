import os
import json
import shutil
import subprocess
import platform
import psutil
import pkg_resources
import winreg
from fastmcp import FastMCP

def _format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def register_system_resource_tools(mcp: FastMCP):
    """Register all system resource monitoring related tools"""
    
    @mcp.tool
    def get_environment_variables() -> str:
        """List environment variables (or get specific one)"""
        try:
            env_vars = dict(os.environ)
            result = "Environment Variables:\n"
            for key, value in sorted(env_vars.items()):
                # Truncate very long values for readability
                display_value = value if len(value) <= 100 else value[:97] + "..."
                result += f"{key}={display_value}\n"
            return result
        except Exception as e:
            return f"Error getting environment variables: {str(e)}"

    @mcp.tool
    def get_installed_python_packages() -> str:
        """List installed Python packages"""
        try:
            packages = []
            for package in pkg_resources.working_set:
                packages.append(f"{package.project_name}=={package.version}")
            
            if not packages:
                return "No packages found"
            
            packages.sort()
            return f"Installed Python packages ({len(packages)} total):\n" + "\n".join(packages)
        except Exception as e:
            return f"Error getting installed packages: {str(e)}"

    @mcp.tool
    def check_command_exists(command: str) -> str:
        """Check if a command/program is available in PATH"""
        try:
            result = shutil.which(command)
            if result:
                return f"Command '{command}' is available at: {result}"
            else:
                return f"Command '{command}' is not available in PATH"
        except Exception as e:
            return f"Error checking command: {str(e)}"

    @mcp.tool
    def get_system_resources() -> str:
        """Get overall CPU, memory, and disk usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            result = f"System Resources:\n\n"
            result += f"CPU:\n"
            result += f"  Usage: {cpu_percent}%\n"
            result += f"  Cores: {cpu_count}\n"
            if cpu_freq:
                result += f"  Frequency: {cpu_freq.current:.0f} MHz\n"
            
            result += f"\nMemory:\n"
            result += f"  Total: {_format_size(memory.total)}\n"
            result += f"  Available: {_format_size(memory.available)}\n"
            result += f"  Used: {_format_size(memory.used)} ({memory.percent}%)\n"
            
            result += f"\nSwap:\n"
            result += f"  Total: {_format_size(swap.total)}\n"
            result += f"  Used: {_format_size(swap.used)} ({swap.percent}%)\n"
            
            result += f"\nDisk (/):\n"
            result += f"  Total: {_format_size(disk.total)}\n"
            result += f"  Used: {_format_size(disk.used)} ({disk.used/disk.total*100:.1f}%)\n"
            result += f"  Free: {_format_size(disk.free)}\n"
            
            return result
        except Exception as e:
            return f"Error getting system resources: {str(e)}"

    @mcp.tool
    def get_battery_status() -> str:
        """Get battery status information"""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "No battery found on this system"
            
            result = "Battery Status:\n"
            result += f"  Charge: {battery.percent:.1f}%\n"
            result += f"  Power plugged: {'Yes' if battery.power_plugged else 'No'}\n"
            
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                if battery.secsleft != psutil.POWER_TIME_UNKNOWN:
                    hours, remainder = divmod(battery.secsleft, 3600)
                    minutes, _ = divmod(remainder, 60)
                    if battery.power_plugged:
                        result += f"  Time until charged: {hours:02d}:{minutes:02d}\n"
                    else:
                        result += f"  Time remaining: {hours:02d}:{minutes:02d}\n"
                else:
                    result += f"  Time remaining: Unknown\n"
            else:
                result += f"  Time remaining: Unlimited (plugged in)\n"
            
            return result
        except Exception as e:
            return f"Error getting battery status: {str(e)}"

    @mcp.tool
    def get_windows_version() -> str:
        """Get Windows version and build number"""
        try:
            if platform.system().lower() != "windows":
                return "This function is only available on Windows systems"
            
            # Get Windows version info
            version_info = platform.version()
            release = platform.release()
            
            result = f"Windows Version Information:\n"
            result += f"  Release: {release}\n"
            result += f"  Version: {version_info}\n"
            result += f"  Platform: {platform.platform()}\n"
            
            # Try to get more detailed build info from registry
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                    product_name = winreg.QueryValueEx(key, "ProductName")[0]
                    current_build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                    display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
                    
                    result += f"  Product Name: {product_name}\n"
                    result += f"  Build Number: {current_build}\n"
                    result += f"  Display Version: {display_version}\n"
            except Exception:
                pass  # Registry access might fail, continue with basic info
            
            return result
        except Exception as e:
            return f"Error getting Windows version: {str(e)}"

    @mcp.tool
    def get_hardware_information() -> str:
        """Get hardware information"""
        try:
            result = "Hardware Information:\n\n"
            
            # CPU Information
            result += "CPU:\n"
            result += f"  Processor: {platform.processor()}\n"
            result += f"  Architecture: {platform.machine()}\n"
            result += f"  Physical cores: {psutil.cpu_count(logical=False)}\n"
            result += f"  Total cores: {psutil.cpu_count(logical=True)}\n"
            
            # CPU frequencies
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                result += f"  Current frequency: {cpu_freq.current:.2f} MHz\n"
                result += f"  Min frequency: {cpu_freq.min:.2f} MHz\n"
                result += f"  Max frequency: {cpu_freq.max:.2f} MHz\n"
            
            # Memory Information
            memory = psutil.virtual_memory()
            result += f"\nMemory:\n"
            result += f"  Total: {_format_size(memory.total)}\n"
            result += f"  Available: {_format_size(memory.available)}\n"
            
            # Disk Information
            result += f"\nDisk Drives:\n"
            for partition in psutil.disk_partitions():
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    result += f"  {partition.device}\n"
                    result += f"    Mountpoint: {partition.mountpoint}\n"
                    result += f"    File system: {partition.fstype}\n"
                    result += f"    Total Size: {_format_size(partition_usage.total)}\n"
                    result += f"    Used: {_format_size(partition_usage.used)}\n"
                    result += f"    Free: {_format_size(partition_usage.free)}\n"
                except PermissionError:
                    result += f"  {partition.device}: Permission denied\n"
            
            # Network interfaces
            result += f"\nNetwork Interfaces:\n"
            net_if_stats = psutil.net_if_stats()
            for interface, stats in net_if_stats.items():
                result += f"  {interface}:\n"
                result += f"    Up: {'Yes' if stats.isup else 'No'}\n"
                result += f"    Speed: {stats.speed} Mbps\n"
                result += f"    MTU: {stats.mtu}\n"
            
            return result
        except Exception as e:
            return f"Error getting hardware information: {str(e)}"

    @mcp.tool
    def list_installed_applications() -> str:
        """List installed applications (Windows only)"""
        try:
            if platform.system().lower() != "windows":
                return "This function is currently only available on Windows systems"
            
            apps = []
            
            # Check both 32-bit and 64-bit registry locations
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, subkey_path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, subkey_path) as key:
                        for i in range(0, winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        try:
                                            display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                        except FileNotFoundError:
                                            display_version = "Unknown"
                                        try:
                                            publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                                        except FileNotFoundError:
                                            publisher = "Unknown"
                                        
                                        apps.append({
                                            "name": display_name,
                                            "version": display_version,
                                            "publisher": publisher
                                        })
                                    except FileNotFoundError:
                                        # Skip entries without DisplayName
                                        continue
                            except OSError:
                                # Skip inaccessible entries
                                continue
                except FileNotFoundError:
                    # Registry key doesn't exist
                    continue
            
            # Remove duplicates based on name and version
            unique_apps = []
            seen = set()
            for app in apps:
                key = (app["name"], app["version"])
                if key not in seen:
                    seen.add(key)
                    unique_apps.append(app)
            
            # Sort by name
            unique_apps.sort(key=lambda x: x["name"].lower())
            
            result = f"Installed Applications ({len(unique_apps)} found):\n\n"
            for app in unique_apps:
                result += f"Name: {app['name']}\n"
                result += f"  Version: {app['version']}\n"
                result += f"  Publisher: {app['publisher']}\n\n"
            
            return result
        except Exception as e:
            return f"Error listing installed applications: {str(e)}"

    @mcp.tool
    def get_temperature_information() -> str:
        """Get temperature information from system sensors"""
        try:
            temperatures = psutil.sensors_temperatures()
            
            if not temperatures:
                return "No temperature sensors found on this system"
            
            result = "Temperature Information:\n\n"
            
            for name, entries in temperatures.items():
                result += f"{name}:\n"
                for entry in entries:
                    result += f"  {entry.label or 'Unknown'}: {entry.current}°C"
                    if entry.high:
                        result += f" (High: {entry.high}°C)"
                    if entry.critical:
                        result += f" (Critical: {entry.critical}°C)"
                    result += "\n"
                result += "\n"
            
            return result
        except Exception as e:
            return f"Error getting temperature information: {str(e)}"
