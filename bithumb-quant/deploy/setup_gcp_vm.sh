#!/usr/bin/env bash
# ==============================================================================
# 1-Click Setup Script for GCP Always Free VM / Oracle Cloud Free Tier
# Sets up Python 3.11, 2GB Swap (prevents OOM on 1GB RAM instances), NTP Sync, and Systemd/Docker
# ==============================================================================

set -e

echo "🚀 Starting 1-Click Server Setup for Bithumb Quant Bot..."

# 1. Update OS Packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git curl docker.io docker-compose chrony

# 2. Configure 2GB Swap Memory (Crucial for GCP e2-micro 1GB RAM instances)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 2GB Swap file for RAM optimization..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ 2GB Swap memory activated."
fi

# 3. Synchronize NTP System Clock (Crucial for Bithumb JWT Nonce Auth)
sudo systemctl enable --now chrony
sudo chronyc tracking

# 4. Create Project Virtual Environment
PROJECT_DIR="/opt/bithumb-quant"
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

if [ -d "$PROJECT_DIR/venv" ]; then
    echo "Python venv already exists."
else
    python3 -m venv $PROJECT_DIR/venv
    echo "✅ Python virtual environment created at $PROJECT_DIR/venv"
fi

# 5. Install Systemd Service
if [ -f "$PROJECT_DIR/deploy/bithumb-quant.service" ]; then
    sudo cp $PROJECT_DIR/deploy/bithumb-quant.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable bithumb-quant.service
    echo "✅ Systemd service installed and enabled."
fi

echo "=============================================================================="
echo "🎉 Setup Complete!"
echo "Next steps:"
echo "1. Edit /opt/bithumb-quant/.env with your Bithumb, Gemini, and Telegram keys."
echo "2. Start the service using: sudo systemctl start bithumb-quant"
echo "3. Monitor logs using: sudo journalctl -u bithumb-quant -f"
echo "=============================================================================="
