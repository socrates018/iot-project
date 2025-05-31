import socket
import os

def get_port_for_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    if local_ip == '192.168.1.3':
        port = 3030
    elif local_ip == '192.168.1.9':
        port = 65432
    elif local_ip == '192.168.1.6':
        port = 65431
    else:
        print(f"[DEBUG] Unknown IP {local_ip}, using default port 65432")
        port = 65432
    print(f"[DEBUG] Detected local IP {local_ip}, using port {port}")
    return port, local_ip

# --- TCP Client Example ---
def tcp_client():
    # Prompt user for server selection
    print("Choose server to connect to:")
    print("1. giannis")
    print("2. aggelos")
    print("3. pi2")
    server_choice = input("Enter 1 for giannis, 2 for aggelos, 3 for pi2: ").strip()
    host = '94.71.245.187'
    if server_choice == '1':
        port = 3030
    elif server_choice == '2':
        port = 65431
    elif server_choice == '3':
        port = 65432
    else:
        print("Invalid choice.")
        return
    print(f"[DEBUG] Connecting to TCP server at {host}:{port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print(f"[DEBUG] Connected to TCP server at {host}:{port}")
        message = os.urandom(10 * 1024 * 1024)  # 10MB
        print(f'Sending 10MB of data')
        s.sendall(message)
        data = s.recv(1024)
        print(f'Received: {data.decode(errors="replace")}')

# --- TCP Server Example ---
def tcp_server():
    PORT, local_ip = get_port_for_local_ip()
    HOST = '0.0.0.0'
    print(f"[DEBUG] TCP server detected local IP {local_ip}, using port {PORT}")
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
            to_receive = 10 * 1024 * 1024  # 10MB
            while received < to_receive:
                chunk = conn.recv(min(4096, to_receive - received))
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
            print(f'Received {received} bytes from client')
            # Generate random 10MB message
            response = os.urandom(10 * 1024 * 1024)
            conn.sendall(response)
            print(f'Sent 10MB of data')

# --- UDP Client Example ---
def udp_client():
    # Prompt user for server selection
    print("Choose server to connect to:")
    print("1. giannis")
    print("2. aggelos")
    print("3. pi2")
    server_choice = input("Enter 1 for giannis, 2 for aggelos, 3 for pi2: ").strip()
    host = '94.71.245.187'
    if server_choice == '1':
        port = 3030
    elif server_choice == '2':
        port = 65431
    elif server_choice == '3':
        port = 65432
    else:
        print("Invalid choice.")
        return
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
    PORT, local_ip = get_port_for_local_ip()
    HOST = '0.0.0.0'
    print(f"[DEBUG] UDP server detected local IP {local_ip}, using port {PORT}")
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
