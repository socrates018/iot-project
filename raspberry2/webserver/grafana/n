#!/bin/bash

# Εγκατάσταση Grafana
sudo apt update
sudo apt install -y grafana

# Αντιγραφή provisioning config
sudo mkdir -p /etc/grafana/provisioning/{dashboards,datasources}
sudo cp grafana/dashboards/dashboard.json /etc/grafana/provisioning/dashboards/
sudo cp grafana/provisioning/* /etc/grafana/provisioning/

# Εκκίνηση Grafana
sudo systemctl enable grafana-server
sudo systemctl restart grafana-server

echo "✅ Grafana setup complete! Access it on http://<your_rpi_ip>:3000"

