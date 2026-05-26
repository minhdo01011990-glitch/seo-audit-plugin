# SEO Audit — Cowork Plugin

Plugin phân tích SEO website theo **105+ tiêu chí Technical + UI** cho Claude Desktop App (Cowork tab).

## Yêu Cầu

- Python 3.11+
- Claude Desktop App (Mac hoặc Windows)
- MCP server đã được cài đặt (xem hướng dẫn bên dưới)

## Cài Đặt

### Bước 1: Cài đặt MCP server

```bash
cd "/Users/maytinh/SEO Audit"
chmod +x setup.sh
./setup.sh
```

### Bước 2: Đăng ký MCP server với Claude Desktop

Thêm vào `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "seo-audit": {
      "command": "/Users/maytinh/SEO Audit/mcp_server/.venv/bin/python",
      "args": ["/Users/maytinh/SEO Audit/mcp_server/server.py"],
      "env": {
        "PAGESPEED_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Restart Claude Desktop App sau khi lưu.

### Bước 3: Tạo file plugin

```bash
cd "/Users/maytinh/SEO Audit"
chmod +x package-plugin.sh
./package-plugin.sh
```

File `seo-audit.plugin` sẽ được tạo tại thư mục gốc.

### Bước 4: Cài plugin vào Cowork

1. Mở Claude Desktop App → tab **Cowork**
2. Mở **Settings** → **Plugins**
3. Chọn **Upload Plugin** và chọn file `seo-audit.plugin`
4. Sau khi cài xong, skill `/seo-audit` sẽ xuất hiện trong Cowork

## Sử Dụng

Trong tab Cowork, gõ:

```
audit website example.com
```

hoặc

```
phân tích SEO cho https://example.com
```

Claude sẽ tự động kích hoạt skill SEO Audit và hỏi tuần tự 8 câu thông tin.

## Tính Năng

- Crawl ~15 trang đại diện của website
- Kiểm tra robots.txt, sitemap, redirect chain
- Tích hợp Google PageSpeed Insights API (tùy chọn)
- Phân tích theo 73 tiêu chí Technical (14 nhóm) + 113 tiêu chí UI (10 loại trang)
- Hệ thống điểm: A/B/C/D/F với priority weighting
- Xuất báo cáo `.md` vào thư mục `reports/`
- Hỗ trợ import dữ liệu từ Screaming Frog, Google Search Console, Ahrefs
