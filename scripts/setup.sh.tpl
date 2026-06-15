#!/bin/bash
set -e

yum install -y python3 python3-pip
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
User=root
WorkingDirectory=/opt/blog
ExecStart=/usr/local/bin/gunicorn -w 2 -b 0.0.0.0:80 app:app
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable blog
systemctl start blog
