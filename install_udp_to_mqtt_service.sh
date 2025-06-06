#!/bin/bash
# install_udp_to_mqtt_service.sh
# Installs a systemd service to run udp_to_mqtt.py on startup using venv

SERVICE_NAME="udp_to_mqtt"
VENVDIR="$(dirname "$(realpath "$0")")/venv"
PYTHON_PATH="$VENVDIR/bin/python3"
SCRIPT_PATH="$(dirname "$(realpath "$0")")/raspberry1/udp_to_mqtt.py"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_ROOT="$(dirname "$(dirname "$(realpath "$0")")")"

# Check if venv python exists
if [ ! -x "$PYTHON_PATH" ]; then
  echo "ERROR: venv python not found at $PYTHON_PATH. Please set up your venv first."
  exit 1
fi

# Create systemd service file
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=UDP to MQTT Gateway Service
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
