#!/usr/bin/env python3
import os
import sys
import subprocess
import miniupnpc
import logging
import time
from pathlib import Path
import urllib.request

# Configuration
PORT_PROTOCOLS = [(8080, 'TCP'), (80, 'TCP'), (53, 'UDP')]
DDNS_CONFIG = {
    'enabled': True,
    'apikey': 'your_api_key',
    'hostname': 'yourhost.dynu.com',
    'interval': 600
}
INTERVAL = 1800
SERVICE_NAME = "auto_upnp_ddns_service"
SCRIPT_PATH = Path(__file__).resolve()
VENV_DIR = SCRIPT_PATH.parent / "upnp_venv"
LOG_FILE = "/var/log/auto_upnp_service.log"

def check_root():
    if os.geteuid() != 0:
        print("❌ Please run with sudo!")
        sys.exit(1)

def install_dependencies():
    print("🔧 Setting up virtual environment and dependencies...")
    try:
        # Install required system packages
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "python3-venv"], check=True)
        
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
        
        # Install packages in venv
        subprocess.run([
            VENV_DIR / "bin" / "pip",
            "install",
            "miniupnpc"
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        sys.exit(1)

def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    logging.info("=== Starting Auto UPnP/DDNS Service Setup ===")

def create_service_file():
    service_content = f"""\
[Unit]
Description=Auto UPnP Port Forwarding + Dynu DDNS
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={VENV_DIR}/bin/python {SCRIPT_PATH}
Restart=always
RestartSec=60
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
"""

    service_path = f"/etc/systemd/system/{SERVICE_NAME}.service"
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        print(f"📝 Created service file at {service_path}")
    except Exception as e:
        logging.error(f"Service file creation failed: {e}")
        print("❌ Failed to create service file!")
        sys.exit(1)

# ... [rest of the functions remain unchanged from previous version] ...


def enable_service():
    try:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)
        subprocess.run(["systemctl", "start", SERVICE_NAME], check=True)
        print(f"🚀 Service {SERVICE_NAME} installed and started!")
    except subprocess.CalledProcessError as e:
        logging.error(f"Service activation failed: {e}")
        print("❌ Failed to enable/start service!")
        sys.exit(1)

def setup_upnp():
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    try:
        upnp.discover()
        upnp.selectigd()
        return upnp
    except Exception as e:
        logging.error(f"UPnP setup failed: {e}")
        return None

def forward_ports(upnp):
    if not upnp:
        return False
    
    success = True
    for port, protocol in PORT_PROTOCOLS:
        try:
            upnp.addportmapping(
                port, protocol, upnp.lanaddr, port,
                'Auto-UPnP-Service', '', 3600  # Set lifetime to 1 hour (3600 seconds)
            )
            logging.info(f"Forwarded {port}/{protocol}")
        except Exception as e:
            logging.error(f"Port {port}/{protocol} error: {e}")
            success = False
    return success

def update_ddns():
    if not DDNS_CONFIG['enabled']:
        return True

    try:
        # Get current IP address
        with urllib.request.urlopen('https://api.ipify.org') as response:
            current_ip = response.read().decode('utf-8').strip()

        # Update Dynu DNS
        update_url = (
            f"https://api.dynu.com/nic/update?"
            f"hostname={DDNS_CONFIG['hostname']}&"
            f"myip={current_ip}&"
            f"username={DDNS_CONFIG['apikey']}"
        )
        
        with urllib.request.urlopen(update_url) as response:
            result = response.read().decode('utf-8').strip()
        
        logging.info(f"Dynu DDNS update: {result}")
        return "good" in result.lower() or "nochg" in result.lower()
    except Exception as e:
        logging.error(f"Dynu DDNS update failed: {e}")
        return False

def service_loop():
    logging.info("Starting service loop")
    print("🔌 Service running in background. Ctrl+C to exit.")
    
    last_port_update = 0
    last_ddns_update = 0
    
    while True:
        current_time = time.time()
        
        # Update ports if interval has passed
        if current_time - last_port_update >= INTERVAL:
            upnp = setup_upnp()
            if upnp:
                if forward_ports(upnp):
                    logging.info("Port renewal successful")
                else:
                    logging.warning("Partial port renewal failure")
            else:
                logging.error("UPnP gateway not found")
            last_port_update = current_time
        
        # Update DDNS if enabled and interval has passed
        if DDNS_CONFIG['enabled'] and (current_time - last_ddns_update >= DDNS_CONFIG['interval']):
            if update_ddns():
                logging.info("DDNS update successful")
            else:
                logging.warning("DDNS update failed")
            last_ddns_update = current_time
        
        time.sleep(60)  # Check every minute


def main():
    check_root()
    print("🛠 Starting automated UPnP + Dynu DDNS setup...")
    
    # Initial setup phase
    if not Path(f"/etc/systemd/system/{SERVICE_NAME}.service").exists():
        setup_logging()
        install_dependencies()
        create_service_file()
        enable_service()
    
    # Continuous service phase
    try:
        service_loop()
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
