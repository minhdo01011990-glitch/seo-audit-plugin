#!/bin/bash
set -e

cd "$(dirname "$0")"

OUTPUT="seo-audit.plugin"

echo "Đóng gói Cowork plugin..."

# Xóa file cũ nếu có
rm -f "$OUTPUT"

# Tạo zip từ thư mục cowork-plugin (bao gồm hidden files như .claude-plugin và .mcp.json)
cd cowork-plugin
zip -r "../$OUTPUT" . --exclude "*.DS_Store" --exclude "__pycache__/*"
cd ..

echo "✅ Đã tạo: $OUTPUT"
echo ""
echo "Cài đặt:"
echo "  Claude Desktop → Cowork → Settings → Plugins → Upload Plugin → chọn $OUTPUT"
