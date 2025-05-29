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
UDP_PORT = 8080  # UDP port to listen on (must match ESP32 sender)
MQTT_BROKER = "194.177.207.38"  # MQTT broker address
MQTT_PORT = 1883  # MQTT broker port
MQTT_CLIENT_ID = "raspberry_pi_udp_gateway"  # MQTT client ID for this gateway
MQTT_TOPIC_PREFIX = "iot/team19/"  # MQTT topic prefix (final topic is 'iot/team19')
MQTT_USERNAME = "team19"  # MQTT username
MQTT_RETRY_INTERVAL = 5    # Seconds between MQTT connection retry attempts
MAX_RETRY_ATTEMPTS = 3     # Maximum number of MQTT connection retry attempts
PUBLISH_INTERVAL = 2       # Seconds between MQTT publishes (batch interval)

import socket
import json
import paho.mqtt.client as mqtt
import time
import getpass
import threading

MQTT_PASSWORD = getpass.getpass("Enter MQTT password: ")

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
        from paho.mqtt.client import MQTTv5
        client = mqtt.Client(mqtt.MQTTv5, client_id=MQTT_CLIENT_ID)
    except (ImportError, ValueError):
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

# Process message and store latest reading per ESP
# Note: We remove the 'timestamp' field before storing/publishing, as timestamps will be added automatically by the database (InfluxDB)
def process_message(mqtt_client, data, addr):
    try:
        message = data.decode().strip()
        try:
            json_data = json.loads(message)
            device_id = json_data.get("id", None)
            if device_id:
                # Add/replace 'timestamp' with current unix time
                json_data["timestamp"] = int(time.time())
                latest_readings[device_id] = json_data
                print(f"Updated reading for {device_id}: {json_data}")
            else:
                print(f"No 'id' in message: {json_data}")
        except json.JSONDecodeError:
            print(f"Non-JSON message from {addr}: {message}")
    except Exception as e:
        print(f"Error processing message: {e}")

# Periodically publish all latest readings in one MQTT message
PUBLISH_INTERVAL = 2  # seconds

def publish_all_readings():
    topic = MQTT_TOPIC_PREFIX.rstrip('/')
    while True:
        if mqtt_client and latest_readings:
            # Compose a list of the latest readings from all ESPs
            payload = json.dumps(list(latest_readings.values()))
            mqtt_client.publish(topic, payload)
            print(f"Published to {topic}: {payload}")
        time.sleep(PUBLISH_INTERVAL)

def main():
    # Initialize UDP socket and print info before anything else
    UDP_IP = get_local_ip()  # Automatically detect local WiFi IP
    print(f"[INFO] UDP listener starting on {UDP_IP}:{UDP_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[INFO] UDP socket bound. Waiting for packets...")

    # Print debug for each UDP packet received
    def udp_receive_loop():
        while True:
            data, addr = sock.recvfrom(1024)
            print(f"[DEBUG] UDP packet received from {addr}: {data!r}")
            try:
                decoded = data.decode().strip()
                print(f"[DEBUG] Decoded UDP data: {decoded}")
            except Exception as e:
                print(f"[DEBUG] Error decoding UDP data: {e}")
            # Process and store latest reading (MQTT may not be set up yet, so pass None)
            process_message(None, data, addr)
    # Start UDP receive loop in main thread (blocking)
    udp_receive_loop()

if __name__ == "__main__":
    main()
