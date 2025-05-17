#!/usr/bin/env python3
import subprocess
import os
import sys
from shutil import copy2

WPA_SUPPLICANT_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"
BACKUP_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf.bak"

def check_sudo():
    """Ensure script runs with sudo."""
    if os.geteuid() != 0:
        print("Error: This script must be run with sudo.")
        sys.exit(1)

def backup_config():
    """Backup the original config file."""
    try:
        copy2(WPA_SUPPLICANT_CONF, BACKUP_CONF)
        print(f"Backup created at {BACKUP_CONF}")
    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)

def list_networks():
    """List all saved Wi-Fi networks."""
    try:
        with open(WPA_SUPPLICANT_CONF, 'r') as f:
            content = f.read()
            print("Saved Wi-Fi Networks:")
            print("---------------------")
            if "network=" not in content:
                print("No networks configured.")
            else:
                print(content.split("network=")[1:])
    except FileNotFoundError:
        print(f"Error: {WPA_SUPPLICANT_CONF} not found.")
        sys.exit(1)

def add_network(ssid, password):
    """Add a new Wi-Fi network."""
    backup_config()
    network_config = f'\nnetwork={{\n    ssid="{ssid}"\n    psk="{password}"\n}}\n'

    try:
        with open(WPA_SUPPLICANT_CONF, 'a') as f:
            f.write(network_config)
        print(f"Successfully added network: {ssid}")
        restart_wifi()
    except Exception as e:
        print(f"Failed to add network: {e}")
        restore_backup()

def delete_network(ssid):
    """Delete a Wi-Fi network by SSID."""
    backup_config()
    try:
        with open(WPA_SUPPLICANT_CONF, 'r') as f:
            lines = f.readlines()

        new_lines = []
        skip = False
        for line in lines:
            if f'ssid="{ssid}"' in line:
                skip = True
            elif skip and "}" in line:
                skip = False
                continue
            if not skip:
                new_lines.append(line)

        with open(WPA_SUPPLICANT_CONF, 'w') as f:
            f.writelines(new_lines)

        print(f"Successfully deleted network: {ssid}")
        restart_wifi()
    except Exception as e:
        print(f"Failed to delete network: {e}")
        restore_backup()

def restart_wifi():
    """Restart Wi-Fi to apply changes."""
    try:
        subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"], check=True)
        print("Wi-Fi reconfigured successfully.")
    except subprocess.CalledProcessError:
        print("Failed to restart Wi-Fi. Try rebooting.")

def restore_backup():
    """Restore from backup if something goes wrong."""
    try:
        copy2(BACKUP_CONF, WPA_SUPPLICANT_CONF)
        print("Restored original config from backup.")
    except Exception as e:
        print(f"Restore failed: {e}")

def main():
    check_sudo()
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} list                           - List saved networks")
        print(f"  {sys.argv[0]} add <SSID> <PASSWORD>          - Add a new network")
        print(f"  {sys.argv[0]} delete <SSID>                  - Delete a network")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_networks()
    elif command == "add":
        if len(sys.argv) != 4:
            print("Usage: sudo python3 wifi_manager.py add <SSID> <PASSWORD>")
            sys.exit(1)
        ssid, password = sys.argv[2], sys.argv[3]
        add_network(ssid, password)
    elif command == "delete":
        if len(sys.argv) != 3:
            print("Usage: sudo python3 wifi_manager.py delete <SSID>")
            sys.exit(1)
        ssid = sys.argv[2]
        delete_network(ssid)
    else:
        print("Invalid command. Use 'list', 'add', or 'delete'.")

if __name__ == "__main__":
    main()