import random
import socket
import requests
import paho.mqtt.client as mqtt
from requests.auth import HTTPBasicAuth
import getpass

# ---------- Configuration ----------
# ---------- Configuration ----------
PRIVATE_IP = "10.64.44.156"
PUBLIC_IP = "194.177.207.38"
INFLUXDB_URL = f"http://{PUBLIC_IP}:8086"    # Internal IP for InfluxDB
MQTT_BROKER = PUBLIC_IP                       # Internal IP for MQTT Broker
MQTT_PORT = 1883
#HOSTNAME = socket.gethostname()              # π.χ. "team19"
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
def insert_data(db_name, user, password, measurement, value, timestamp=None):
    line = f"{measurement} value={value}"
    if timestamp:
        line += f" {timestamp}"
    response = requests.post(
        f"{INFLUXDB_URL}/write",
        params={"db": db_name},
        data=line,
        auth=HTTPBasicAuth(user, password)
    )
    print("📤 Insert data:", response.ok)

# ---------- MQTT Callback ----------
def on_message(client, userdata, msg):
    measurement = msg.topic.split("/")[-1]
    value = msg.payload.decode()

    insert_data(DB_NAME, HOSTNAME, MQTT_PASSWORD, measurement, value)
    print(f"📥 Write `{value}` to `{measurement}`")

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
