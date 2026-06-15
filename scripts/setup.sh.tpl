#!/bin/bash
set -e

yum install -y python3 python3-pip nginx
mkdir -p /opt/blog

cat > /opt/blog/app.py << 'PYEOF'
${app_content}
PYEOF

pip3 install -r /dev/stdin << 'REQEOF'
${requirements}
REQEOF

cat > /etc/systemd/system/blog.service << 'SVCEOF'
[Unit]
Description=Flask Blog
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/opt/blog
ExecStart=/usr/local/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF

cat > /etc/nginx/conf.d/blog.conf << 'NGXEOF'
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $$host;
        proxy_set_header X-Real-IP $$remote_addr;
    }
}
NGXEOF

rm -f /etc/nginx/conf.d/default.conf

cat > /etc/nginx/nginx.conf << 'NGINXEOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;

include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;
    include /etc/nginx/conf.d/*.conf;
}
NGINXEOF
chown -R ec2-user:ec2-user /opt/blog

systemctl daemon-reload
systemctl enable blog
systemctl start blog
systemctl enable nginx
systemctl start nginx
