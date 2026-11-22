#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "Run this script as root." >&2
  exit 1
fi

version="2.338.2"
archive="actions-runner-linux-x64-${version}.tar.gz"
checksum="baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40"

install -d -o actions -g actions /opt/actions-runner
cd /opt/actions-runner

if [[ -f .runner ]]; then
  echo "Runner is already configured; installation stopped." >&2
  exit 1
fi

sudo -u actions curl \
  --fail --location --show-error \
  --retry 5 \
  --connect-timeout 10 \
  "https://github.com/actions/runner/releases/download/v${version}/${archive}" \
  -o "$archive"

printf '%s  %s\n' "$checksum" "$archive" | sha256sum --check -

sudo -u actions tar -xzf "$archive"
rm "$archive"

./bin/installdependencies.sh

mkdir -p /etc/needrestart/conf.d

cat > /etc/needrestart/conf.d/actions_runner_services.conf <<'CONF'
$nrconf{override_rc}{qr(^actions\.runner\..+\.service$)} = 0;
CONF

echo "Runner application installed."
