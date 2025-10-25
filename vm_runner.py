import logging
import os
import inspect
from colorama import Fore, Style, init
import subprocess
import argparse

# Initialize colorama for Windows compatibility
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.max_file_len = 0
        self.max_func_len = 0
        self.max_level_len = 0
        
        # Color mapping for log levels
        self.colors = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.MAGENTA + Style.BRIGHT
        }
    
    def format(self, record):
        level = record.levelname
        self.max_level_len = max(self.max_level_len, len(level))
        
        # Format with alignment and colors
        color = self.colors.get(level, Fore.WHITE)
        formatted = (
            f"[{color}{level:<{self.max_level_len}}{Style.RESET_ALL}] "
            f"{record.getMessage()}"
        )
        
        return formatted

def get_logger(name=None):
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with custom formatter
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logger.addHandler(handler)
    
    return logger


class VMManager:

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.vboxmanage_path = self.find_vboxmanage()
        if not self.vboxmanage_path:
            self.logger.error("VirtualBox installation not found. Please install VirtualBox.")
    
    def find_vboxmanage(self):
        """Find VBoxManage executable path"""
        try:
            # Common installation paths for VBoxManage
            common_paths = [
                r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
                r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
                "/usr/bin/VBoxManage",
                "/usr/local/bin/VBoxManage",
                "/Applications/VirtualBox.app/Contents/MacOS/VBoxManage"
            ]
            
            self.logger.debug("Searching for VBoxManage executable...")
            
            # First check the specific path you mentioned
            vbox_path = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
            self.logger.debug(f"Checking specific path: {vbox_path}")
            
            if os.path.exists(vbox_path):
                try:
                    result = subprocess.run([vbox_path, "--version"], 
                                          capture_output=True, text=True, check=True, timeout=10)
                    version = result.stdout.strip()
                    self.logger.info(f"VBoxManage found at: {vbox_path}")
                    self.logger.debug(f"VirtualBox version: {version}")
                    return vbox_path
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"VBoxManage exists but failed to run: {e}")
                except subprocess.TimeoutExpired:
                    self.logger.warning("VBoxManage command timed out")
            else:
                self.logger.warning(f"VBoxManage not found at expected path: {vbox_path}")
            
            # Try to find VBoxManage in PATH
            try:
                result = subprocess.run(["VBoxManage", "--version"], 
                                      capture_output=True, text=True, check=True, timeout=10)
                self.logger.info("VBoxManage found in system PATH")
                self.logger.debug(f"VirtualBox version: {result.stdout.strip()}")
                return "VBoxManage"
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.debug("VBoxManage not found in PATH")
            
            # Check all common installation paths
            for path in common_paths:
                self.logger.debug(f"Checking path: {path}")
                if os.path.exists(path):
                    try:
                        result = subprocess.run([path, "--version"], 
                                              capture_output=True, text=True, check=True, timeout=10)
                        self.logger.info(f"VBoxManage found at: {path}")
                        self.logger.debug(f"VirtualBox version: {result.stdout.strip()}")
                        return path
                    except subprocess.CalledProcessError as e:
                        self.logger.warning(f"VBoxManage at {path} failed to run: {e}")
                        continue
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"VBoxManage at {path} timed out")
                        continue
                else:
                    self.logger.debug(f"Path does not exist: {path}")
            
            # If not found, raise an exception
            raise FileNotFoundError("VBoxManage not found in any expected location")
            
        except Exception as e:
            self.logger.error(f"Could not locate VBoxManage: {str(e)}")
            self.logger.error("Please ensure VirtualBox is properly installed")
            return None
    
    def list_vms(self):
        """List all VirtualBox VMs"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot list VMs.")
            return []
            
        try:
            self.logger.info("Listing all VirtualBox VMs...")
            
            cmd = [self.vboxmanage_path, "list", "vms"]
            self.logger.debug(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            # Parse the output to extract VM names
            vm_names = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Extract VM name from format: "VM Name" {UUID}
                    if '"' in line:
                        vm_name = line.split('"')[1]
                        vm_names.append(vm_name)
                        self.logger.debug(f"Found VM: {vm_name}")
            
            self.logger.info(f"Found {len(vm_names)} VMs")
            return vm_names
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to list VMs: {e.stderr}")
            return []
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout listing VMs")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error listing VMs: {str(e)}")
            return []

    def start_vm(self, vm_name, headless=True):
        """Start a VirtualBox VM by name"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot start VM.")
            return False
            
        try:
            self.logger.info(f"Starting VM: {vm_name}")
            
            # Use detected VBoxManage path to start the VM
            vm_type = "headless" if headless else "gui"
            cmd = [self.vboxmanage_path, "startvm", vm_name, "--type", vm_type]
            self.logger.debug(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            
            self.logger.info(f"VM '{vm_name}' started successfully in {vm_type} mode")
            self.logger.debug(f"Command output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start VM '{vm_name}': {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout starting VM '{vm_name}'")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error starting VM '{vm_name}': {str(e)}")
            return False

    def stop_vm(self, vm_name, graceful=True):
        """Stop a VirtualBox VM by name"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot stop VM.")
            return False
        self.broadcast_message_to_vm(vm_name=vm_name,user="nhu",message="System will be shutdown")    
        try:
            self.logger.info(f"Stopping VM: {vm_name}")
            
            # Use detected VBoxManage path to stop the VM
            if graceful:
                cmd = [self.vboxmanage_path, "controlvm", vm_name, "acpipowerbutton"]
                self.logger.debug("Using graceful shutdown (ACPI power button)")
            else:
                cmd = [self.vboxmanage_path, "controlvm", vm_name, "poweroff"]
                self.logger.debug("Using force power off")
                
            self.logger.debug(f"Command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            self.logger.info(f"VM '{vm_name}' stop command sent successfully")
            self.logger.debug(f"Command output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to stop VM '{vm_name}': {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout stopping VM '{vm_name}'")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error stopping VM '{vm_name}': {str(e)}")
            return False

    def get_vm_ip(self, vm_name):
        """Get the IP address of a VirtualBox VM by name"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot get VM IP.")
            return None
            
        try:
            self.logger.info(f"Getting IP address for VM: {vm_name}")
            
            # Use detected VBoxManage path to get VM guest properties
            cmd = [self.vboxmanage_path, "guestproperty", "get", vm_name, "/VirtualBox/GuestInfo/Net/0/V4/IP"]
            self.logger.debug(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            # Parse the output to extract IP address
            output = result.stdout.strip()
            self.logger.debug(f"Command output: {output}")
            
            if "No value set!" in output:
                self.logger.warning(f"No IP address found for VM '{vm_name}'. VM might not be running or Guest Additions not installed.")
                return None
            
            # Extract IP from "Value: <ip_address>" format
            if "Value: " in output:
                ip_address = output.split("Value: ")[1].strip()
                self.logger.info(f"VM '{vm_name}' IP address: {ip_address}")
                return ip_address
            else:
                self.logger.warning(f"Could not parse IP address for VM '{vm_name}'. Output: {output}")
                return None
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get IP for VM '{vm_name}': {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout getting IP for VM '{vm_name}'")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting IP for VM '{vm_name}': {str(e)}")
            return None
    
    def get_vm_status(self, vm_name):
        """Get the status of a VirtualBox VM by name"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot get VM status.")
            return None
            
        try:
            self.logger.info(f"Getting status for VM: {vm_name}")
            
            cmd = [self.vboxmanage_path, "showvminfo", vm_name, "--machinereadable"]
            self.logger.debug(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            # Parse the output to extract VM state
            for line in result.stdout.strip().split('\n'):
                if line.startswith('VMState='):
                    state = line.split('=')[1].strip('"')
                    self.logger.info(f"VM '{vm_name}' status: {state}")
                    return state
            
            self.logger.warning(f"Could not determine status for VM '{vm_name}'")
            return None
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get status for VM '{vm_name}': {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout getting status for VM '{vm_name}'")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting status for VM '{vm_name}': {str(e)}")
            return None

    def get_vm_config(self, vm_name):
        """Get VM configuration - no longer using YAML file"""
        # Since we're not using YAML configuration anymore, return None
        return None

    def install_guest_additions(self, vm_name):
        """Install Guest Additions by mounting the ISO"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot install Guest Additions.")
            return False
            
        try:
            self.logger.info(f"Installing Guest Additions for VM: {vm_name}")
            
            # Path to Guest Additions ISO (usually in VirtualBox installation directory)
            vbox_dir = os.path.dirname(self.vboxmanage_path)
            guest_additions_iso = os.path.join(vbox_dir, "VBoxGuestAdditions.iso")
            
            if not os.path.exists(guest_additions_iso):
                self.logger.error(f"Guest Additions ISO not found at: {guest_additions_iso}")
                return False
            
            self.logger.debug(f"Guest Additions ISO found at: {guest_additions_iso}")
            
            # Get VM info to find the storage controller
            info_cmd = [self.vboxmanage_path, "showvminfo", vm_name, "--machinereadable"]
            self.logger.debug(f"Getting VM info: {' '.join(info_cmd)}")
            
            result = subprocess.run(info_cmd, capture_output=True, text=True, check=True, timeout=30)
            
            # Find the first IDE or SATA controller
            controller_name = None
            for line in result.stdout.split('\n'):
                if 'storagecontrollername' in line.lower() and ('ide' in line.lower() or 'sata' in line.lower()):
                    controller_name = line.split('=')[1].strip('"')
                    break
            
            if not controller_name:
                # Try common controller names
                controller_name = "IDE Controller"
                self.logger.debug(f"No controller found in VM info, trying default: {controller_name}")
            else:
                self.logger.debug(f"Found storage controller: {controller_name}")
            
            # Try to mount Guest Additions ISO, if it fails try port 0
            ports_to_try = ["1", "0"]
            mounted = False
            
            for port in ports_to_try:
                try:
                    cmd = [
                        self.vboxmanage_path, "storageattach", vm_name,
                        "--storagectl", controller_name,
                        "--port", port,
                        "--device", "0", 
                        "--type", "dvddrive",
                        "--medium", guest_additions_iso
                    ]
                    
                    self.logger.debug(f"Trying to mount Guest Additions on port {port}: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
                    mounted = True
                    self.logger.debug(f"Successfully mounted on port {port}")
                    break
                    
                except subprocess.CalledProcessError as e:
                    self.logger.debug(f"Failed to mount on port {port}: {e.stderr}")
                    continue
            
            if not mounted:
                self.logger.warning("Could not mount on existing ports, trying to add new CD drive...")
                
                # Try to add a new CD drive and mount
                try:
                    # Add CD drive
                    add_cmd = [
                        self.vboxmanage_path, "storageattach", vm_name,
                        "--storagectl", controller_name,
                        "--port", "1",
                        "--device", "0",
                        "--type", "dvddrive",
                        "--medium", "emptydrive"
                    ]
                    
                    self.logger.debug(f"Adding CD drive: {' '.join(add_cmd)}")
                    subprocess.run(add_cmd, capture_output=True, text=True, check=True, timeout=30)
                    
                    # Now mount the ISO
                    cmd = [
                        self.vboxmanage_path, "storageattach", vm_name,
                        "--storagectl", controller_name,
                        "--port", "1",
                        "--device", "0",
                        "--type", "dvddrive", 
                        "--medium", guest_additions_iso
                    ]
                    
                    self.logger.debug(f"Mounting Guest Additions after adding drive: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
                    mounted = True
                    
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to add CD drive and mount: {e.stderr}")
                    return False
            
            if not mounted:
                self.logger.error("Could not mount Guest Additions ISO")
                return False
            
            self.logger.info(f"Guest Additions ISO mounted successfully for VM '{vm_name}'")
            self.logger.info("Now boot the VM and install Guest Additions from the mounted CD")
            self.logger.info("Windows: Run VBoxWindowsAdditions.exe from the CD")
            self.logger.info("Linux: Run 'sudo /mnt/cdrom/VBoxLinuxAdditions.run' from the CD")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install Guest Additions for VM '{vm_name}': {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout installing Guest Additions for VM '{vm_name}'")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error installing Guest Additions for VM '{vm_name}': {str(e)}")
            return False

    def send_message_to_vm(self, vm_name, user, password, message):
        """Send a message to all terminals on the target VM"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot send message to VM.")
            return False

        try:
            self.logger.info(f"Sending message to all terminals on VM: {vm_name}")
            
            # Get VM IP address
            ip = self.get_vm_ip(vm_name)
            if not ip:
                self.logger.error(f"Could not get IP address for VM '{vm_name}'. Cannot send message.")
                return False
            
            # Use SSH to execute wall command on the target machine
            ssh_cmd = [
                "ssh", "-o", "StrictHostKeyChecking=no", 
                "-o", "UserKnownHostsFile=/dev/null",
                f"{user}@{ip}",
                f"echo '{message}' | wall"
            ]
            
            self.logger.debug(f"SSH command: {' '.join(ssh_cmd)}")
            
            # Execute the command
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30, input=password)
            
            if result.returncode == 0:
                self.logger.info(f"Message sent successfully to all terminals on VM '{vm_name}'")
                return True
            else:
                self.logger.error(f"Failed to send message: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("SSH connection timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send message to VM '{vm_name}': {str(e)}")
            return False

    def broadcast_message_to_vm(self, vm_name, user, message):
        """Send a broadcast message using VBoxManage guestcontrol (requires Guest Additions)"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot broadcast message.")
            return False

        try:
            self.logger.info(f"Broadcasting message to VM: {vm_name}")
            
            # Use VBoxManage guestcontrol to execute wall command
            cmd = [
                self.vboxmanage_path, "guestcontrol", vm_name,
                "--username", user,
                "run", "--exe", "/usr/bin/wall",
                "--", "wall", message
            ]
            
            self.logger.debug(f"VBoxManage command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info(f"Message broadcasted successfully to VM '{vm_name}'")
                return True
            else:
                self.logger.error(f"Failed to broadcast message: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("VBoxManage guestcontrol timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to broadcast message to VM '{vm_name}': {str(e)}")
            return False

    def open_terminal(self,vm_name,user):
        """Open Windows Terminal and SSH to the VM"""
        if not self.vboxmanage_path:
            self.logger.error("VBoxManage not available. Cannot get VM IP for SSH.")
            return False

        try:
            self.logger.info(f"Opening terminal to SSH into VM: {vm_name} as user: {user}")
            
            # Get VM IP address
            ip = self.get_vm_ip(vm_name)
            if not ip:
                self.logger.error(f"Could not get IP address for VM '{vm_name}'. Cannot establish SSH connection.")
                return False
            
            # Construct SSH command as separate arguments
            self.logger.debug(f"SSH target: {user}@{ip}")
            
            # Open Windows Terminal with SSH command - need to separate arguments properly
            wt_cmd = ["wt", "new-tab", "--title", f"SSH-{vm_name}", "--", "ssh", f"{user}@{ip}"]
            self.logger.debug(f"Windows Terminal command: {' '.join(wt_cmd)}")
            
            subprocess.Popen(wt_cmd, shell=False)
            self.logger.info(f"Windows Terminal opened with SSH connection to {user}@{ip}")
            return True
            
        except FileNotFoundError:
            self.logger.error("Windows Terminal (wt) not found. Please ensure Windows Terminal is installed.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to open terminal for VM '{vm_name}': {str(e)}")
            return False

    def start_vm_and_open_a_terminal(self,vm_name,user):
        if vm_name == None or user == None:
            logging.error("vm name and user both need to be provided")
        status = self.get_vm_status(vm_name=vm_name)
        logging.debug(f"got status: {status} for vm: {vm_name}")

        if status != "running":    
            self.start_vm(vm_name=vm_name,headless=True)
        else:
            logging.debug(f"VM: {vm_name} already running, skipping starting action")

        if self.get_vm_status(vm_name=vm_name) != "running":
            logging.error("Vm not running after failed starting attempt...")
            return 1
        self.open_terminal(vm_name=vm_name,user=user)
        return 0
            
            



def main():
    parser = argparse.ArgumentParser(description="VirtualBox VM Management Tool")
    parser.add_argument("action", choices=["start", "stop", "ip", "list", "guest", "terminal", "message", "svo", "status"], help="Action to perform")
    parser.add_argument("vm_name", nargs='?', help="Name of the VM (not required for 'list' action)")
    parser.add_argument("--gui", action="store_true", help="Start VM with GUI (default is headless)")
    parser.add_argument("--force", action="store_true", help="Force power off (for stop command)")
    parser.add_argument("--user", help="Username for SSH connection")
    parser.add_argument("--password", help="Password for SSH connection (for message sending)")
    parser.add_argument("--text", help="Message text to send to all terminals")
    
    args = parser.parse_args()
    
    # Create logger and VM manager first to get available VMs
    logger = get_logger()
    logger.info("VirtualBox VM Management Tool Starting...")
    
    vm_manager = VMManager()
    
    # Interactive prompts for missing arguments
    if args.action not in ["list"] and not args.vm_name:
        print(f"{Fore.CYAN}VM name is required for action '{args.action}'{Style.RESET_ALL}")
        
        # Get available VMs
        vms = vm_manager.list_vms()
        if vms:
            print(f"{Fore.YELLOW}Available VMs:{Style.RESET_ALL}")
            for i, vm in enumerate(vms, 1):
                print(f"  {i}. {vm}")
            
            while True:
                choice = input(f"{Fore.CYAN}Enter VM name or number (1-{len(vms)}): {Style.RESET_ALL}").strip()
                
                # Check if it's a number
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(vms):
                        args.vm_name = vms[idx]
                        break
                    else:
                        print(f"{Fore.RED}Invalid number. Please choose 1-{len(vms)}{Style.RESET_ALL}")
                # Check if it's a valid VM name
                elif choice in vms:
                    args.vm_name = choice
                    break
                # Check if it's empty
                elif not choice:
                    print(f"{Fore.RED}VM name cannot be empty{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}VM '{choice}' not found. Please choose from the list above{Style.RESET_ALL}")
        else:
            # No VMs available, ask for manual input
            while True:
                vm_name = input(f"{Fore.CYAN}Enter VM name: {Style.RESET_ALL}").strip()
                if vm_name:
                    args.vm_name = vm_name
                    break
                else:
                    print(f"{Fore.RED}VM name cannot be empty{Style.RESET_ALL}")
    
    # Interactive prompts for action-specific missing arguments
    if args.action in ["terminal", "svo"]:
        if not args.user:
            # Ask for required username input
            while True:
                user_input = input(f"{Fore.CYAN}Enter username: {Style.RESET_ALL}").strip()
                if user_input:
                    args.user = user_input
                    break
                else:
                    print(f"{Fore.RED}Username is required for this action{Style.RESET_ALL}")
    
    if args.action == "message":
        if not args.user:
            # Ask for required username input for message action
            while True:
                user_input = input(f"{Fore.CYAN}Enter username: {Style.RESET_ALL}").strip()
                if user_input:
                    args.user = user_input
                    break
                else:
                    print(f"{Fore.RED}Username is required for this action{Style.RESET_ALL}")
        
        if not args.text:
            message = input(f"{Fore.CYAN}Enter message to broadcast: {Style.RESET_ALL}").strip()
            if message:
                args.text = message
            else:
                print(f"{Fore.RED}Message cannot be empty{Style.RESET_ALL}")
                exit(1)
        
        # For SSH fallback, ask for password if not provided
        if not args.password:
            import getpass
            password = getpass.getpass(f"{Fore.CYAN}Enter password for SSH (optional, press Enter to skip): {Style.RESET_ALL}")
            if password:
                args.password = password
    
    # Check if VirtualBox was found
    if not vm_manager.vboxmanage_path:
        logger.critical("VirtualBox installation not found. Exiting.")
        exit(1)
    
    # Execute the requested action
    if args.action == "start":
        headless = not args.gui  # Default is headless unless --gui is specified
        success = vm_manager.start_vm(args.vm_name, headless=headless)
        if not success:
            exit(1)
    elif args.action == "stop":
        graceful = not args.force  # Default is graceful unless --force is specified
        success = vm_manager.stop_vm(args.vm_name, graceful=graceful)
        if not success:
            exit(1)
    elif args.action == "ip":
        ip = vm_manager.get_vm_ip(args.vm_name)
        if ip is None:
            exit(1)
        else:
            print(f"IP Address: {ip}")
    elif args.action == "list":
        vms = vm_manager.list_vms()
        if vms:
            print(f"\n{Fore.CYAN}Available VMs:{Style.RESET_ALL}")
            for vm in vms:
                print(f"  • {Fore.GREEN}{vm}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No VMs found{Style.RESET_ALL}")
    elif args.action == "guest":
        success = vm_manager.install_guest_additions(args.vm_name)
        if not success:
            exit(1)
        else:
            print(f"{Fore.GREEN}Guest Additions ISO mounted for VM '{args.vm_name}'{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Next steps:{Style.RESET_ALL}")
            print(f"  1. Start the VM: {Fore.CYAN}python vm_start.py start {args.vm_name} --gui{Style.RESET_ALL}")
            print(f"  2. Install Guest Additions from the mounted CD in the guest OS")
    elif args.action == "terminal":
        success = vm_manager.open_terminal(args.vm_name, args.user)
        if not success:
            exit(1)
    elif args.action == "message":
        # Message text was already validated in interactive section
        message = args.text
        
        # Try VBoxManage guestcontrol first (if Guest Additions available)
        success = vm_manager.broadcast_message_to_vm(args.vm_name, args.user, message)
        
        if not success and args.password:
            # Fall back to SSH method
            print(f"{Fore.YELLOW}Trying SSH method...{Style.RESET_ALL}")
            success = vm_manager.send_message_to_vm(args.vm_name, args.user, args.password, message)
        
        if success:
            print(f"{Fore.GREEN}Message sent successfully to all terminals on VM '{args.vm_name}'{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to send message. Try using --password option for SSH method{Style.RESET_ALL}")
            exit(1)
    elif args.action == "svo":
        success = vm_manager.start_vm_and_open_a_terminal(args.vm_name, args.user)
        if not success:
            exit(1)
    elif args.action == "status":
        status = vm_manager.get_vm_status(args.vm_name)
        if status is None:
            exit(1)        

# Example usage
if __name__ == "__main__":
    main()