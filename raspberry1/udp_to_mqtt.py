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

import os
import time
import json
import socket
import getpass
import paho.mqtt.client as mqtt

# Configuration
UDP_PORT = 8080
MQTT_BROKER = "194.177.207.38"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "team19_pi_gateway"
MQTT_TOPIC_PREFIX = "iot/team19/"
MQTT_USERNAME = "team19"
USE_TCP = False  # <-- Set this to True for TCP mode


def load_mqtt_password():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    password = None
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('MQTT_PASSWORD='):
                    password = line.strip().split('=', 1)[1]
                    break
    if not password:
        password = getpass.getpass("Enter MQTT password: ")
        with open(env_path, 'w') as f:
            f.write(f"MQTT_PASSWORD={password}\n")
    return password


def check_mqtt_password(broker, port, username, password):
    """
    Returns True if MQTT credentials are correct (can connect), False otherwise.
    """
    result = [False]
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            result[0] = True
        client.disconnect()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    try:
        client.connect(broker, port, 60)
        client.loop_start()
        time.sleep(1)
        client.loop_stop()
    except Exception:
        return False
    return result[0]


def receive_packet(sock, use_tcp):
    if use_tcp:
        conn, addr = sock.accept()
        with conn:
            data = conn.recv(1024)
        return data, addr
    else:
        data, addr = sock.recvfrom(1024)
        return data, addr


def setup_socket_and_mode():
    """
    Sets up and returns (sock, use_tcp) based on the USE_TCP variable.
    Prints listener info. Handles both TCP and UDP.
    """
    if USE_TCP:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))
        sock.listen(1)
        print(f"[INFO] TCP listener on 0.0.0.0:{UDP_PORT}, publishing to MQTT {MQTT_BROKER}:{MQTT_PORT}")
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", UDP_PORT))
        print(f"[INFO] UDP listener on 0.0.0.0:{UDP_PORT}, publishing to MQTT {MQTT_BROKER}:{MQTT_PORT}")
    return sock, USE_TCP


def main():
    password = load_mqtt_password()
    if not check_mqtt_password(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, password):
        print("Wrong MQTT password. Exiting.")
        return
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USERNAME, password)
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()  # Let paho handle reconnects in background

    sock, use_tcp = setup_socket_and_mode()

    try:
        while True:
            data, addr = receive_packet(sock, use_tcp)
            try:
                message = data.decode().strip()
                json_data = json.loads(message)
                device_id = json_data.get("id", None)
                if not device_id:
                    print(f"[WARN] No 'id' in message: {json_data}")
                    continue
                json_data["timestamp"] = int(time.time_ns())
                topic = f"{MQTT_TOPIC_PREFIX.rstrip('/')}/{device_id}"
                payload = json.dumps(json_data)
                result = client.publish(topic, payload)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"Published to {topic}: {payload}")
                else:
                    print(f"[ERROR] Failed to publish to {topic}: {payload}")
                result.wait_for_publish()
            except Exception as e:
                print(f"[ERROR] Failed to process packet: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user!")
    finally:
        client.loop_stop()
        client.disconnect()
        sock.close()

if __name__ == "__main__":
    main()
