import random
import socket
import json
import requests
import paho.mqtt.client as mqtt
from requests.auth import HTTPBasicAuth
import getpass

# ---------- Configuration ----------
PRIVATE_IP = "10.64.44.156"
PUBLIC_IP = "194.177.207.38"
INFLUXDB_URL = f"http://{PUBLIC_IP}:8086"
MQTT_BROKER = PUBLIC_IP
MQTT_PORT = 1883
HOSTNAME = "team19"
DB_NAME = "team19_db"


def check_influxdb_password(db_name, user, password, influxdb_url):
    """
    Returns True if the credentials are correct, False otherwise.
    """
    import requests
    from requests.auth import HTTPBasicAuth
    query = "SHOW MEASUREMENTS"
    response = requests.get(
        f"{influxdb_url}/query",
        params={"db": db_name, "q": query},
        auth=HTTPBasicAuth(user, password)
    )
    return response.status_code != 401



# Store latest values per device id
latest_values = {}

# ---------- Prompt for password ----------
MQTT_PASSWORD = getpass.getpass("Enter MQTT password: ")

# ---------- MQTT Setup ----------
topic = f"iot/{HOSTNAME}/#"
client_id = f"client_{random.randint(0, 1000)}" #check this
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(HOSTNAME, MQTT_PASSWORD)

# ---------- InfluxDB insert ----------
def insert_data(db_name, user, password, measurement, value, timestamp, device_id):
    line = f"{measurement},id={device_id} value={value} {timestamp}"
    response = requests.post(
        f"{INFLUXDB_URL}/write",
        params={"db": db_name},
        data=line,
        auth=HTTPBasicAuth(user, password)
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
    # Check InfluxDB password before starting MQTT loop
    INFLUXDB_PASSWORD = getpass.getpass("Enter InfluxDB password: ")
    if not check_influxdb_password(DB_NAME, HOSTNAME, INFLUXDB_PASSWORD, INFLUXDB_URL):
        print("Wrong InfluxDB password. Exiting.")
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
