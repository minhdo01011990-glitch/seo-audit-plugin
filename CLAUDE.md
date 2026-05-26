# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tổng Quan

Đây là **MCP plugin** chạy trên **Claude Desktop App** (không phải Claude Code). Người dùng tạo một Project trong Claude Desktop, paste nội dung `project_instructions.md` vào Project Instructions, rồi gõ yêu cầu audit trong cuộc hội thoại để bắt đầu. Claude Desktop tự spawn MCP server và gọi các tools.

## Setup & Cài Đặt

```bash
chmod +x setup.sh && ./setup.sh
```

Tạo `mcp_server/.venv` và cài dependencies. Tạo `.env` từ `.env.example` nếu chưa có.

MCP server đăng ký trong `~/Library/Application Support/Claude/claude_desktop_config.json` — Claude Desktop tự spawn, không chạy thủ công.

## Test Server Khi Debug

```bash
source mcp_server/.venv/bin/activate
python mcp_server/server.py
# Gõ JSON-RPC request thủ công để test từng tool
```

## Kiến Trúc

**MCP Server** (`mcp_server/server.py`) — Python stdio transport. Claude Desktop spawn khi khởi động app. Session state lưu trong `_audit_config` (in-memory dict, reset mỗi lần server restart). Tools khai báo trong `list_tools()`, dispatch trong `_dispatch()`.

**Project Instructions** (`project_instructions.md`) — System prompt paste vào Claude Desktop Project. Hướng dẫn Claude thực hiện 4 agent phases, gọi MCP tools và tổng hợp kết quả.

### Luồng Dữ Liệu

```
Người dùng: "audit website X"
  → Agent 1: hỏi 8 câu → seo_collect_input
  → Agent 2: crawl 15 trang + robots + sitemap
             → seo_crawl_page, seo_check_robots, seo_check_sitemap,
               seo_check_url_batch, seo_check_pagespeed
  → Agent 3: map crawl data → checklist → seo_get_checklist
  → Agent 4: render + lưu → seo_save_report → reports/{domain}_{timestamp}.md
```

### Cấu Trúc Dữ Liệu Chính

- **`ChecklistItem`** (`checklist/technical.py`) — 73 tiêu chí Technical, 14 nhóm. Fields: `id`, `name`, `category`, `priority` (mandatory/high/nicetohave), `check_method` (auto/manual/api).

- **`UIChecklistItem`** (`checklist/ui.py`) — 113 tiêu chí UI, 10 loại trang. Thêm: `check_mode` (auto/manual), `crawl_field` (tên field trong kết quả `crawl_page`), `manual_guide`.

- **`ChecklistResult`** (`analyzer/scorer.py`) — Kết quả sau khi map dữ liệu crawl vào 1 checklist item. Fields: `status` (passed/failed/warning/manual), `evidence`, `recommendation`.

- **`crawl_page` return dict** (`tools/crawler.py`) — 50+ fields gồm `header_has_*`, `footer_has_*`, `has_*` boolean map trực tiếp vào `crawl_field` của UI checklist.

### Hệ Thống Điểm

`mandatory=3pt · high=2pt · nicetohave=1pt` × `passed=100% · warning=50% · failed=0%` — `manual` bỏ qua khi tính. Grade: A≥90 · B≥75 · C≥60 · D≥40 · F<40.

### Sinh Báo Cáo

`seo_save_report` render `templates/report_template.md` qua Jinja2. Fallback sang `_build_fallback_report()` nếu template lỗi. Output: `./reports/seo_report_{domain}_{timestamp}.md`.

## Thêm / Sửa Checklist

- **Technical**: thêm `ChecklistItem(...)` vào `TECHNICAL_CHECKLIST` trong `checklist/technical.py`
- **UI auto**: `check_mode="auto"` + `crawl_field=` tên field trong kết quả `crawl_page()`
- **UI manual**: `check_mode="manual"` + `manual_guide=` hướng dẫn kiểm tra thủ công

Nếu thêm crawl field mới: thêm logic trích xuất vào `crawl_page()` trong `tools/crawler.py`, sau đó dùng field đó trong `crawl_field` của checklist item tương ứng.

## Lưu Ý Import

`server.py` insert thư mục gốc vào `sys.path` để `from mcp_server.tools...` hoạt động khi chạy trực tiếp. Không xóa dòng này.
