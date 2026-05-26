#!/usr/bin/env bash
# install.sh — Cài đặt SEO Audit MCP Plugin một lệnh (hoàn toàn tự động)
# Dùng: bash <(curl -sSL https://github.com/minhdo01011990-glitch/seo-audit-plugin/raw/main/install.sh)
set -euo pipefail

REPO="minhdo01011990-glitch/seo-audit-plugin"
PLUGIN_FILE="seo-audit.plugin"
PLUGIN_ID="plugin_seo_audit_mcp"
REPORT_DIR="$HOME/Documents/SEO Audit Reports"
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
CLAUDE_DATA="$HOME/Library/Application Support/Claude"

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

BINARY=""
SCRIPTS_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || echo "")
if [[ -n "$SCRIPTS_DIR" && -f "$SCRIPTS_DIR/seo-audit-mcp" ]]; then
    BINARY="$SCRIPTS_DIR/seo-audit-mcp"
fi
if [[ -z "$BINARY" ]]; then
    USER_BIN=$(python3 -m site --user-base 2>/dev/null)/bin
    [[ -f "$USER_BIN/seo-audit-mcp" ]] && BINARY="$USER_BIN/seo-audit-mcp"
fi
if [[ -z "$BINARY" ]]; then
    BINARY=$(which seo-audit-mcp 2>/dev/null || echo "seo-audit-mcp")
fi
info "Binary: $BINARY"

# ── Bước 3: Cấu hình MCP server ──────────────────────────────────────────────
step "3/4 Cấu hình MCP server trong Claude Desktop..."

mkdir -p "$(dirname "$CONFIG_PATH")" "$REPORT_DIR"

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

# ── Bước 4: Cài đặt Cowork plugin tự động ────────────────────────────────────
step "4/4 Cài đặt Cowork plugin..."

RELEASE_URL="https://github.com/$REPO/releases/latest/download/$PLUGIN_FILE"
TMP_PLUGIN=$(mktemp /tmp/seo-audit-XXXXXX.plugin)

if ! curl -fsSL "$RELEASE_URL" -o "$TMP_PLUGIN" 2>/dev/null; then
    warn "Không tải được plugin từ GitHub"
    rm -f "$TMP_PLUGIN"
    TMP_PLUGIN=""
fi

# Tìm tất cả rpm/manifest.json trong dữ liệu Claude Desktop
RPM_MANIFESTS=()
while IFS= read -r -d '' f; do
    RPM_MANIFESTS+=("$f")
done < <(find "$CLAUDE_DATA/local-agent-mode-sessions" -name "manifest.json" -path "*/rpm/manifest.json" -print0 2>/dev/null)

PLUGIN_INSTALLED=false

if [[ ${#RPM_MANIFESTS[@]} -gt 0 && -n "$TMP_PLUGIN" ]]; then
    for MANIFEST in "${RPM_MANIFESTS[@]}"; do
        RPM_DIR=$(dirname "$MANIFEST")
        PLUGIN_TARGET="$RPM_DIR/$PLUGIN_ID"

        # Giải nén plugin vào thư mục plugin_seo_audit_mcp/
        rm -rf "$PLUGIN_TARGET"
        mkdir -p "$PLUGIN_TARGET"
        unzip -q -o "$TMP_PLUGIN" -d "$PLUGIN_TARGET"

        # Cập nhật manifest.json
        python3 - <<PYEOF
import json
from pathlib import Path
from datetime import datetime, timezone

manifest_path = Path("""$MANIFEST""")
try:
    manifest = json.loads(manifest_path.read_text())
except Exception:
    manifest = {}

manifest.setdefault("plugins", [])
# Xóa entry cũ nếu đã tồn tại
manifest["plugins"] = [p for p in manifest["plugins"] if p.get("id") != """$PLUGIN_ID"""]
# Thêm entry mới
manifest["plugins"].append({
    "id": """$PLUGIN_ID""",
    "name": "seo-audit",
    "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
    "marketplaceId": "local_install",
    "marketplaceName": "Local Install",
    "installedBy": "user",
    "installationPreference": "available"
})
manifest["lastUpdated"] = int(datetime.now().timestamp() * 1000)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print(f"  → Đã cập nhật: $MANIFEST")
PYEOF

        PLUGIN_INSTALLED=true
        echo "  Đã cài plugin vào: $RPM_DIR"
    done

    info "Cowork plugin đã cài đặt tự động"
else
    # Fallback: tải về Desktop để upload thủ công
    if [[ -n "$TMP_PLUGIN" ]]; then
        PLUGIN_DEST="$HOME/Desktop/$PLUGIN_FILE"
        cp "$TMP_PLUGIN" "$PLUGIN_DEST"
        warn "Không tìm thấy thư mục Cowork — cần upload thủ công:"
        echo "  Claude Desktop → Cowork → Settings → Plugins → Upload Plugin"
        echo "  Chọn file: $PLUGIN_DEST"
    else
        warn "Không tải được plugin. Tải thủ công tại: https://github.com/$REPO/releases"
    fi
fi

[[ -n "$TMP_PLUGIN" ]] && rm -f "$TMP_PLUGIN"

# ── Khởi động lại Claude Desktop ─────────────────────────────────────────────
if [[ "$PLUGIN_INSTALLED" == "true" ]]; then
    step "Khởi động lại Claude Desktop..."
    if pgrep -x "Claude" &>/dev/null; then
        osascript -e 'tell application "Claude" to quit' 2>/dev/null || killall "Claude" 2>/dev/null || true
        sleep 3
    fi
    open -a "Claude" 2>/dev/null || warn "Không thể tự mở Claude Desktop — hãy mở thủ công"
    info "Claude Desktop đã restart"
fi

# ── Hoàn tất ──────────────────────────────────────────────────────────────────
divider
echo -e "${BOLD}${GREEN}  Cài đặt hoàn tất!${RESET}"
divider
echo ""

if [[ "$PLUGIN_INSTALLED" == "true" ]]; then
    echo -e "${BOLD}Mọi thứ đã tự động. Dùng ngay:${RESET}"
    echo ""
    echo "  1. Trong Claude Desktop → Cowork, gõ: /onpage"
    echo "  2. Claude sẽ hỏi domain cần audit và bắt đầu phân tích"
else
    echo -e "${BOLD}Bước còn lại (30 giây):${RESET}"
    echo "  1. Mở Claude Desktop → Cowork → Settings → Plugins → Upload Plugin"
    echo "  2. Restart Claude Desktop"
    echo "  3. Gõ: /onpage"
fi

echo ""
echo -e "  💡 Thêm PageSpeed API key (tùy chọn, miễn phí):"
echo "     Sửa: $CONFIG_PATH"
echo "     Thêm PAGESPEED_API_KEY vào env của seo-audit"
echo ""
divider
