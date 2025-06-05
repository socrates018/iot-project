#!/usr/bin/env python3
"""
UDP to MQTT Gateway for ESP32 Sensor Nodes

This script acts as a gateway between multiple ESP32 sensor nodes (sending UDP packets)
and an MQTT broker. It is designed to run on a Raspberry Pi or similar Linux system.

How it works:
- The script listens for UDP packets on a specified port (default: 8080).
- Each ESP32 sensor node sends its sensor data as a JSON string via UDP. The JSON must include a unique 'id' field (e.g., last 3 bytes of MAC address) and all sensor values (e.g., temp, hum, caqi, tvoc, eco2, timestamp).
- When a UDP packet is received, the script decodes the JSON and stores the latest reading for each ESP32 node in a dictionary, keyed by 'id'.
- Every PUBLISH_INTERVAL seconds, the script publishes a single MQTT message to the topic MQTT_TOPIC (e.g., 'iot/team19'). This message is a JSON array containing the most recent reading from each ESP32 node.
- This approach ensures that the MQTT broker receives only one organized message per interval, containing all current sensor values from all nodes, reducing message flooding and making downstream processing (e.g., InfluxDB, Grafana) much easier.

Configuration is done via defines at the top of the script. You can adjust the UDP port, MQTT broker address, topic, publish interval, and other parameters as needed.

Example MQTT message payload:
[
  {"id": "AABBCC", "temp": 23.4, "hum": 56.7, ...},
  {"id": "DDEEFF", "temp": 24.1, "hum": 55.1, ...},
  ...
]

This design is scalable (works for 4 or 100+ ESPs), efficient, and easy to integrate with data pipelines.
"""

# --- Configuration Defines ---
USE_TCP = False  # Set to True to listen for TCP instead of UDP
UDP_PORT = 8080  # UDP/TCP port to listen on (must match ESP32 sender)
MQTT_BROKER = "194.177.207.38"  # MQTT broker address
MQTT_PORT = 1883  # MQTT broker port
MQTT_CLIENT_ID = "team19_pi_gateway"  # MQTT client ID for this gateway
MQTT_TOPIC_PREFIX = "iot/team19/"  # MQTT topic prefix (final topic is 'iot/team19')
MQTT_USERNAME = "team19"  # MQTT username
MQTT_RETRY_INTERVAL = 5    # Seconds between MQTT connection retry attempts
MAX_RETRY_ATTEMPTS = 3     # Maximum number of MQTT connection retry attempts
PUBLISH_INTERVAL = 2       # Seconds between MQTT publishes (batch interval)

import socket
import json
import time
import os
import threading
import queue
import paho.mqtt.client as mqtt

# ---------- Load or prompt for password ----------
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
MQTT_PASSWORD = None
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('MQTT_PASSWORD='):
                MQTT_PASSWORD = line.strip().split('=', 1)[1]
                break
if not MQTT_PASSWORD:
    import getpass
    MQTT_PASSWORD = getpass.getpass("Enter MQTT password: ")
    with open(ENV_PATH, 'w') as f:
        f.write(f"MQTT_PASSWORD={MQTT_PASSWORD}\n")

print("[DEBUG] Current working directory:", os.getcwd())
print("[DEBUG] ENV_PATH:", ENV_PATH)
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        print("[DEBUG] .env contents:", f.read())
else:
    print("[DEBUG] .env file NOT FOUND at:", ENV_PATH)

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

# Set up MQTT client
def setup_mqtt():
    try:
        from paho.mqtt.client import MQTTv5, CallbackAPIVersion
        client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    except (ImportError, ValueError, AttributeError):
        try:
            client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        except TypeError:
            client = mqtt.Client()
            client._client_id = MQTT_CLIENT_ID
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            client.connect(MQTT_BROKER, MQTT_PORT)
            client.loop_start()
            print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            return client
        except Exception as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS}: Failed to connect to MQTT broker: {e}")
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                print(f"Retrying in {MQTT_RETRY_INTERVAL} seconds...")
                time.sleep(MQTT_RETRY_INTERVAL)
            else:
                print("Running in console-only mode (no MQTT)")
                return None

# Store latest reading from each ESP by id
latest_readings = {}

# Thread-safe queue for incoming UDP packets
udp_queue = queue.Queue()

# Worker thread for publishing to MQTT
class MQTTPublishWorker(threading.Thread):
    def __init__(self, mqtt_client, udp_queue):
        super().__init__(daemon=True)
        self.mqtt_client = mqtt_client
        self.udp_queue = udp_queue

    def run(self):
        while True:
            device_id, reading = self.udp_queue.get()
            if self.mqtt_client:
                topic = f"{MQTT_TOPIC_PREFIX.rstrip('/')}/{device_id}"
                payload = json.dumps(reading)
                self.mqtt_client.publish(topic, payload)
                print(f"Published to {topic}: {payload}")
            self.udp_queue.task_done()

# UDP receive loop (threaded)
def udp_receive_loop(sock, udp_queue):
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"[DEBUG] UDP packet received from {addr}: {data!r}")
        try:
            message = data.decode().strip()
            json_data = json.loads(message)
            device_id = json_data.get("id", None)
            if device_id:
                # Set timestamp to current unix time in nanoseconds
                json_data["timestamp"] = int(time.time_ns())
                latest_readings[device_id] = json_data
                print(f"Updated reading for {device_id}: {json_data}")
                udp_queue.put((device_id, json_data))
            else:
                print(f"No 'id' in message: {json_data}")
        except json.JSONDecodeError:
            print(f"Non-JSON message from {addr}: {message}")
        except Exception as e:
            print(f"Error processing message: {e}")

# TCP receive loop (threaded, similar to UDP)
def tcp_receive_loop(sock, udp_queue):
    while True:
        conn, addr = sock.accept()
        with conn:
            data = conn.recv(1024)
            print(f"[DEBUG] TCP packet received from {addr}: {data!r}")
            try:
                message = data.decode().strip()
                json_data = json.loads(message)
                device_id = json_data.get("id", None)
                if device_id:
                    json_data["timestamp"] = int(time.time_ns())
                    latest_readings[device_id] = json_data
                    print(f"Updated reading for {device_id}: {json_data}")
                    udp_queue.put((device_id, json_data))
                else:
                    print(f"No 'id' in message: {json_data}")
            except json.JSONDecodeError:
                print(f"Non-JSON message from {addr}: {message}")
            except Exception as e:
                print(f"Error processing message: {e}")

def check_mqtt_password(broker, port, username, password):
    """
    Returns True if MQTT credentials are correct (can connect), False otherwise.
    """
    result = [False]
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            result[0] = True
        client.disconnect()
    # Use the modern Callback API version to avoid deprecation warning
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    try:
        client.connect(broker, port, 60)
        client.loop_start()
        import time
        time.sleep(1)  # Wait for connect callback
        client.loop_stop()
    except Exception:
        return False
    return result[0]

def main():
    global mqtt_client
    # Check MQTT password before starting anything else
    if not check_mqtt_password(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD):
        print("Wrong MQTT password. Exiting.")
        return

    # Initialize socket and print info before anything else
    UDP_IP = get_local_ip()  # Automatically detect local WiFi IP
    proto = "TCP" if USE_TCP else "UDP"
    print(f"[INFO] {proto} listener starting on {UDP_IP}:{UDP_PORT}...")
    if USE_TCP:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((UDP_IP, UDP_PORT))
        sock.listen(5)
        print(f"[INFO] TCP socket bound. Waiting for connections...")
        # Start MQTT client in background
        mqtt_client = setup_mqtt()
        # Start MQTT publish worker thread
        mqtt_worker = MQTTPublishWorker(mqtt_client, udp_queue)
        mqtt_worker.start()
        # Start TCP receive loop in main thread (blocking)
        tcp_receive_loop(sock, udp_queue)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        print(f"[INFO] UDP socket bound. Waiting for packets...")
        # Start MQTT client in background
        mqtt_client = setup_mqtt()
        # Start MQTT publish worker thread
        mqtt_worker = MQTTPublishWorker(mqtt_client, udp_queue)
        mqtt_worker.start()
        # Start UDP receive loop in main thread (blocking)
        udp_receive_loop(sock, udp_queue)

if __name__ == "__main__":
    main()
