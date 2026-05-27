# SEO Audit MCP Plugin

Phân tích website theo **105+ tiêu chí Technical SEO + UI** thông qua 4 agent tuần tự.  
Chạy trên **Claude Desktop App** — hỗ trợ lệnh `/onpage` trong Cowork.  
Xuất báo cáo dạng **Markdown · Excel · Word** theo lựa chọn.

---

## Cài Đặt

### Bước 1 — Chạy 1 lệnh terminal

```bash
bash <(curl -sSL https://raw.githubusercontent.com/minhdo01011990-glitch/seo-audit-plugin/main/install.sh)
```

Script tự động:
1. Phát hiện Python 3.11+ và cài `seo-audit-mcp` từ PyPI
2. Cấu hình MCP server vào `claude_desktop_config.json` (Claude Desktop)
3. Cấu hình MCP server vào `~/.claude/settings.json` (Claude Code CLI)
4. Cài plugin files vào `~/.local/share/seo-audit-mcp/plugin/`
5. Thêm shell function vào `~/.zshrc` / `~/.bashrc` để tự load `--plugin-dir`
6. Restart Claude Desktop (macOS)

### Bước 2 — Upload plugin vào Cowork (1 lần duy nhất)

1. Tải file [`seo-audit.plugin`](https://github.com/minhdo01011990-glitch/seo-audit-plugin/releases/latest) từ trang Releases
2. Mở Claude Desktop → **Cowork → Settings → Plugins → Upload** → chọn file vừa tải

Sau bước này, gõ `/onpage` trong Cowork là dùng được.

---

## Yêu Cầu

- Python **3.11+** ([tải tại đây](https://python.org/downloads/))
- Claude Desktop App (Mac hoặc Windows)
- Google PageSpeed Insights API key — tùy chọn, miễn phí ([lấy tại đây](https://console.cloud.google.com/))

---

## Sử Dụng

Trong Claude Desktop → Cowork, gõ:

```
/onpage
```

Claude hiển thị bảng nhập thông tin một lần:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 THÔNG TIN CƠ BẢN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Domain                :
Thương hiệu & ngành   :
Mục đích audit        : [ ] Audit toàn diện  [ ] Kiểm tra nhanh  ...
Ngôn ngữ báo cáo      : [ ] Tiếng Việt  [ ] English

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DỮ LIỆU BỔ SUNG  (bỏ qua nếu không có)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Screaming Frog CSV    :
GSC Coverage CSV      :
PageSpeed API Key     :

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TÙY CHỌN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nhóm tiêu chí ưu tiên : [ ] Tất cả  (hoặc chọn nhóm: I II III ...)
Kèm đề xuất xử lý    : [ ] Có  [ ] Không

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Thư mục lưu báo cáo  : (để trống = ~/Documents/SEO Audit Reports)
Định dạng output     : [ ] Markdown (.md)  [ ] Excel (.xlsx)  [ ] Word (.docx)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Điền xong → gửi một lần → Claude tự động crawl ~15 trang, kiểm tra 105+ tiêu chí, xuất báo cáo.

---

## Cập Nhật Lên Phiên Bản Mới

### Bước 1 — Cập nhật MCP server

```bash
bash <(curl -sSL https://raw.githubusercontent.com/minhdo01011990-glitch/seo-audit-plugin/main/install.sh)
```

### Bước 2 — Cập nhật plugin Cowork

*(Chỉ cần khi SKILL.md thay đổi — xem Release Notes để biết)*

1. Tải `seo-audit.plugin` mới từ [Releases](https://github.com/minhdo01011990-glitch/seo-audit-plugin/releases/latest)
2. Cowork → Settings → Plugins → **xóa plugin cũ** → **Upload** file mới

---

## Dữ Liệu Bổ Sung (tùy chọn)

Cung cấp export file khi chạy `/onpage` để tăng độ chính xác:

| File | Cách lấy | Tác dụng |
|------|----------|---------|
| Screaming Frog CSV | Export → All Crawl Data | Phát hiện duplicate title, broken links, missing meta toàn site |
| GSC Performance CSV | Search Console → Performance → Export | Top queries, CTR, vị trí từ khóa |
| GSC Coverage CSV | Search Console → Coverage → Export | Trang bị excluded, lỗi index |
| Ahrefs CSV | Site Audit → Issues → Export | Broken backlinks, redirect chains |

---

## MCP Tools

| Tool | Mô tả |
|------|-------|
| `seo_collect_input` | Lưu config audit session (domain, format, output dir...) |
| `seo_crawl_page` | Crawl 1 URL, trả về 50+ SEO fields |
| `seo_check_robots` | Phân tích robots.txt + llms.txt |
| `seo_check_sitemap` | Validate sitemap.xml, đếm URLs |
| `seo_check_pagespeed` | Google PageSpeed Insights API v5 |
| `seo_parse_screaming_frog` | Parse CSV export từ Screaming Frog |
| `seo_parse_gsc_data` | Parse GSC Coverage/Performance CSV |
| `seo_get_checklist` | Trả về toàn bộ 105+ checklist |
| `seo_check_url_batch` | Check status code hàng loạt URL |
| `seo_save_report` | Render và lưu báo cáo (md / xlsx / docx) |

---

## Hệ Thống Điểm

| Priority | Điểm | Status | Hệ số |
|----------|------|--------|-------|
| mandatory | 3 | passed | 100% |
| high | 2 | warning | 50% |
| nicetohave | 1 | failed | 0% |
| — | — | manual | bỏ qua |

**Grade:** A (≥90%) · B (≥75%) · C (≥60%) · D (≥40%) · F (<40%)

---

## Kiến Trúc

```
mcp_server/
├── server.py                  # MCP server entry point (stdio)
├── templates/                 # Jinja2 report template (.md)
├── tools/
│   ├── crawler.py             # Async crawl, 50+ SEO fields/trang
│   ├── technical_checks.py    # robots.txt, sitemap, redirect chain
│   ├── pagespeed.py           # Google PageSpeed Insights API v5
│   └── file_parsers.py        # Screaming Frog / GSC / Ahrefs CSV
├── checklist/
│   ├── technical.py           # 73 tiêu chí Technical (14 nhóm)
│   └── ui.py                  # 113 tiêu chí UI (10 loại trang)
├── analyzer/
│   └── scorer.py              # Scoring engine + grade
└── plugin_data/
    ├── skills/onpage/SKILL.md # Định nghĩa slash command /onpage
    ├── claude_plugin/         # Plugin manifest
    └── mcp.json
```

---

## Debug MCP Server

```bash
source mcp_server/.venv/bin/activate
python mcp_server/server.py
# Gõ JSON-RPC request thủ công để test từng tool
```

---

## License

MIT
