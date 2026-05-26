#!/usr/bin/env bash
# install.sh — Cài đặt SEO Audit MCP Plugin
# Dùng: bash <(curl -sSL https://github.com/minhdo01011990-glitch/seo-audit-plugin/raw/main/install.sh)
set -euo pipefail

BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; RESET="\033[0m"

# Kiểm tra Python 3.11+
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ Python 3 không tìm thấy. Cài đặt tại https://python.org/downloads/${RESET}"
    exit 1
fi
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 11 ]]; then
    echo -e "${RED}❌ Cần Python 3.11+, hiện có Python $PY_MAJOR.$PY_MINOR${RESET}"
    exit 1
fi

echo -e "${BOLD}Cài đặt seo-audit-mcp từ PyPI...${RESET}"
pip3 install --quiet --upgrade seo-audit-mcp

echo -e "${BOLD}Chạy installer...${RESET}"
seo-audit-mcp-install
