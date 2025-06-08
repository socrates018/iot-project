import os
import time
import json
import requests
import paho.mqtt.client as mqtt
import getpass

# Configuration
PRIVATE_IP = "10.64.44.156"
PUBLIC_IP = "194.177.207.38"
INFLUXDB_URL = f"http://{PUBLIC_IP}:8086"
MQTT_BROKER = PUBLIC_IP
MQTT_PORT = 1883
HOSTNAME = "team19"
DB_NAME = "team19_db"


def check_mqtt_password(broker, port, username, password):
    """
    Returns True if MQTT credentials are correct (can connect), False otherwise.
    """
    result = [False]

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            result[0] = True
        client.disconnect()

    client = mqtt.Client()
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


# Store latest values per device id
latest_values = {}


def load_mqtt_password():
    """
    Loads MQTT password from .env or prompts the user if not found.
    Returns the password as a string.
    """
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


def insert_data(db_name, user, password, device_id, measurement_type, value, timestamp):
    """
    Insert a data point into InfluxDB using line protocol.
    """
    line = f"{device_id},type={measurement_type} value={value} {timestamp}"
    response = requests.post(
        f"{INFLUXDB_URL}/write",
        params={"db": db_name},
        data=line,
        auth=requests.auth.HTTPBasicAuth(user, password)
    )
    print("Insert data:", response.ok, line)


def on_message(client, userdata, msg):
    try:
        print(f"Raw MQTT message: {msg.payload.decode()}")
        data = json.loads(msg.payload.decode())
        device_id = data.get("id", "unknown")
        if device_id not in latest_values:
            latest_values[device_id] = {}
        for key in ["temp", "hum", "caqi", "tvoc", "eco2"]:
            if key in data and "timestamp" in data:
                latest_values[device_id][key] = {
                    "value": data[key],
                    "timestamp": data["timestamp"]
                }
                insert_data(DB_NAME, HOSTNAME, MQTT_PASSWORD, device_id, key, data[key], data["timestamp"])
                print(f"Saved value {data[key]} for {key} from device {device_id} at {data['timestamp']}")
    except Exception as e:
        print("Error processing message:", e)


def main():
    # Check MQTT password before starting MQTT loop
    global MQTT_PASSWORD
    MQTT_PASSWORD = load_mqtt_password()
    if not check_mqtt_password(MQTT_BROKER, MQTT_PORT, HOSTNAME, MQTT_PASSWORD):
        print("Wrong MQTT password. Exiting.")
        return

    topic = f"iot/{HOSTNAME}/#"
    client_id = int(time.time() * 0.8)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
    client.username_pw_set(HOSTNAME, MQTT_PASSWORD)
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.subscribe(topic)
        print(f"Subscribing to {topic}. Waiting for messages...")
        client.loop_forever()
    except Exception as e:
        print(f"MQTT loop failed: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user!")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
