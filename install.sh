#!/usr/bin/env bash
# install.sh — Cài đặt SEO Audit MCP Plugin một lệnh
# Dùng: bash <(curl -sSL https://github.com/minhdo01011990-glitch/seo-audit-plugin/raw/main/install.sh)
set -euo pipefail

REPO="minhdo01011990-glitch/seo-audit-plugin"
PLUGIN_FILE="seo-audit.plugin"
REPORT_DIR="$HOME/Documents/SEO Audit Reports"
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# ── Màu in ra terminal ────────────────────────────────────────────────────────
BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; RESET="\033[0m"
info()    { echo -e "${BOLD}${GREEN}✅ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${RESET}"; }
step()    { echo -e "\n${BOLD}$*${RESET}"; }
divider() { echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"; }

divider
echo -e "${BOLD}  SEO Audit MCP Plugin — Installer${RESET}"
divider

# ── Bước 1: Kiểm tra Python ───────────────────────────────────────────────────
step "1/4 Kiểm tra Python..."

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ Python 3 không tìm thấy. Cài đặt tại https://python.org/downloads/${RESET}"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 11 ]]; then
    echo -e "${RED}❌ Cần Python 3.11+, hiện có Python $PY_VER${RESET}"
    exit 1
fi
info "Python $PY_VER"

# ── Bước 2: Cài đặt Python package ───────────────────────────────────────────
step "2/4 Cài đặt seo-audit-mcp từ PyPI..."

pip3 install --quiet --upgrade seo-audit-mcp
info "seo-audit-mcp đã cài đặt"

# Tìm đường dẫn binary vừa cài
BINARY=""
SCRIPTS_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || echo "")
if [[ -n "$SCRIPTS_DIR" && -f "$SCRIPTS_DIR/seo-audit-mcp" ]]; then
    BINARY="$SCRIPTS_DIR/seo-audit-mcp"
fi

# Fallback: user scripts directory
if [[ -z "$BINARY" ]]; then
    USER_BIN=$(python3 -m site --user-base 2>/dev/null)/bin
    if [[ -f "$USER_BIN/seo-audit-mcp" ]]; then
        BINARY="$USER_BIN/seo-audit-mcp"
    fi
fi

# Fallback: which
if [[ -z "$BINARY" ]]; then
    BINARY=$(which seo-audit-mcp 2>/dev/null || echo "")
fi

if [[ -z "$BINARY" ]]; then
    warn "Không tìm thấy binary path tự động. Sẽ dùng 'seo-audit-mcp' (cần có trong PATH)"
    BINARY="seo-audit-mcp"
fi
info "Binary: $BINARY"

# ── Bước 3: Cấu hình claude_desktop_config.json ───────────────────────────────
step "3/4 Cấu hình MCP server trong Claude Desktop..."

mkdir -p "$(dirname "$CONFIG_PATH")"
mkdir -p "$REPORT_DIR"

python3 - <<PYEOF
import json
from pathlib import Path

config_path = Path("""$CONFIG_PATH""")
config = {}
if config_path.exists():
    try:
        config = json.loads(config_path.read_text())
    except Exception:
        pass

config.setdefault("mcpServers", {})["seo-audit"] = {
    "command": """$BINARY""",
    "env": {
        "PAGESPEED_API_KEY": "",
        "REPORT_OUTPUT_DIR": """$REPORT_DIR"""
    }
}

config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
print("  → claude_desktop_config.json đã cập nhật")
PYEOF

info "MCP server đã đăng ký"
echo "  Báo cáo sẽ lưu tại: $REPORT_DIR"

# ── Bước 4: Tải Cowork plugin ─────────────────────────────────────────────────
step "4/4 Tải Cowork plugin..."

PLUGIN_DEST="$HOME/Desktop/$PLUGIN_FILE"
RELEASE_URL="https://github.com/$REPO/releases/latest/download/$PLUGIN_FILE"

if curl -fsSL "$RELEASE_URL" -o "$PLUGIN_DEST" 2>/dev/null; then
    info "Plugin đã tải: $PLUGIN_DEST"
else
    warn "Không tải được plugin tự động (có thể chưa có release trên GitHub)"
    echo "  Tải thủ công tại: https://github.com/$REPO/releases"
    PLUGIN_DEST=""
fi

# ── Hoàn tất ──────────────────────────────────────────────────────────────────
divider
echo -e "${BOLD}${GREEN}  Cài đặt hoàn tất!${RESET}"
divider
echo ""
echo -e "${BOLD}Bước cuối (thủ công — 30 giây):${RESET}"
echo ""
echo "  1. Mở Claude Desktop → Cowork"
echo "  2. Settings → Plugins → Upload Plugin"
if [[ -n "$PLUGIN_DEST" ]]; then
echo "  3. Chọn file: $PLUGIN_DEST"
else
echo "  3. Chọn file seo-audit.plugin đã tải từ GitHub"
fi
echo ""
echo "  4. Restart Claude Desktop App"
echo "  5. Trong Cowork, gõ: /onpage"
echo ""
echo -e "  💡 Để thêm PageSpeed API key (tùy chọn, miễn phí):"
echo "     Sửa file: $CONFIG_PATH"
echo "     Thêm PAGESPEED_API_KEY trong phần env của seo-audit"
echo ""
divider
