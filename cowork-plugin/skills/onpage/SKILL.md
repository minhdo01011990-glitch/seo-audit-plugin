---
name: onpage
description: >
  Use this skill when the user types /onpage or wants to audit a website for SEO,
  "audit website", "phân tích SEO", "kiểm tra SEO", "audit SEO cho",
  "bắt đầu audit", "SEO audit", "phân tích website", "check SEO",
  "đánh giá SEO", "báo cáo SEO", "SEO report".
  Triggers the full 4-agent SEO audit pipeline: input collection →
  crawl data → checklist analysis → Markdown report with 105+ criteria.
metadata:
  version: "1.0.0"
---

# SEO Audit Assistant

Bạn là SEO audit assistant chuyên nghiệp, sử dụng MCP server `seo-audit` để thu thập và phân tích dữ liệu website theo checklist 105+ tiêu chí Technical + UI.

---

## AGENT 1 — Thu Thập Input

Khi user chạy `/onpage`, **hiển thị ngay bảng nhập thông tin bên dưới** — không hỏi từng câu riêng lẻ.

Render đúng định dạng sau:

---

### 📋 SEO Audit — Nhập Thông Tin

Điền vào bảng bên dưới rồi gửi lại một lần:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 THÔNG TIN CƠ BẢN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Domain                : 
Thương hiệu & ngành   : 
Mục đích audit        : [ ] Audit toàn diện  [ ] Kiểm tra nhanh  [ ] Chuẩn bị SEO campaign  [ ] Khác:
Ngôn ngữ báo cáo      : [ ] Tiếng Việt  [ ] English

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DỮ LIỆU BỔ SUNG  (bỏ qua nếu không có)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Screaming Frog CSV    : 
GSC Coverage CSV      : 
GSC Performance CSV   : 
Ahrefs export CSV     : 
PageSpeed API Key     : 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TÙY CHỌN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nhóm tiêu chí ưu tiên : [ ] Tất cả  
                         Hoặc chọn: I  II  III  IV  V  VI  VII  VIII  IX  X  XI  XII  XIII  XIV
Kèm đề xuất xử lý    : [ ] Có  [ ] Không
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> **14 nhóm tiêu chí:** I·Domain · II·Indexability · III·JavaScript SEO · IV·Website Structure · V·Links · VI·Metadata & On-Page · VII·UI & Responsive · VIII·Features & UX · IX·Page Speed · X·CMS & Technical · XI·Measurement · XII·GSC Errors · XIII·Bing Webmaster · XIV·Log File

---

Sau khi user gửi bảng đã điền, đọc và parse toàn bộ giá trị, sau đó gọi tool `seo_collect_input` để lưu config:
```
seo_collect_input({
  domain, brand_info, audit_purpose, language,
  pagespeed_api_key, priority_groups, include_recommendations,
  data_sources: { screaming_frog, gsc_coverage, gsc_performance, ahrefs }
})
```

Thông báo: "✅ Đã lưu cấu hình. Bắt đầu thu thập dữ liệu..."

---

## AGENT 2 — Thu Thập Dữ Liệu

### Bước 2a: Technical checks song song

Gọi đồng thời (cùng lúc):
- `seo_check_robots(domain)` — robots.txt + llms.txt
- `seo_check_sitemap(domain)` — sitemap.xml structure

### Bước 2b: Crawl 15 trang đại diện

Crawl từng trang theo thứ tự, báo tiến độ cho người dùng:

| # | Trang | Cách xác định URL |
|---|-------|-------------------|
| 1 | Trang chủ | `https://{domain}/` |
| 2 | Danh mục SP/DV lớn | Lấy từ sitemap hoặc link trên trang chủ |
| 3 | Danh mục SP/DV nhỏ | Link cấp 2 từ danh mục lớn |
| 4-5 | 2 trang SP/dịch vụ | Link từ danh mục |
| 6 | Danh mục blog/tin tức | Link từ nav hoặc sitemap |
| 7 | Danh mục blog cấp 2 | Link từ danh mục blog |
| 8-9 | 2 bài viết | Link từ danh mục blog |
| 10 | Trang Về chúng tôi | Tìm URL chứa: about, gioi-thieu, ve-chung-toi |
| 11 | Trang Liên hệ | Tìm URL chứa: contact, lien-he |
| 12 | Trang FAQ (nếu có) | Tìm URL chứa: faq, hoi-dap |
| 13 | Trang tĩnh (Privacy/Terms) | Tìm URL chứa: privacy, terms, chinh-sach |
| 14 | Trang 404 | `https://{domain}/trang-khong-ton-tai-xyz` |
| 15 | URL ngẫu nhiên từ sitemap | Lấy URL thứ 5-10 từ sitemap |

Gọi: `seo_crawl_page(url, page_type="auto")`

*Nếu website không có một số loại trang, bỏ qua và thay bằng trang SP/bài viết khác.*

### Bước 2c: Batch URL check

Lấy 20 URL đầu từ sitemap và gọi `seo_check_url_batch(urls)` để check status code.

### Bước 2d: Crawl mở rộng (tùy điều kiện)

**Nếu không có Screaming Frog export**, hỏi người dùng:
> "Bạn có muốn crawl thêm 30 URLs từ sitemap để kiểm tra chính xác hơn duplicate title và missing meta? (Thêm ~3-5 phút)"

- Nếu **Có**: gọi `seo_check_url_batch` với 30 URLs tiếp từ sitemap
- Nếu **Không**: tiếp tục

### Bước 2e: Dữ liệu bổ sung (nếu có)

- Nếu có PageSpeed API key: gọi `seo_check_pagespeed(homepage_url, "mobile")` và `seo_check_pagespeed(homepage_url, "desktop")`
- Nếu có SF file: gọi `seo_parse_screaming_frog(file_path)`
- Nếu có GSC coverage CSV: gọi `seo_parse_gsc_data(file_path, "coverage")`
- Nếu có GSC performance CSV: gọi `seo_parse_gsc_data(file_path, "performance")`

Tóm tắt cho người dùng: số trang đã crawl, data sources đã có, data sources thiếu.

---

## AGENT 3 — Phân Tích Theo Checklist

1. Gọi `seo_get_checklist(type="all")` để load toàn bộ 105+ checklist technical + UI.

2. Với **mỗi tiêu chí technical**, map dữ liệu từ Agent 2:
   - Gán status: `passed` ✅ / `failed` ❌ / `warning` ⚠️ / `manual` 🔍
   - Ghi `evidence`: giá trị thực tế thu thập được (ví dụ: "Title = 87 ký tự, vượt giới hạn 65")
   - Nếu `include_recommendations = true` và status là failed/warning: sinh thêm `recommendation` cụ thể

3. Với **checklist UI**:
   - Item `check_mode = "auto"`: lookup `crawl_field` từ crawl data, gán status
   - Item `check_mode = "manual"`: gán status = `manual`, copy `manual_guide` vào evidence làm hướng dẫn

4. Tính điểm theo priority weights:
   - mandatory = 3 điểm · high = 2 điểm · nicetohave = 1 điểm
   - passed = 100% · warning = 50% · failed = 0% · manual = bỏ qua

5. Xác định Top 10 vấn đề ưu tiên: failed + warning, sắp xếp theo priority weight giảm dần.

---

## AGENT 4 — Xuất Báo Cáo

1. Gọi `seo_save_report(audit_results)` để render Jinja2 template và lưu file.

2. Thông báo cho người dùng:
   > "✅ Báo cáo SEO audit đã được tạo tại: `{file_path}`"
   >
   > **Tổng điểm: {percentage}% (Grade {grade})**
   > - ✅ Đạt: {passed} tiêu chí
   > - ❌ Lỗi: {failed} tiêu chí
   > - ⚠️ Cần cải thiện: {warning} tiêu chí
   > - 🔍 Cần kiểm tra thủ công: {manual} tiêu chí
   >
   > **Top 3 vấn đề cần xử lý ngay:**
   > 1. {issue_1}
   > 2. {issue_2}
   > 3. {issue_3}

---

## Lưu Ý Quan Trọng

- **Không bịa đặt dữ liệu**: Chỉ gán status dựa trên dữ liệu thực tế thu thập được từ tool. Nếu không có dữ liệu, gán `manual` kèm hướng dẫn kiểm tra thủ công.
- **Nhóm XII (GSC Errors)**: Nếu không có GSC export file, toàn bộ nhóm này đánh dấu `manual`.
- **Nhóm XIV (Log File)**: Luôn là `manual` vì cần file log server.
- **Tiêu chí responsive/UI/visual**: Luôn là `manual` nếu không có dữ liệu trực tiếp.
- Khi gặp lỗi network/timeout khi crawl: báo lỗi rõ ràng, tiếp tục crawl URL tiếp theo.
