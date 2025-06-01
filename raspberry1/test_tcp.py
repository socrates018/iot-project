import socket
import os

def get_port_for_local_ip():
    # Prompt user for port only; always bind to 0.0.0.0 for server
    port = int(input("Enter port to bind: ").strip())
    local_ip = '0.0.0.0'
    print(f"[DEBUG] Using local IP {local_ip}, port {port}")
    return port, local_ip

# --- TCP Client Example ---
def tcp_client():
    # Prompt user for server IP and port
    host = input("Enter server IP to connect to: ").strip()
    port = int(input("Enter server port to connect to: ").strip())
    print(f"[DEBUG] Connecting to TCP server at {host}:{port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print(f"[DEBUG] Connected to TCP server at {host}:{port}")
        message = os.urandom(70)  # 70 bytes
        print(f'Sending 70 bytes of data')
        s.sendall(message)
        print('Data sent.')

# --- TCP Server Example ---
def tcp_server():
    PORT, HOST = get_port_for_local_ip()
    print(f"[DEBUG] TCP server using local IP {HOST}, port {PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'TCP server listening on {HOST}:{PORT}')
        conn, addr = s.accept()
        print(f"[DEBUG] Client connected from {addr}")
        with conn:
            print(f'Connected by {addr}')
            received = 0
            chunks = []
            to_receive = 70  # 70 bytes
            while received < to_receive:
                chunk = conn.recv(min(4096, to_receive - received))
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
            print(f'Received {received} bytes from client')
            # Optionally, you can send a small acknowledgment if you want
            # conn.sendall(b'OK')
            # print('Sent acknowledgment to client')

# --- UDP Client Example ---
def udp_client():
    # Prompt user for server IP and port
    host = input("Enter server IP to send to: ").strip()
    port = int(input("Enter server port to send to: ").strip())
    print(f"[DEBUG] Sending to UDP server at {host}:{port}")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        message = os.urandom(10 * 1024 * 1024)  # 10MB
        print(f'Sending 10MB of data in UDP packets')
        # UDP has a max packet size, so send in chunks
        chunk_size = 1400
        for i in range(0, len(message), chunk_size):
            s.sendto(message[i:i+chunk_size], (host, port))
        print(f"[DEBUG] Sent 10MB to UDP server at {host}:{port}")
        data, addr = s.recvfrom(1024)
        print(f'Received from {addr}: {data.decode(errors="replace")}')

# --- UDP Server Example ---
def udp_server():
    PORT, HOST = get_port_for_local_ip()
    print(f"[DEBUG] UDP server using local IP {HOST}, port {PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        print(f'UDP server listening on {HOST}:{PORT}')
        received = 0
        chunks = []
        to_receive = 10 * 1024 * 1024  # 10MB
        addr = None
        while received < to_receive:
            chunk, addr = s.recvfrom(4096)
            if not chunk:
                break
            chunks.append(chunk)
            received += len(chunk)
        print(f"[DEBUG] Datagram received from {addr}")
        print(f'Received {received} bytes from {addr}')
        # Generate random 10MB message
        response = os.urandom(10 * 1024 * 1024)
        # Send in chunks
        chunk_size = 1400
        for i in range(0, len(response), chunk_size):
            s.sendto(response[i:i+chunk_size], addr)
        print(f'Sent 10MB of data')

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
