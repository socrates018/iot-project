#!/usr/bin/env python3
import subprocess
import sys
import os

def check_sudo():
    """Ensure script runs with sudo."""
    if os.geteuid() != 0:
        print("Error: This script must be run with sudo.")
        sys.exit(1)

def check_nmcli():
    """Check if nmcli is available."""
    try:
        subprocess.run(["nmcli", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError:
        print("Error: nmcli (NetworkManager) is not installed.")
        print("Install it with: sudo apt install network-manager")
        sys.exit(1)

def list_networks():
    """List all saved Wi-Fi connections."""
    try:
        result = subprocess.run(["nmcli", "connection", "show"], capture_output=True, text=True, check=True)
        print("Saved Wi-Fi Networks:")
        print("---------------------")
        connections = [line.split()[0] for line in result.stdout.split('\n') if "wifi" in line]
        if not connections:
            print("No saved Wi-Fi networks.")
        else:
            for conn in connections:
                print(conn)
    except subprocess.CalledProcessError as e:
        print(f"Failed to list networks: {e.stderr}")

def add_network(ssid, password):
    """Add a new Wi-Fi network using nmcli."""
    try:
        subprocess.run(
            ["nmcli", "device", "wifi", "connect", ssid, "password", password],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully added and connected to: {ssid}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to add network: {e.stderr}")

def delete_network(ssid):
    """Delete a saved Wi-Fi connection."""
    try:
        subprocess.run(
            ["nmcli", "connection", "delete", ssid],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully deleted: {ssid}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete network: {e.stderr}")

def main():
    check_sudo()
    check_nmcli()  # Ensure NetworkManager is installed
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} list                     - List saved networks")
        print(f"  {sys.argv[0]} add <SSID> <PASSWORD>    - Add a new network")
        print(f"  {sys.argv[0]} delete <SSID>            - Delete a network")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_networks()
    elif command == "add":
        if len(sys.argv) != 4:
            print("Usage: sudo python3 nmcli_wifi_manager.py add <SSID> <PASSWORD>")
            sys.exit(1)
        ssid, password = sys.argv[2], sys.argv[3]
        add_network(ssid, password)
    elif command == "delete":
        if len(sys.argv) != 3:
            print("Usage: sudo python3 nmcli_wifi_manager.py delete <SSID>")
            sys.exit(1)
        ssid = sys.argv[2]
        delete_network(ssid)
    else:
        print("Invalid command. Use 'list', 'add', or 'delete'.")

if __name__ == "__main__":
    main()