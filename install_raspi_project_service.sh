#!/bin/bash
# install_raspi_service.sh
# Installs a systemd service for one of the main Raspberry Pi Python scripts using venv

# Prompt user for service type
cat <<EOF
Which service do you want to install as a systemd service?
1) UDP to MQTT (per-device data)
2) UDP to MQTT (mean aggregation)
3) MQTT to Influx
4) MQTT Mean to Influx
EOF
read -p "Enter 1, 2, 3, or 4: " CHOICE

SCRIPT_PATH=""
SERVICE_NAME=""
DESC=""

case "$CHOICE" in
  1)
    SCRIPT_PATH="$(dirname \"$(realpath \"$0\")\")/raspberry1/udp_to_mqtt.py"
    SERVICE_NAME="udp_to_mqtt"
    DESC="UDP to MQTT Gateway Service (per-device)"
    ;;
  2)
    SCRIPT_PATH="$(dirname \"$(realpath \"$0\")\")/raspberry1/udp_to_mqtt_mean.py"
    SERVICE_NAME="udp_to_mqtt_mean"
    DESC="UDP to MQTT Gateway Service (mean aggregation)"
    ;;
  3)
    SCRIPT_PATH="$(dirname \"$(realpath \"$0\")\")/raspberry2/mqtt_to_influx.py"
    SERVICE_NAME="mqtt_to_influx"
    DESC="MQTT to InfluxDB Service"
    ;;
  4)
    SCRIPT_PATH="$(dirname \"$(realpath \"$0\")\")/raspberry2/mqtt_mean_to_influx.py"
    SERVICE_NAME="mqtt_mean_to_influx"
    DESC="MQTT Mean to InfluxDB Service"
    ;;
  *)
    echo "Invalid input. Exiting."
    exit 1
    ;;
esac

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENVDIR="$(dirname \"$(realpath \"$0\")\")/venv"
PYTHON_PATH="$VENVDIR/bin/python3"
PROJECT_ROOT="$(dirname \"$(dirname \"$(realpath \"$0\")\")\")"

# Check if venv python exists
if [ ! -x "$PYTHON_PATH" ]; then
  echo "ERROR: venv python not found at $PYTHON_PATH. Please set up your venv first."
  exit 1
fi

# Create systemd service file
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=$DESC
After=network.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 10
ExecStart=${PYTHON_PATH} ${SCRIPT_PATH}
WorkingDirectory=${PROJECT_ROOT}
Restart=on-failure
RestartSec=10
User=$(whoami)
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "Service $SERVICE_NAME installed and started using venv python."
echo "To check status: sudo systemctl status $SERVICE_NAME"
echo "To see logs: sudo journalctl -u $SERVICE_NAME -f"

# Show live logs automatically
echo "\n--- Showing live logs for $SERVICE_NAME (press Ctrl+C to exit) ---"
sudo journalctl -u $SERVICE_NAME -f
