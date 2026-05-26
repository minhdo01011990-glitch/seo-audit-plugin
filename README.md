# SEO Audit MCP Plugin

Phân tích website theo **105+ tiêu chí Technical SEO + UI** thông qua 4 agent tuần tự.  
Chạy trên **Claude Desktop App** (Cowork) — hỗ trợ lệnh `/onpage`.

## Cài Đặt (1 lệnh, hoàn toàn tự động)

```bash
bash <(curl -sSL https://github.com/minhdo01011990-glitch/seo-audit-plugin/raw/main/install.sh)
```

Script tự động 100%:
1. Cài `seo-audit-mcp` từ PyPI
2. Cấu hình MCP server vào `claude_desktop_config.json`
3. Cài plugin trực tiếp vào Claude Desktop (không cần upload thủ công)
4. Restart Claude Desktop

Sau khi script chạy xong, mở Cowork và gõ `/onpage` là dùng được ngay.

## Cài Đặt Thủ Công (nếu script báo lỗi)

```bash
# 1. Cài Python package
pip install seo-audit-mcp

# 2. Cấu hình claude_desktop_config.json
# Mở: ~/Library/Application Support/Claude/claude_desktop_config.json
# Thêm vào mcpServers:
{
  "seo-audit": {
    "command": "/path/to/seo-audit-mcp",
    "env": {
      "PAGESPEED_API_KEY": "YOUR_KEY_HERE",
      "REPORT_OUTPUT_DIR": "/Users/you/Documents/SEO Audit Reports"
    }
  }
}

# 3. Tải seo-audit.plugin từ GitHub Releases → upload vào Cowork → Restart
```

## Sử Dụng

Trong Claude Desktop → Cowork, gõ:

```
/onpage
```

Claude hiển thị bảng nhập thông tin → điền domain + các tùy chọn → gửi một lần.  
Claude tự động crawl ~15 trang, kiểm tra 105+ tiêu chí, xuất báo cáo `.md`.

## Yêu Cầu

- Python 3.11+
- Claude Desktop App (Mac hoặc Windows)
- Google PageSpeed Insights API key (tùy chọn, miễn phí — [lấy tại đây](https://console.cloud.google.com/))

## Biến Môi Trường

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `PAGESPEED_API_KEY` | _(trống)_ | Google PageSpeed Insights API v5 |
| `REPORT_OUTPUT_DIR` | `~/Documents/SEO Audit Reports` | Thư mục lưu báo cáo |

## Kiến Trúc

```
mcp_server/
├── server.py                  # MCP server (entry: seo-audit-mcp)
├── templates/                 # Jinja2 report template
├── tools/
│   ├── crawler.py             # Async crawl, 50+ SEO fields
│   ├── technical_checks.py    # robots.txt, sitemap, redirect
│   ├── pagespeed.py           # Google PageSpeed Insights API v5
│   └── file_parsers.py        # Screaming Frog / GSC / Ahrefs CSV
├── checklist/
│   ├── technical.py           # 73 tiêu chí Technical (14 nhóm)
│   └── ui.py                  # 113 tiêu chí UI (10 page types)
└── analyzer/
    └── scorer.py              # mandatory=3 · high=2 · nicetohave=1

cowork-plugin/                 # Cowork plugin package
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json                  # Tham chiếu tới seo-audit-mcp binary
└── skills/onpage/
    └── SKILL.md               # Skill definition cho /onpage command
```

## MCP Tools (10 tools)

| Tool | Mô tả |
|------|-------|
| `seo_collect_input` | Lưu config audit session |
| `seo_crawl_page` | Crawl 1 URL, trả về đầy đủ SEO data |
| `seo_check_robots` | Phân tích robots.txt + llms.txt |
| `seo_check_sitemap` | Validate sitemap.xml |
| `seo_check_pagespeed` | Google PageSpeed Insights API v5 |
| `seo_parse_screaming_frog` | Parse CSV export từ Screaming Frog |
| `seo_parse_gsc_data` | Parse GSC Coverage/Performance CSV |
| `seo_get_checklist` | Trả về toàn bộ 105+ checklist |
| `seo_check_url_batch` | Check status code batch URLs |
| `seo_save_report` | Render và lưu báo cáo .md |

## Dữ Liệu Bổ Sung (tùy chọn)

Khi dùng `/onpage`, có thể cung cấp export file để tăng độ chính xác:

| File | Cách lấy | Tác dụng |
|------|----------|---------|
| Screaming Frog CSV | Export → All Crawl Data | Phát hiện duplicate title, broken links, missing meta toàn site |
| SF Images CSV | Export → Images | Kiểm tra ảnh thiếu alt text |
| GSC Performance CSV | Search Console → Performance → Export | Top queries, CTR, vị trí |
| GSC Coverage CSV | Search Console → Coverage → Export | Trang bị excluded, lỗi index |

## Publish Phiên Bản Mới (dành cho maintainer)

```bash
# Cài build tools (chỉ cần 1 lần)
pip install build twine

# Tạo PyPI token tại: https://pypi.org/manage/account/token/
# Lưu vào ~/.pypirc hoặc export TWINE_PASSWORD=pypi-...

# Publish patch version
bash publish.sh

# Publish minor version
bash publish.sh minor
```

Script `publish.sh` tự động: bump version → build → upload PyPI → git tag → push → tạo GitHub Release.

## Hệ Thống Điểm

- `mandatory` = 3 điểm | `high` = 2 điểm | `nicetohave` = 1 điểm
- `passed` = 100% | `warning` = 50% | `failed` = 0% | `manual` = bỏ qua
- **Grade:** A (≥90%) · B (≥75%) · C (≥60%) · D (≥40%) · F (<40%)

## Debug MCP Server

```bash
source mcp_server/.venv/bin/activate
python mcp_server/server.py
# Gõ JSON-RPC request để test tool cụ thể
```

## License

MIT
