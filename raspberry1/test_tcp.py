import socket
import os

# --- TCP Client Example ---
def tcp_client():
    host = '94.71.245.187'
    port = 65432
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        message = 'Hello, TCP server!'
        print(f'Sending: {message}')
        s.sendall(message.encode())
        data = s.recv(1024)
        print(f'Received: {data.decode()}')

# --- TCP Server Example ---
def tcp_server():
    HOST = '0.0.0.0'
    PORT = 65432
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'TCP server listening on {HOST}:{PORT}')
        conn, addr = s.accept()
        with conn:
            print(f'Connected by {addr}')
            data = conn.recv(1024)
            print(f'Received: {data.decode()}')
            # Generate random 70-byte message
            response = os.urandom(70)
            conn.sendall(response)
            print(f'Sent: {response.hex()}')

# --- UDP Client Example ---
def udp_client():
    host = '94.71.245.187'
    port = 65432
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        message = 'Hello, UDP server!'
        print(f'Sending: {message}')
        s.sendto(message.encode(), (host, port))
        data, addr = s.recvfrom(1024)
        print(f'Received from {addr}: {data.decode()}')

# --- UDP Server Example ---
def udp_server():
    HOST = '0.0.0.0'
    PORT = 65432
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        print(f'UDP server listening on {HOST}:{PORT}')
        data, addr = s.recvfrom(1024)
        print(f'Received from {addr}: {data.decode()}')
        # Generate random 70-byte message
        response = os.urandom(70)
        s.sendto(response, addr)
        print(f'Sent: {response.hex()}')

if __name__ == "__main__":
    print("Choose protocol:")
    print("1. TCP")
    print("2. UDP")
    proto_choice = input("Enter 1 for TCP, 2 for UDP: ").strip()
    if proto_choice == '1':
        print("Choose mode:")
        print("1. Run as server (wait for connection)")
        print("2. Connect to remote server")
        choice = input("Enter 1 for server, 2 for connect: ").strip()
        if choice == '1':
            tcp_server()
        elif choice == '2':
            tcp_client()
        else:
            print("Invalid choice.")
    elif proto_choice == '2':
        print("Choose mode:")
        print("1. Run as server (wait for datagram)")
        print("2. Send to remote server")
        choice = input("Enter 1 for server, 2 for client: ").strip()
        if choice == '1':
            udp_server()
        elif choice == '2':
            udp_client()
        else:
            print("Invalid choice.")
    else:
        print("Invalid protocol choice.")
