#!/bin/bash
set -e

yum install -y docker
systemctl start docker
systemctl enable docker

aws ecr get-login-password --region ${region} | \
  docker login --username AWS --password-stdin ${ecr_url}

docker pull ${ecr_url}:latest

cat > /etc/systemd/system/blog.service << 'SVCEOF'
[Unit]
Description=Flask Blog
After=docker.service
Requires=docker.service

[Service]
Restart=always
ExecStartPre=-/usr/bin/docker stop blog
ExecStartPre=-/usr/bin/docker rm blog
ExecStart=/usr/bin/docker run --name blog \
  -p 80:80 \
  -e DB_HOST=${db_host} \
  -e DB_NAME=${db_name} \
  -e DB_USER=${db_user} \
  -e DB_PASSWORD=${db_password} \
  ${ecr_url}:latest

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable blog
systemctl start blog
