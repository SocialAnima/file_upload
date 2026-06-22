#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/file_upload"
SERVICE_NAME="file-upload"

echo "==> 安装系统依赖（Python3、venv、nginx）"
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip nginx
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3 python3-pip nginx
else
    echo "请手动安装 python3、python3-venv 和 nginx"
fi

echo "==> 创建应用目录"
sudo mkdir -p "$APP_DIR"
sudo rsync -a --delete \
    --exclude venv \
    --exclude data \
    --exclude .env \
    ./ "$APP_DIR/"

echo "==> 创建虚拟环境并安装依赖"
sudo python3 -m venv "$APP_DIR/venv"
sudo "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> 配置环境变量"
if [ ! -f "$APP_DIR/.env" ]; then
    sudo cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sudo sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" "$APP_DIR/.env"
    echo "已生成 .env，默认管理密码为 admin123，请登录后立即修改"
fi

echo "==> 创建数据目录"
sudo mkdir -p "$APP_DIR/data/uploads"
sudo chown -R www-data:www-data "$APP_DIR"

echo "==> 安装 systemd 服务"
sudo cp "$APP_DIR/deploy/file-upload.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "==> 配置 Nginx"
NGINX_SNIPPET="/etc/nginx/conf.d/file_upload.conf"
sudo cp "$APP_DIR/deploy/nginx-file_upload.conf" "$NGINX_SNIPPET"

if ! grep -q "include /etc/nginx/conf.d/file_upload.conf;" /etc/nginx/nginx.conf 2>/dev/null; then
    echo "请在现有 server 块中加入: include /etc/nginx/conf.d/file_upload.conf;"
    echo "或直接粘贴 deploy/nginx-file_upload.conf 到对应 server 配置中"
fi

sudo nginx -t
sudo systemctl reload nginx

echo "==> 部署完成"
echo "访问地址: http://106.54.199.248/file_upload"
echo "默认管理密码: admin123"
