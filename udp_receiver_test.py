import socket

UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for UDP packets on port {UDP_PORT}...")

try:
    while True:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        print(f"Received message from {addr}: {data.decode('utf-8')}")
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    sock.close()
