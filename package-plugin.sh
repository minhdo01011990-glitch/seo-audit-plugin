#!/bin/bash
# Đóng gói seo-audit.plugin từ mcp_server/plugin_data/ (nguồn chính thức)
set -e
cd "$(dirname "$0")"

OUTPUT="seo-audit.plugin"
SRC="mcp_server/plugin_data"

rm -f "$OUTPUT"

# Tạo thư mục tạm với đúng tên file (thêm lại dấu chấm)
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

cp "$SRC/mcp.json"                "$TMP/.mcp.json"
cp -r "$SRC/claude_plugin"        "$TMP/.claude-plugin"
cp -r "$SRC/skills"               "$TMP/skills"

cd "$TMP"
zip -r "$OLDPWD/$OUTPUT" . --exclude "*.DS_Store" --exclude "__pycache__/*"

echo "✅ Đã tạo: $OUTPUT"
