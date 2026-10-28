#!/bin/zsh
cd "$(dirname "$0")/stage1" || exit 1
export SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/ssl/cert.pem}"
export REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-/etc/ssl/cert.pem}"
exec .venv/bin/python server.py --env-file /Users/viroksharma/Desktop/Orbi/mvp-v2/.env.local
