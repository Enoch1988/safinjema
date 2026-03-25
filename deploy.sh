#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  deploy.sh  –  SaFi Njema Python Backend Deployment
#  Ubuntu 22.04 / 24.04 · Python 3.11 + Gunicorn + Nginx + SSL
#  Usage:  chmod +x deploy.sh && sudo bash deploy.sh
# ═══════════════════════════════════════════════════════════════
set -e
DOMAIN="safinjema.co.za"
APP_DIR="/var/www/safinjema"
SERVICE_NAME="safinjema"
PYTHON_VERSION="3.11"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║  🌿  SaFi Njema Python Backend – Deployment   ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# ── 1. System packages ──
echo "▶  Installing system packages..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx -qq

echo "   Python: $(python3 --version)"

# ── 2. App directory ──
echo "▶  Setting up $APP_DIR..."
mkdir -p "$APP_DIR"
rsync -a --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' \
      --exclude='data/' --exclude='.venv/' . "$APP_DIR/"
cd "$APP_DIR"
mkdir -p data

# ── 3. Virtual environment ──
echo "▶  Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install gunicorn --quiet

# ── 4. Check .env ──
if [ ! -f .env ]; then
  echo ""
  echo "⚠️   No .env file found!"
  echo "    cp .env.example .env && nano $APP_DIR/.env"
  read -p "    Press Enter once .env is configured..." _
fi

# ── 5. Systemd service ──
echo "▶  Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SERVICE
[Unit]
Description=SaFi Njema Python Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/.venv/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/safinjema-access.log \
    --error-logfile  /var/log/safinjema-error.log \
    --timeout 60
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

chown -R www-data:www-data "$APP_DIR"
systemctl daemon-reload
systemctl enable  "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
echo "   Service status: $(systemctl is-active $SERVICE_NAME)"

# ── 6. Nginx ──
echo "▶  Configuring Nginx..."
cat > "/etc/nginx/sites-available/${DOMAIN}" << NGINX
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    root ${APP_DIR}/public;
    index index.html;

    # Proxy all /api requests to FastAPI
    location /api {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        client_max_body_size 10m;
    }

    # FastAPI auto-docs
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
    }

    # Static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2|webp|svg)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files \$uri \$uri/ \$uri.html /index.html;
    }

    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript;
}
NGINX

ln -sf "/etc/nginx/sites-available/${DOMAIN}" "/etc/nginx/sites-enabled/" 2>/dev/null || true
nginx -t && systemctl reload nginx

# ── 7. SSL ──
echo "▶  SSL certificate..."
certbot --nginx -d "$DOMAIN" -d "www.${DOMAIN}" --non-interactive --agree-tos \
  -m "$(grep SMTP_USER .env 2>/dev/null | cut -d= -f2 || echo admin@${DOMAIN})" --redirect 2>/dev/null || \
  echo "   ⚠️  SSL skipped — run: certbot --nginx -d ${DOMAIN}"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║  ✅  Deployment Complete!                     ║"
echo "╠═══════════════════════════════════════════════╣"
echo "║  🌐  https://${DOMAIN}"
echo "║  📖  API Docs: https://${DOMAIN}/docs"
echo "║  👑  Admin:    https://${DOMAIN}/admin.html"
echo "╠═══════════════════════════════════════════════╣"
echo "║  Logs:    journalctl -u safinjema -f          ║"
echo "║  Restart: systemctl restart safinjema         ║"
echo "╚═══════════════════════════════════════════════╝"
