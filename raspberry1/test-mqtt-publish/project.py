import time
import random
import socket
import logging
import paho.mqtt.client as mqtt

LOGGING = "console"
LOG_FILE = "stats.log"

PUBLISH_INTERVAL = 5

MY_TEAM = "team19"

# Use only public IPs
broker_address = "194.177.207.38"
broker_port = 1883
topic = f"iot/{MY_TEAM}"
client_id = f"client_{random.randint(0, 1000)}"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.connect(broker_address, broker_port)
client.loop_start()

def config_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_measurements() -> tuple[float, float]:
    # Generate random temperature and humidity
    temperature = random.uniform(15.0, 30.0)
    humidity = random.uniform(30.0, 70.0)

    client.publish(f"{topic}/airTemperature", f"{temperature:.2f}", qos=1)
    client.publish(f"{topic}/airHumidity", f"{humidity:.2f}", qos=1)

    if LOGGING == "console":
        print(f"Temperature: {temperature:.2f} °C")
        print(f"Humidity: {humidity:.2f} %")
    else:
        logging.info(f"Temperature: {temperature:.2f} °C")
        logging.info(f"Humidity: {humidity:.2f} %")

    return temperature, humidity

def main() -> None:
    config_logging()
    try:
        while True:
            temperature, humidity = get_measurements()

            if LOGGING == "console":
                print(f"Temperature value is: {temperature:.2f}")
                print(f"Humidity value is: {humidity:.2f}")
            else:
                logging.info(f"Temperature value is: {temperature:.2f}")
                logging.info(f"Humidity value is: {humidity:.2f}")

            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        if LOGGING == "console":
            print("Received Ctrl+C signal! Bye")
        else:
            logging.info("Received Ctrl+C signal! Bye")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
    exit(0)
