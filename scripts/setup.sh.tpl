#!/bin/bash
set -e

yum install -y python3 python3-pip git
git clone https://github.com/Utkarsh-077/aws-playground.git /opt/blog
pip3 install -r /opt/blog/app/requirements.txt

cat > /etc/systemd/system/blog.service << 'SVCEOF'
[Unit]
Description=Flask Blog
After=network.target

[Service]
User=root
WorkingDirectory=/opt/blog/app
Environment="DB_HOST=${db_host}"
Environment="DB_NAME=${db_name}"
Environment="DB_USER=${db_user}"
Environment="DB_PASSWORD=${db_password}"
ExecStart=/usr/local/bin/gunicorn -w 2 -b 0.0.0.0:80 app:app
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable blog
systemctl start blog
