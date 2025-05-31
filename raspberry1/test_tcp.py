import socket

# --- TCP Client Example ---
def tcp_client():
    host = input("Enter remote server IP to connect to: ").strip()
    port = int(input("Enter remote server port to connect to: ").strip())
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
            response = 'Hello, TCP client!'
            conn.sendall(response.encode())
            print(f'Sent: {response}')

if __name__ == "__main__":
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
