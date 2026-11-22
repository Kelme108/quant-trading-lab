#!/usr/bin/env bash
# Prepares a fresh Ubuntu 24.04 VM (Azure Brazil South, B2als v2) to run the lab's Freqtrade bots 24/7.
# Run once, as the admin user created with the VM:
#   curl -fsSL <raw url of this file> -o bootstrap.sh   (or scp it)   &&   bash bootstrap.sh
# Idempotent: running it again only re-applies the same settings.
#
# It does NOT: create the VM, open any inbound port besides SSH, put any key on disk,
# start any bot, or turn dry_run off. Secrets go into .env files by hand afterwards.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Kelme108/quant-trading-lab.git}"
APP_DIR="${APP_DIR:-$HOME/quant-trading-lab}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"

echo "== packages"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  docker.io docker-compose-v2 git sqlite3 chrony ufw unattended-upgrades python3 jq

echo "== clock: UTC + chrony (Binance rejects requests with a skewed timestamp)"
sudo timedatectl set-timezone UTC
sudo systemctl enable --now chrony
chronyc tracking | head -3 || true

echo "== automatic security updates"
sudo dpkg-reconfigure -f noninteractive unattended-upgrades

echo "== firewall: SSH only (the Freqtrade API stays disabled / bound to 127.0.0.1)"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw --force enable

echo "== docker: start on boot, rotate container logs"
sudo mkdir -p /etc/docker
echo '{"log-driver":"json-file","log-opts":{"max-size":"20m","max-file":"5"}}' | sudo tee /etc/docker/daemon.json >/dev/null
sudo systemctl enable --now docker
sudo systemctl restart docker
sudo usermod -aG docker "$USER"
sudo docker pull freqtradeorg/freqtrade:2026.9

echo "== repository"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"   # a private repo asks for a GitHub token or deploy key here
fi
mkdir -p "$APP_DIR/user_data/logs" "$APP_DIR/ops/state" "$BACKUP_DIR"

echo "== Freqtrade file logs: rotate daily, keep 14"
sudo tee /etc/logrotate.d/trading-lab >/dev/null <<EOF
$APP_DIR/user_data/logs/*.log {
  daily
  rotate 14
  compress
  missingok
  notifempty
  copytruncate
}
EOF

echo "== cron: guard every 5 min, SQLite backup daily at 03:10 UTC (kept 30 days)"
CRON_TMP="$(mktemp)"
crontab -l 2>/dev/null | grep -v '# trading-lab' > "$CRON_TMP" || true
cat >> "$CRON_TMP" <<EOF
*/5 * * * * cd $APP_DIR && python3 ops/freqtrade_guard.py --config ops/guard.forward.json >> ops/state/guard-cron.log 2>&1 # trading-lab
10 3 * * * cd $APP_DIR && for f in user_data/tradesv3.*.sqlite; do sqlite3 "\$f" ".backup '$BACKUP_DIR/\$(basename "\$f" .sqlite)-\$(date +\%F).sqlite'"; done && find $BACKUP_DIR -name '*.sqlite' -mtime +30 -delete # trading-lab
EOF
crontab "$CRON_TMP"
rm -f "$CRON_TMP"

echo
echo "== done"
echo "Public IP (whitelist it on the Binance API key):  $(curl -fsS https://api.ipify.org || echo '?')"
echo "Log out and back in so the docker group applies. Next steps: docs/runbook-ao-vivo.md"
