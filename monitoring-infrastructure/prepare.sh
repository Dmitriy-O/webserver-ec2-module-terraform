#!/bin/bash
set -Eeuo pipefail

cd "$(dirname "$0")"
umask 077

if [[ -e terraform.tfvars ]]; then
  echo "terraform.tfvars already exists. Review it instead of overwriting it." >&2
  exit 1
fi

mkdir -p "$HOME/.ssh"

key_path="$HOME/.ssh/week13-monitoring"

if [[ -e "$key_path" || -e "$key_path.pub" ]]; then
  if [[ ! -f "$key_path" || ! -f "$key_path.pub" ]]; then
    echo "Incomplete SSH key pair at $key_path; resolve before continuing." >&2
    exit 1
  fi
else
  ssh-keygen \
    -t ed25519 \
    -f "$key_path" \
    -N "" \
    -C "week13-monitoring"
fi

admin_ip="$(
  curl \
    -4 \
    --fail \
    --silent \
    --show-error \
    --connect-timeout 10 \
    --max-time 20 \
    https://checkip.amazonaws.com
)"

if [[ ! "$admin_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Could not determine public IPv4 address." >&2
  exit 1
fi

cat > terraform.tfvars <<EOF
admin_cidr          = "$admin_ip/32"
ssh_public_key_path = "$key_path.pub"
EOF

echo "Prepared terraform.tfvars and the SSH key. No AWS resources were created."
