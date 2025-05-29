import socket
import time

UDP_IP = "192.168.1.9"
UDP_PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    message = current_time.encode('utf-8')
    sock.sendto(message, (UDP_IP, UDP_PORT))
    print(f"Sent UDP packet with time '{current_time}' to {UDP_IP}:{UDP_PORT}")
    time.sleep(1)  # send every second
