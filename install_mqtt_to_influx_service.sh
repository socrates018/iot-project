#!/bin/bash
# install_mqtt_to_influx_service.sh
# Installs a systemd service to run mqtt_to_influx.py on startup

SERVICE_NAME="mqtt_to_influx"
PYTHON_PATH="/usr/bin/python3"
SCRIPT_PATH="$(dirname "$(realpath "$0")")/raspberry2/mqtt_to_influx.py"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Create systemd service file
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=MQTT to InfluxDB Gateway Service
After=network.target

[Service]
Type=simple
ExecStart=${PYTHON_PATH} ${SCRIPT_PATH}
WorkingDirectory=$(dirname "$SCRIPT_PATH")
Restart=on-failure
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Service $SERVICE_NAME installed and started."
echo "To check status: sudo systemctl status $SERVICE_NAME"
echo "To see logs: sudo journalctl -u $SERVICE_NAME -f"
