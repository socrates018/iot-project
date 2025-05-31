#!/bin/bash
# check_raspi_services.sh
# Shows status and logs for both udp_to_mqtt and mqtt_to_influx systemd services

echo "--- Service Status: udp_to_mqtt ---"
sudo systemctl status udp_to_mqtt.service --no-pager

echo "--- Service Status: mqtt_to_influx ---"
sudo systemctl status mqtt_to_influx.service --no-pager

echo "--- Last 50 log lines: udp_to_mqtt ---"
sudo journalctl -u udp_to_mqtt.service -n 50 --no-pager

echo "--- Last 50 log lines: mqtt_to_influx ---"
sudo journalctl -u mqtt_to_influx.service -n 50 --no-pager
