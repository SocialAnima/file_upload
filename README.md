# 资源下载网站

基于 Flask 的文件资源下载站点，支持公开浏览/下载、密码保护的管理模式（上传、删除、修改密码），单文件上传限制 100MB。

## 功能

- 用户：查看文件列表、下载文件
- 管理员：上传文件、删除文件、修改管理密码
- 访问路径：`http://106.54.199.248/file_upload`

## 本地开发

```bash
cd file_upload
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS

python wsgi.py
```

本地可直接运行：

```bash
flask --app wsgi:app run --debug
```

或：

```bash
python -c "from wsgi import app; app.run(debug=True, port=5000)"
```

开发环境访问：`http://127.0.0.1:5000/file_upload/`

默认管理密码：`admin123`（可在 `.env` 中通过 `DEFAULT_ADMIN_PASSWORD` 修改，仅首次初始化数据库时生效）

## 服务器部署（106.54.199.248）

### 1. 上传代码到服务器

```bash
scp -r . user@106.54.199.248:/tmp/file_upload
ssh user@106.54.199.248
cd /tmp/file_upload
```

### 2. 执行部署脚本

```bash
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

若出现 `/usr/bin/env: 'bash\r': No such file or directory`，说明脚本被 Windows 换行符污染，在服务器上执行：

```bash
sed -i 's/\r$//' deploy/deploy.sh
sudo bash deploy/deploy.sh
```

脚本会完成：

- 安装 Python 依赖
- 复制代码到 `/opt/file_upload`
- 创建虚拟环境与 `.env`
- 注册并启动 systemd 服务
- 配置 Nginx 反向代理

### 3. Nginx 配置

将 [deploy/nginx-file_upload.conf](deploy/nginx-file_upload.conf) 内容加入现有 `server` 块，例如：

```nginx
server {
    listen 80;
    server_name 106.54.199.248;

    include /etc/nginx/conf.d/file_upload.conf;
}
```

关键配置：

- 子路径：`/file_upload/`
- 上传限制：`client_max_body_size 100m;`

### 4. 验证

```bash
sudo systemctl status file-upload
curl -I http://127.0.0.1/file_upload/
```

浏览器访问：`http://106.54.199.248/file_upload`

## 管理说明

1. 点击右上角「管理」按钮
2. 输入管理密码（默认 `admin123`）
3. 登录后可上传、删除文件，或在面板底部修改密码

**部署后请立即修改默认密码。**

## 目录说明

```
app/              Flask 应用代码
data/uploads/     上传文件存储（运行时生成）
data/app.db       SQLite 数据库（运行时生成）
deploy/           Nginx、systemd、部署脚本
wsgi.py           应用入口
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | Session 密钥 | 必填（生产环境） |
| DEFAULT_ADMIN_PASSWORD | 初始管理密码 | admin123 |
| BASE_PATH | 访问前缀 | /file_upload |
| MAX_UPLOAD_SIZE_MB | 上传大小限制 | 100 |

## 常用运维命令

```bash
sudo systemctl restart file-upload
sudo journalctl -u file-upload -f
sudo nginx -t && sudo systemctl reload nginx
```
