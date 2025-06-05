#!/bin/bash
# install_mqtt_to_influx_service.sh
# Installs a systemd service to run mqtt_to_influx.py on startup using venv

SERVICE_NAME="mqtt_to_influx"
VENVDIR="$(dirname "$(realpath "$0")")/venv"
PYTHON_PATH="$VENVDIR/bin/python3"
SCRIPT_PATH="$(dirname "$(realpath "$0")")/raspberry2/mqtt_to_influx.py"
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
Description=MQTT to InfluxDB Gateway Service
After=network.target

[Service]
Type=simple
ExecStart=${PYTHON_PATH} ${SCRIPT_PATH}
WorkingDirectory=${PROJECT_ROOT}
Restart=on-failure
User=$(whoami)

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
