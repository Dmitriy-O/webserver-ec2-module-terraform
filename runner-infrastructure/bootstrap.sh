#!/usr/bin/env bash
set -Eeuo pipefail

exec > >(tee -a /var/log/week12-runner-bootstrap.log) 2>&1
trap 'echo "Bootstrap failed on line ${LINENO}" >&2' ERR

export DEBIAN_FRONTEND=noninteractive

# Runner swap for memory-limited instances
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
fi

if ! swapon --show=NAME --noheadings | grep -qx /swapfile; then
  swapon /swapfile
fi

if ! grep -q '^/swapfile ' /etc/fstab; then
  printf '/swapfile none swap sw 0 0\n' >> /etc/fstab
fi

apt-get -o Acquire::Retries=5 update

apt-get -o DPkg::Lock::Timeout=180 install -y \
  ca-certificates \
  curl \
  git \
  jq \
  unzip \
  build-essential

install_dir=$(mktemp -d)

curl --fail --silent --show-error \
  --retry 5 \
  --connect-timeout 10 \
  --max-time 300 \
  https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
  -o "$install_dir/awscliv2.zip"

unzip -q "$install_dir/awscliv2.zip" -d "$install_dir"
"$install_dir/aws/install" --update
rm -rf "$install_dir"

if ! id actions >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash actions
fi

install -d -o actions -g actions /opt/actions-runner

aws --version
git --version

echo "Runner host bootstrap completed."
