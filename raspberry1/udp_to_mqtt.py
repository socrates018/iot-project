#!/usr/bin/env python3
"""
UDP Server Example for Concept 4

Listens for UDP packets from ESP32 sensor nodes, identifies them by MAC address,
and publishes their data to an MQTT broker.
Designed to run on a Raspberry Pi (or any Linux system with Python 3).

Usage:
    python3 udp_server_raspi_example.py

Make sure your firewall allows UDP traffic on the specified port.
Requirements:
    - paho-mqtt: pip install paho-mqtt
"""
import socket
import json
import paho.mqtt.client as mqtt
import time
import getpass

# MQTT Configuration (copied from mqtt_to_influx.py for consistency)
MQTT_BROKER = "194.177.207.38"  # Use public IP for MQTT broker
MQTT_PORT = 1883
MQTT_CLIENT_ID = "raspberry_pi_udp_gateway"
MQTT_TOPIC_PREFIX = "esp/sensors/"  # Topic prefix, will append device id
MQTT_USERNAME = "team19"  # Same as HOSTNAME in mqtt_to_influx.py
MQTT_RETRY_INTERVAL = 5    # Seconds between retry attempts
MAX_RETRY_ATTEMPTS = 3     # Maximum number of connection retry attempts
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

# Process message and publish to MQTT
def process_message(mqtt_client, data, addr):
    try:
        message = data.decode().strip()
        
        try:
            json_data = json.loads(message)
            mac_address = json_data.get("mac", "unknown")
            if mqtt_client:
                topic = f"{MQTT_TOPIC_PREFIX}{mac_address}"
                mqtt_client.publish(topic, message)
                print(f"Published to {topic}: {message}")
            else:
                print(f"Data from {mac_address}: {json_data}")
            
        except json.JSONDecodeError:
            parts = message.split(":", 1)
            if len(parts) == 2:
                mac_address, sensor_data = parts
                if mqtt_client:
                    topic = f"{MQTT_TOPIC_PREFIX}{mac_address}"
                    mqtt_client.publish(topic, sensor_data)
                    print(f"Published to {topic}: {sensor_data}")
                else:
                    print(f"Data from {mac_address}: {sensor_data}")
            else:
                print(f"Invalid message format from {addr}: {message}")
                
    except Exception as e:
        print(f"Error processing message: {e}")

UDP_IP = get_local_ip()  # Automatically detect local WiFi IP
UDP_PORT = 8080      # Must match the ESP32 sender

print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Set up MQTT client
mqtt_client = setup_mqtt()
if mqtt_client is None:
    print("Continuing without MQTT connection - messages will be printed to console only")
    # Remove the exit here to allow console-only mode

try:
    while True:
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        print(f"Received from {addr}: {data.decode().strip()}")
        
        # Process and publish to MQTT
        process_message(mqtt_client, data, addr)
            
except KeyboardInterrupt:
    print("\nServer stopped by user.")
finally:
    if mqtt_client:
        mqtt_client.loop_stop()
    sock.close()
