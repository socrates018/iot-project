#!/bin/bash

# Install Grafana
sudo apt update
sudo apt install -y grafana

# Ask user for InfluxDB password for Grafana datasource
echo -n "Enter the InfluxDB password for Grafana datasource (team19): "
read -s INFLUX_PASS
echo

# Prepare provisioning folders
sudo mkdir -p /etc/grafana/provisioning/dashboards
sudo mkdir -p /etc/grafana/provisioning/datasources

# Copy dashboard JSON to provisioning folder
sudo cp dashboards/dashboard.json /etc/grafana/provisioning/dashboards/

# Copy and update datasource.yml with provided password
tmpfile=$(mktemp)
sed "s|basicAuthPassword:.*|basicAuthPassword: $INFLUX_PASS|" provisioning/datasource.yml > "$tmpfile"
sudo cp "$tmpfile" /etc/grafana/provisioning/datasources/datasource.yml
rm "$tmpfile"

# Copy dashboard provisioning YAML if exists
dash_yaml="dashboards/dashboard.yaml"
if [ -f "$dash_yaml" ]; then
    sudo cp "$dash_yaml" /etc/grafana/provisioning/dashboards/
fi

# Enable and start Grafana service
sudo systemctl enable grafana-server
sudo systemctl restart grafana-server

echo "✅ Grafana setup complete! Access it at http://<your_rpi_ip>:3000"

