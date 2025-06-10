import os
import time
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
MQTT_CLIENT_ID = f"client_mean_influx_{int(time.time() * 0.75)}"
SENSOR_KEYS = ["temp", "hum", "caqi", "tvoc", "eco2"]
MEAN_TOPIC = f"iot/{HOSTNAME}/mean_value/+"


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


def insert_data(db_name, user, password, measurement_type, value, timestamp=None):
    try:
        line = f"mean_value,type={measurement_type} value={value}"
        if timestamp:
            line += f" {timestamp}"
        response = requests.post(
            f"{INFLUXDB_URL}/write",
            params={"db": db_name},
            data=line,
            auth=requests.auth.HTTPBasicAuth(user, password),
            timeout=5
        )
        if not response.ok:
            print(f"Failed to insert data: {response.status_code} {response.text}")
        else:
            print("Insert data:", response.ok, line)
    except requests.exceptions.Timeout:
        print("[ERROR] InfluxDB request timed out for line:", line)
    except Exception as e:
        print(f"[ERROR] Exception during insert_data: {e}")


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode(errors="replace")
        print(f"[MQTT] Received message on topic: {topic} | payload: {payload}")
        parts = topic.split('/')
        if len(parts) >= 4 and parts[2] == "mean_value":
            measurement_type = parts[3]
            raw_value = payload
            try:
                if measurement_type in ("temp", "hum"):
                    value = float(raw_value)
                else:
                    value = int(raw_value)
            except ValueError:
                print(f"[WARN] Could not parse value '{raw_value}' for type '{measurement_type}'. Skipping.")
                return
            insert_data(DB_NAME, HOSTNAME, MQTT_PASSWORD, measurement_type, value)
        else:
            print(f"[WARN] Ignored message with unexpected topic structure: {topic}")
    except Exception as e:
        print(f"[ERROR] Exception in on_message: {e}")


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[INFO] Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} as {HOSTNAME}.")
    else:
        print(f"[ERROR] Failed to connect to MQTT broker, rc={rc}")


def on_disconnect(client, userdata, rc):
    if rc == 0:
        print(f"[INFO] Cleanly disconnected from MQTT broker.")
    else:
        print(f"[WARN] Unexpected disconnect from MQTT broker (rc={rc})")


def main():
    global MQTT_PASSWORD
    MQTT_PASSWORD = load_mqtt_password()
    if not check_mqtt_password(MQTT_BROKER, MQTT_PORT, HOSTNAME, MQTT_PASSWORD):
        print("Wrong MQTT password. Exiting.")
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.username_pw_set(HOSTNAME, MQTT_PASSWORD)
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.enable_logger()

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.subscribe(MEAN_TOPIC)
        print(f"Subscribing to {MEAN_TOPIC}. Waiting for mean value messages...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Interrupted by user!")
    except Exception as e:
        print(f"MQTT loop failed: {e}")
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            print(f"[ERROR] Exception during cleanup: {e}")

if __name__ == "__main__":
    main()
