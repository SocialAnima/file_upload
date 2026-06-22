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
sudo mkdir -p /etc/nginx/snippets
sudo cp "$APP_DIR/deploy/nginx-location.conf" /etc/nginx/snippets/file_upload_location.conf

# 清理旧版错误配置（location 不能直接放在 conf.d 顶层）
if [ -f /etc/nginx/conf.d/file_upload.conf ]; then
    sudo rm /etc/nginx/conf.d/file_upload.conf
fi

DEFAULT_SITE="/etc/nginx/sites-enabled/default"
if [ -f "$DEFAULT_SITE" ] && ! grep -q "file_upload_location.conf" "$DEFAULT_SITE"; then
    echo ""
    echo "Nginx 片段已安装到 /etc/nginx/snippets/file_upload_location.conf"
    echo "请编辑 $DEFAULT_SITE，在 server { ... } 内加入："
    echo "    include snippets/file_upload_location.conf;"
    echo ""
    echo "然后执行: sudo nginx -t && sudo systemctl reload nginx"
else
    sudo nginx -t
    sudo systemctl reload nginx
fi

echo "==> 部署完成"
echo "访问地址: http://106.54.199.248/file_upload"
echo "默认管理密码: admin123"
