#!/bin/bash

set -Eeuo pipefail

exec > >(tee -a /var/log/db-bootstrap.log) 2>&1

export DEBIAN_FRONTEND=noninteractive

echo "Starting MariaDB installation"

apt-get \
  -o Acquire::Retries=5 \
  -o APT::Update::Error-Mode=any \
  update

apt-get \
  -o Acquire::Retries=5 \
  install -y mariadb-server

systemctl enable --now mariadb

systemctl is-active --quiet mariadb
mariadb-admin ping --silent

echo "MariaDB installation completed successfully"
