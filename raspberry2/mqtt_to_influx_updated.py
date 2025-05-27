
import json
import random
import socket
import requests
import paho.mqtt.client as mqtt
from requests.auth import HTTPBasicAuth
import getpass

# ---------- Configuration ----------
PUBLIC_IP = "194.177.207.38"
INFLUXDB_URL = f"http://{PUBLIC_IP}:8086"
MQTT_BROKER = PUBLIC_IP
MQTT_PORT = 1883

HOSTNAME = "team19"
DB_NAME = "team19_db"

# ---------- Prompt for password ----------
MQTT_PASSWORD = getpass.getpass("Enter MQTT password: ")

# ---------- MQTT Setup ----------
topic = f"iot/{HOSTNAME}/#"
client_id = f"client_{random.randint(0, 1000)}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(HOSTNAME, MQTT_PASSWORD)

# ---------- InfluxDB insert ----------
def insert_data(measurement, value, device_id, timestamp=None):
    line = f"{measurement},id={device_id} value={value}"
    if timestamp:
        line += f" {timestamp}"
    response = requests.post(
        f"{INFLUXDB_URL}/write",
        params={"db": DB_NAME},
        data=line,
        auth=HTTPBasicAuth(HOSTNAME, MQTT_PASSWORD)
    )
    print(f"📤 Insert {measurement}={value} (device: {device_id}) → OK:", response.ok)

# ---------- MQTT Callback ----------
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("id", "unknown")

        for key in ["temp", "hum", "caqi", "tvoc", "eco2"]:
            if key in payload:
                insert_data(key, payload[key], device_id)
    except Exception as e:
        print("❌ Error decoding message:", e)

# ---------- Main loop ----------
def main():
    try:
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.subscribe(topic)

        print(f"🚀 Subscribing to `{topic}`. Waiting for messages...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("❌ Interrupted by user!")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
