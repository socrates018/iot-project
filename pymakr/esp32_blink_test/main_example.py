import machine
import time

def main():
    led = machine.Pin(8, machine.Pin.OUT)  # Use pin 8 for ESP32-C3 onboard LED
    while True:
        led.value(1)  # LED on
        time.sleep(0.5)
        led.value(0)  # LED off
        time.sleep(0.5)

if __name__ == '__main__':
    main()