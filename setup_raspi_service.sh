#!/bin/bash
# setup_raspi_service.sh
# This script sets up a systemd service to run either udp_to_mqtt.py or mqtt_to_influx.py on boot.
# It also ensures the Python virtual environment is activated before running the script.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$REPO_DIR/venv.sh python3"

# Ask user which Raspberry Pi this is
read -p "Is this Raspberry Pi 1 (UDP to MQTT) or Raspberry Pi 2 (MQTT to Influx)? Enter 1 or 2: " RASPI_NUM

if [ "$RASPI_NUM" = "1" ]; then
    SERVICE_NAME="udp_to_mqtt"
    SCRIPT_PATH="$REPO_DIR/raspberry1/udp_to_mqtt.py"
elif [ "$RASPI_NUM" = "2" ]; then
    SERVICE_NAME="mqtt_to_influx"
    SCRIPT_PATH="$REPO_DIR/raspberry2/mqtt_to_influx.py"
else
    echo "Invalid input. Exiting."
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=IoT Python Service: $SERVICE_NAME
After=network.target

[Service]
Type=simple
WorkingDirectory=$REPO_DIR
ExecStart=/bin/bash -c 'cd $REPO_DIR && bash ./update.sh && bash $REPO_DIR/venv.sh python3 $SCRIPT_PATH'
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon and enabling $SERVICE_NAME.service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME.service
sudo systemctl restart $SERVICE_NAME.service

echo "Service $SERVICE_NAME has been set up and started."
