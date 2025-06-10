#!/bin/bash
# run_raspi_python.sh
# This script runs update.sh, then venv.sh, then the correct Python file for the selected Raspberry Pi.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ask user which Raspberry Pi this is
read -p "Is this Raspberry Pi 1 (UDP to MQTT) or Raspberry Pi 2 (MQTT to Influx)? Enter 1 or 2: " RASPI_NUM

# Ask if user wants to run the mean version
read -p "Do you want to run the 'mean' version of the script? (y/n): " RUN_MEAN

if [ "$RASPI_NUM" = "1" ]; then
    if [[ "$RUN_MEAN" =~ ^[Yy]$ ]]; then
        SCRIPT_PATH="$REPO_DIR/raspberry1/udp_to_mqtt_mean.py"
    else
        SCRIPT_PATH="$REPO_DIR/raspberry1/udp_to_mqtt.py"
    fi
elif [ "$RASPI_NUM" = "2" ]; then
    if [[ "$RUN_MEAN" =~ ^[Yy]$ ]]; then
        SCRIPT_PATH="$REPO_DIR/raspberry2/mqtt_mean_to_influx.py"
    else
        SCRIPT_PATH="$REPO_DIR/raspberry2/mqtt_to_influx.py"
    fi
else
    echo "Invalid input. Exiting."
    exit 1
fi

# Run update.sh
bash "$REPO_DIR/update.sh"

# Run venv.sh with python file
bash "$REPO_DIR/venv.sh" "$SCRIPT_PATH"
