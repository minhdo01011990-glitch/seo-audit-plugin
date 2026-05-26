#!/usr/bin/env bash
# install.sh — Cài đặt SEO Audit MCP Plugin
# Dùng: bash <(curl -sSL https://github.com/minhdo01011990-glitch/seo-audit-plugin/raw/main/install.sh)
set -euo pipefail

BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; RESET="\033[0m"

# Tìm Python 3.11+ — thử theo thứ tự ưu tiên để tránh bị dùng system Python cũ
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" &>/dev/null; then
        _major=$("$candidate" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
        _minor=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo 0)
        if [[ "$_major" -eq 3 && "$_minor" -ge 11 ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo -e "${RED}❌ Không tìm thấy Python 3.11+. Cài đặt tại https://python.org/downloads/${RESET}"
    echo "   (python3 --version hiện tại: $(python3 --version 2>/dev/null || echo 'không tìm thấy'))"
    exit 1
fi
echo -e "${BOLD}Python:${RESET} $("$PYTHON" --version)"

# Tìm pip tương ứng với Python vừa chọn
PIP="$PYTHON -m pip"

echo -e "${BOLD}Cài đặt seo-audit-mcp từ PyPI...${RESET}"
$PIP install --quiet --upgrade seo-audit-mcp

echo -e "${BOLD}Chạy installer...${RESET}"
"$($PYTHON -c "import sysconfig; print(sysconfig.get_path('scripts'))")/seo-audit-mcp-install" 2>/dev/null \
    || "$($PYTHON -m site --user-base 2>/dev/null)/bin/seo-audit-mcp-install" 2>/dev/null \
    || seo-audit-mcp-install
