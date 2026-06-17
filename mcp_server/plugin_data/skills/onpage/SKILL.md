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

## BƯỚC 0 — Load MCP Tools (BẮT BUỘC)

**Làm ngay trước mọi thứ khác** — gọi `ToolSearch` với query `"seo-audit"` (max_results: 15) để load schema của toàn bộ seo-audit tools. Nếu bỏ qua bước này, các tool như `seo_collect_input`, `seo_crawl_page`, v.v. sẽ không khả dụng và audit sẽ thất bại.

Sau khi ToolSearch trả kết quả, xác nhận thấy ít nhất: `seo_collect_input`, `seo_crawl_page`, `seo_save_report` — rồi mới tiếp tục.

---

## AGENT 1 — Thu Thập Input

Khi user chạy `/onpage`, gọi tool `visualize` để hiển thị form nhập thông tin:

**Phần 1 — THÔNG TIN CƠ BẢN:**
- **Domain** (bắt buộc) — `<input type="text">`, placeholder: `example.com`
- **Thương hiệu & ngành** — `<input type="text">`, placeholder: `Hacom — bán lẻ laptop, linh kiện máy tính`
- **Mục đích audit** — `<select>`: `Audit toàn diện` (mặc định), `Kiểm tra nhanh`, `Chuẩn bị SEO campaign`, `Khác`
- **Ngôn ngữ báo cáo** — radio: `Tiếng Việt` (mặc định), `English`

**Phần 2 — DỮ LIỆU BỔ SUNG** (dùng `<details><summary>Mở rộng nếu có file export</summary>` để ẩn gọn):
- **Screaming Frog CSV** — `<input type="text">`, placeholder: `/path/to/screaming_frog.csv`
- **GSC Coverage CSV** — `<input type="text">`, placeholder: `/path/to/gsc_coverage.csv`
- **GSC Performance CSV** — `<input type="text">`, placeholder: `/path/to/gsc_performance.csv`
- **Ahrefs export CSV** — `<input type="text">`, placeholder: `/path/to/ahrefs.csv`
- **PageSpeed API Key** — `<input type="text">`, placeholder: `AIza...`

**Phần 3 — TÙY CHỌN:**
- **Nhóm tiêu chí ưu tiên** — checkbox `Tất cả` (checked mặc định) + 14 checkbox: `I` `II` `III` `IV` `V` `VI` `VII` `VIII` `IX` `X` `XI` `XII` `XIII` `XIV`
  - Tooltip/ghi chú nhỏ: `I·Domain · II·Indexability · III·JS SEO · IV·Structure · V·Links · VI·Metadata · VII·UI · VIII·Features · IX·PageSpeed · X·CMS · XI·Measurement · XII·GSC Errors · XIII·Bing · XIV·Log File`
- **Kèm đề xuất xử lý** — radio: `Có` (mặc định), `Không`

**Phần 4 — OUTPUT:**
- **Thư mục lưu báo cáo** — `<input type="text">`, placeholder: `~/Claude/SEO Reports`
- **Định dạng output** — radio: `Markdown (.md)` (mặc định), `Excel (.xlsx)`, `Word (.docx)`

**Phần 5 — LƯU Ý / YÊU CẦU ĐẶC BIỆT** (tùy chọn):
- **Lưu ý** — `<textarea rows="3">`, placeholder: `Ví dụ: chỉ audit mobile, website thời trang, báo cáo ngắn gọn...`

Nút **"Bắt đầu Audit →"** để submit.

---

Sau khi user gửi bảng đã điền, đọc và parse toàn bộ giá trị, sau đó gọi tool `seo_collect_input` để lưu config:
```
seo_collect_input({
  domain, brand_info, audit_purpose, language,
  pagespeed_api_key, priority_groups, include_recommendations,
  data_sources: { screaming_frog, gsc_coverage, gsc_performance, ahrefs },
  output_dir,      // thư mục lưu báo cáo (chuỗi path, hoặc "" nếu để trống)
  output_format,   // "md" | "xlsx" | "docx"
  notes,           // nội dung ô "Lưu ý / Yêu cầu đặc biệt" (hoặc "" nếu để trống)
})
```

Nếu trường **Lưu ý** không trống, đọc kỹ và điều chỉnh các bước tiếp theo cho phù hợp. Ví dụ:
- "chỉ audit kỹ phần mobile" → ưu tiên checklist UI responsive, ghi chú trong báo cáo
- "website bán hàng thời trang" → chú ý hơn vào Product schema, hình ảnh, giá
- "chỉ cần kiểm tra technical, bỏ qua UI" → bỏ qua toàn bộ UI checklist
- "báo cáo ngắn gọn, không cần chi tiết từng tiêu chí" → chỉ xuất tóm tắt + top issues
- Bất kỳ yêu cầu nào khác: áp dụng theo đúng nghĩa của lưu ý đó

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

1. Gọi `seo_save_report(audit_results, output_format, output_dir)` — truyền `output_format` và `output_dir` từ config đã lưu ở Agent 1. Nếu `output_dir` trống, dùng `~/Claude/SEO Reports`.

2. Sau khi save thành công, gọi `ToolSearch` với query `"present_files"` (max_results: 3) để load tool trình bày file. Nếu tìm thấy tool `present_files` (hoặc tên tương tự), gọi nó với đường dẫn file vừa lưu để hiển thị trong giao diện. Nếu không tìm thấy, bỏ qua bước này.

3. Dùng tool `visualize` để hiển thị kết quả tóm tắt:

   Bảng kết quả gồm:
   - **File báo cáo**: `{file_path}`
   - **Tổng điểm**: `{percentage}%` — Grade `{grade}`
   - **✅ Đạt**: `{passed}` tiêu chí
   - **❌ Lỗi**: `{failed}` tiêu chí
   - **⚠️ Cần cải thiện**: `{warning}` tiêu chí
   - **🔍 Kiểm tra thủ công**: `{manual}` tiêu chí

   Và danh sách Top 3 vấn đề ưu tiên cần xử lý ngay.

---

## Lưu Ý Quan Trọng

- **Không bịa đặt dữ liệu**: Chỉ gán status dựa trên dữ liệu thực tế thu thập được từ tool. Nếu không có dữ liệu, gán `manual` kèm hướng dẫn kiểm tra thủ công.
- **Nhóm XII (GSC Errors)**: Nếu không có GSC export file, toàn bộ nhóm này đánh dấu `manual`.
- **Nhóm XIV (Log File)**: Luôn là `manual` vì cần file log server.
- **Tiêu chí responsive/UI/visual**: Luôn là `manual` nếu không có dữ liệu trực tiếp.
- Khi gặp lỗi network/timeout khi crawl: báo lỗi rõ ràng, tiếp tục crawl URL tiếp theo.
