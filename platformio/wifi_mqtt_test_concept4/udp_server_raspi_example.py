#!/usr/bin/env python3
"""
UDP Server Example for Concept 4

Listens for UDP packets from ESP32 sensor nodes and prints the received data.
Designed to run on a Raspberry Pi (or any Linux system with Python 3).

Usage:
    python3 udp_server_raspi_example.py

Make sure your firewall allows UDP traffic on the specified port.
"""
import socket

# Helper function to get the local WiFi IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

UDP_IP = get_local_ip()  # Automatically detect local WiFi IP
UDP_PORT = 8080      # Must match the ESP32 sender

print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

try:
    while True:
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        print(f"Received from {addr}: {data.decode().strip()}")
except KeyboardInterrupt:
    print("\nServer stopped by user.")
finally:
    sock.close()
