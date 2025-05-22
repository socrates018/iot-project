import random
import socket
import requests
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

INFLUXDB_URL = "http://194.177.207.38:8086" # Public IP: 194.177.207.38
MY_TEAM = socket.gethostname()

load_dotenv()

db_name = "team19_db"
broker_address = "194.177.207.38" # Public IP: 194.177.207.38 # Private IP: 10.64.44.156
broker_port = 1883
topic = f"iot/{MY_TEAM}/#"
client_id = f"client_{random.randint(0, 1000)}"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(MY_TEAM, getenv("MQTT_PASSWORD"))

def insert_data(db_name, user, password, measurement, value, timestamp=None):
  line = f"{measurement} value={value}"
  if timestamp:
    line += f" {timestamp}"
  response = requests.post(f"{INFLUXDB_URL}/write", 
                            params={"db": db_name},
                            data=line,
                            auth=HTTPBasicAuth(MY_TEAM, getenv("MQTT_PASSWORD")))
  print("Insert data:", response.ok)

def on_connect(client, userdata, flags, reason_code, properties):
  print(f"[DEBUG] Connected to MQTT broker with reason code: {reason_code}")
  print(f"[DEBUG] Subscribing to topic: {topic}")
  client.subscribe(topic)

def on_subscribe(client, userdata, mid, granted_qos, properties):
  print(f"[DEBUG] Subscribed: mid={mid}, granted_qos={granted_qos}")

def on_message(client, userdata, msg):
  print(f"[DEBUG] Received MQTT message:")
  print(f"  Topic: {msg.topic}")
  print(f"  Payload: {msg.payload.decode(errors='replace')}")
  print(f"  QoS: {msg.qos}")
  print(f"  Retain: {msg.retain}")
  print(f"  Properties: {getattr(msg, 'properties', None)}")
  measurement = msg.topic.split("/")[-1]
  
  insert_data(db_name, MY_TEAM, getenv("MQTT_PASSWORD"), measurement, msg.payload.decode())
  
  print(f"Write `{msg.payload.decode()}` to `{measurement}`")

def main():
  try:
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    print(f"[DEBUG] Connecting to MQTT broker at {broker_address}:{broker_port} with client_id={client_id}")
    client.connect(broker_address, broker_port)
    print(f"[DEBUG] Entering MQTT loop_forever()")
    client.loop_forever()
  except KeyboardInterrupt:
    print("Receive Ctrl+C signal! Bye")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
  main()

  exit(0)
