import time
import board
import busio
import random
import socket
import logging
import RPi.GPIO as GPIO
import adafruit_ahtx0
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv

LOGGING: str = "console"
LOG_FILE: str = "stats.log"

LED_PIN: int = 18

load_dotenv()

MY_TEAM = socket.gethostname()
PUBLISH_INTERVAL = 5

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_ahtx0.AHTx0(i2c)

broker_address = "10.64.44.156" # Public IP: 194.177.207.38
broker_port = 1883
topic = f"iot/{MY_TEAM}"
client_id = f"client_{random.randint(0, 1000)}"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(MY_TEAM, getenv("MQTT_PASSWORD"))

client.connect(broker_address, broker_port)
client.loop_start()

def config_gpio() -> None:
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(LED_PIN, GPIO.OUT)
  GPIO.output(LED_PIN, GPIO.LOW)

def config_logging() -> None:
  logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
  )

def get_measurements() -> tuple[float, float]:
  if LOGGING == "file":
    logging.debug("Getting AHTx0 sensor measurements...")
  
  temperature = sensor.temperature
  humidity = sensor.relative_humidity

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
  config_gpio()
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
    GPIO.cleanup()
    
    if LOGGING == "console":
      print("Received Ctrl+C signal! Bye")
    else:
      logging.info("Received Ctrl+C signal! Bye")

  finally:
    client.loop_stop()  # Stop the background MQTT loop
    client.disconnect()  # Disconnect from the broker

if __name__ == "__main__":
  main()
  
  exit(0)
