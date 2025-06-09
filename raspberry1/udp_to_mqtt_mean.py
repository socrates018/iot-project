#!/usr/bin/env python3
"""
UDP to MQTT Gateway with Aggregation (Mean Value)

Listens for UDP packets from ESP32 sensor nodes, aggregates (mean) all values for each measurement across all devices, and publishes each mean value to its own MQTT topic (e.g., iot/team19/mean_value/temp).
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
MQTT_CLIENT_ID = f"client_mean_{int(time.time() * 0.6)}"
MQTT_TOPIC_PREFIX = "iot/team19/mean_value"
MQTT_USERNAME = "team19"
USE_TCP = False
PUBLISH_INTERVAL = 60  # seconds
SENSOR_KEYS = ["temp", "hum", "caqi", "tvoc", "eco2"]


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


def aggregate_mean(data_list):
    means = {}
    for key in SENSOR_KEYS:
        if key in ("temp", "hum"):
            values = [float(entry[key]) for entry in data_list if key in entry and isinstance(entry[key], (int, float))]
            if values:
                means[key] = round(sum(values) / len(values), 2)
        else:
            values = [entry[key] for entry in data_list if key in entry and isinstance(entry[key], (int, float))]
            if values:
                means[key] = int(round(sum(values) / len(values)))
    return means


def main():
    password = load_mqtt_password()
    if not check_mqtt_password(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, password):
        print("Wrong MQTT password. Exiting.")
        return
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USERNAME, password)
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()

    sock, use_tcp = setup_socket_and_mode()
    received_data = []
    last_publish = time.time()

    try:
        while True:
            sock.settimeout(1)
            try:
                data, addr = receive_packet(sock, use_tcp)
                message = data.decode().strip()
                json_data = json.loads(message)
                json_data.pop("id", None)
                received_data.append(json_data)
            except socket.timeout:
                pass
            except Exception as e:
                print(f"[ERROR] Failed to process packet: {e}")
            now = time.time()
            if now - last_publish >= PUBLISH_INTERVAL:
                mean_data = aggregate_mean(received_data)
                for key, value in mean_data.items():
                    topic = f"{MQTT_TOPIC_PREFIX}/{key}"
                    payload = str(value)
                    result = client.publish(topic, payload)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        print(f"Published mean {key} to {topic}: {payload}")
                    else:
                        print(f"[ERROR] Failed to publish mean {key} to {topic}: {payload}")
                    result.wait_for_publish()
                received_data.clear()
                last_publish = now
    except KeyboardInterrupt:
        print("Interrupted by user!")
    finally:
        client.loop_stop()
        client.disconnect()
        sock.close()

if __name__ == "__main__":
    main()
