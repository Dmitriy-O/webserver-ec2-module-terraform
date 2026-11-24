#!/bin/bash
set -Eeuo pipefail

exec > >(tee -a /var/log/week11-db-bootstrap.log /dev/console) 2>&1
trap 'echo MARIADB_BOOTSTRAP_FAILED >&2' ERR

export DEBIAN_FRONTEND=noninteractive

apt-get -o Acquire::Retries=5 -o APT::Update::Error-Mode=any update
apt-get -o Acquire::Retries=5 -o DPkg::Lock::Timeout=300 install -y mariadb-server

systemctl enable --now mariadb
systemctl is-active --quiet mariadb

result="$(mariadb --batch --skip-column-names -e 'SELECT 1;')"
[[ "$result" == "1" ]]

echo MARIADB_BOOTSTRAP_READY
