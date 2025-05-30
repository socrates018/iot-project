# Configuration
UDP_IP = "192.168.1.9"      # Destination IP
UDP_PORT = 8080              # Destination port
UDP_SOURCE_PORT = 0       # Source port (0 lets OS choose)
SEND_INTERVAL = 1            # Seconds between sends

import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_SOURCE_PORT))

try:
    while True:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        message = current_time.encode('utf-8')
        sock.sendto(message, (UDP_IP, UDP_PORT))
        print(f"Sent UDP packet with time '{current_time}' to {UDP_IP}:{UDP_PORT} (source port {sock.getsockname()[1]})")
        time.sleep(SEND_INTERVAL)
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    sock.close()
