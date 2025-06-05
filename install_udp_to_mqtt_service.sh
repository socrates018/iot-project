#!/bin/bash
# install_udp_to_mqtt_service.sh
# Installs a systemd service to run udp_to_mqtt.py on startup

SERVICE_NAME="udp_to_mqtt"
PYTHON_PATH="/usr/bin/python3"
SCRIPT_PATH="$(dirname "$(realpath "$0")")/raspberry1/udp_to_mqtt.py"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Create systemd service file
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=UDP to MQTT Gateway Service
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
