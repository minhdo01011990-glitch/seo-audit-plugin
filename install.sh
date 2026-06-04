#!/usr/bin/env bash
# install.sh — Cài đặt SEO Audit MCP Plugin
# Dùng: bash <(curl -sSL https://github.com/minhdo01011990-glitch/seo-audit-plugin/raw/main/install.sh)
set -euo pipefail

BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"; RESET="\033[0m"

echo -e "${BOLD}Cài đặt seo-audit-mcp từ PyPI...${RESET}"

# ── Ưu tiên uv tool install (tránh lỗi pip trên Homebrew Python) ──────────────
if command -v uv &>/dev/null; then
    echo -e "  Dùng: uv tool install"
    uv tool install --upgrade seo-audit-mcp
    SEO_INSTALL_BIN="$(uv tool dir)/seo-audit-mcp/bin/seo-audit-mcp-install"
    # Fallback: uv để script vào PATH user
    if [[ ! -x "$SEO_INSTALL_BIN" ]]; then
        SEO_INSTALL_BIN="seo-audit-mcp-install"
    fi

# ── Fallback: pip trên Python 3.11+ ───────────────────────────────────────────
else
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
        echo -e "${RED}❌ Không tìm thấy Python 3.11+ hoặc uv.${RESET}"
        echo "   Cài uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   Hoặc cài Python 3.11+: https://python.org/downloads/"
        exit 1
    fi

    echo -e "  Dùng: $PYTHON -m pip"
    "$PYTHON" -m pip install --quiet --upgrade seo-audit-mcp

    SCRIPTS_DIR=$("$PYTHON" -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || echo "")
    USER_BIN=$("$PYTHON" -m site --user-base 2>/dev/null || echo "")/bin
    SEO_INSTALL_BIN="${SCRIPTS_DIR}/seo-audit-mcp-install"
    if [[ ! -x "$SEO_INSTALL_BIN" ]]; then
        SEO_INSTALL_BIN="${USER_BIN}/seo-audit-mcp-install"
    fi
    if [[ ! -x "$SEO_INSTALL_BIN" ]]; then
        SEO_INSTALL_BIN="seo-audit-mcp-install"
    fi
fi

echo -e "${BOLD}Chạy installer...${RESET}"
"$SEO_INSTALL_BIN"
