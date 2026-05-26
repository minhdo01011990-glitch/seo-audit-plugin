#!/bin/bash
set -e

echo "=== SEO Audit MCP Server Setup ==="

# Create virtual environment
python3 -m venv mcp_server/.venv
source mcp_server/.venv/bin/activate

# Install dependencies
pip install --upgrade pip -q
pip install -r mcp_server/requirements.txt

# Create .env from example if not exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Đã tạo .env — vui lòng điền PAGESPEED_API_KEY nếu có"
fi

echo ""
echo "=== Cài đặt hoàn tất ==="
echo ""
echo "Bước tiếp theo: Thêm MCP server vào Claude Code Desktop"
echo "Mở file: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "Thêm đoạn sau vào mcpServers:"
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "seo-audit": {
      "command": "$(pwd)/mcp_server/.venv/bin/python",
      "args": ["$(pwd)/mcp_server/server.py"],
      "env": {
        "PAGESPEED_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
EOF
echo ""
echo "Sau đó restart Claude Code Desktop."
