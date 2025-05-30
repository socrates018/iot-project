import random
import json
import requests
import paho.mqtt.client as mqtt
import getpass

# ---------- Configuration ----------
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
        import time
        time.sleep(1)  # Wait for connect callback
        client.loop_stop()
    except Exception:
        return False
    return result[0]

# Store latest values per device id
latest_values = {}

# ---------- Prompt for password ----------
MQTT_PASSWORD = getpass.getpass("Enter MQTT password: ")

# ---------- MQTT Setup ----------
topic = f"iot/{HOSTNAME}/#"
client_id = f"client_{random.randint(0, 1000)}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(HOSTNAME, MQTT_PASSWORD)

# ---------- InfluxDB insert ----------
def insert_data(db_name, user, password, measurement, value, timestamp, device_id):
    line = f"{measurement},id={device_id} value={value} {timestamp}"
    response = requests.post(
        f"{INFLUXDB_URL}/write",
        params={"db": db_name},
        data=line,
        auth=requests.auth.HTTPBasicAuth(user, password)
    )
    print("Insert data:", response.ok, line)

# ---------- MQTT Callback ----------
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
                insert_data(DB_NAME, HOSTNAME, MQTT_PASSWORD, key, data[key], data["timestamp"], device_id)
                print(f"Saved value {data[key]} for {key} from device {device_id} at {data['timestamp']}")
    except Exception as e:
        print("Error processing message:", e)

# ---------- Main loop ----------
def main():
    # Check MQTT password before starting MQTT loop
    if not check_mqtt_password(MQTT_BROKER, MQTT_PORT, HOSTNAME, MQTT_PASSWORD):
        print("Wrong MQTT password. Exiting.")
        return

    try:
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.subscribe(topic)

        print(f"Subscribing to {topic}. Waiting for messages...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Interrupted by user!")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
