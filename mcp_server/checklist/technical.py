from dataclasses import dataclass


@dataclass
class ChecklistItem:
    id: str
    name: str
    category: str
    priority: str  # mandatory | high | nicetohave
    description: str
    check_method: str  # auto | manual | api
    tool_hint: str


TECHNICAL_CHECKLIST: list[ChecklistItem] = [
    # =========================================================
    # I. DOMAIN (3 items)
    # =========================================================
    ChecklistItem(
        id="domain_01",
        name="www & non-www redirect",
        category="I. DOMAIN",
        priority="mandatory",
        description="Các phiên bản www/non-www đều redirect 301 về phiên bản chính thức. Chỉ 1 phiên bản được index.",
        check_method="auto",
        tool_hint="seo_check_url_batch",
    ),
    ChecklistItem(
        id="domain_02",
        name="HTTP → HTTPS redirect",
        category="I. DOMAIN",
        priority="mandatory",
        description="Toàn bộ URL HTTP redirect 301 về HTTPS. HSTS header được khai báo.",
        check_method="auto",
        tool_hint="seo_crawl_page",
    ),
    ChecklistItem(
        id="domain_03",
        name="Hosting tốc độ & uptime",
        category="I. DOMAIN",
        priority="high",
        description="Server phản hồi < 200ms TTFB. Uptime >= 99.9%. Hosting tại region gần người dùng mục tiêu.",
        check_method="auto",
        tool_hint="seo_crawl_page (response_time_ms) + seo_check_pagespeed",
    ),
    # =========================================================
    # II. INDEXABILITY (5 items)
    # =========================================================
    ChecklistItem(
        id="index_01",
        name="Robots.txt tồn tại và hợp lệ",
        category="II. INDEXABILITY",
        priority="mandatory",
        description="File robots.txt tồn tại tại /robots.txt. Không block Googlebot hoặc các trang quan trọng.",
        check_method="auto",
        tool_hint="seo_check_robots",
    ),
    ChecklistItem(
        id="index_02",
        name="Sitemap.xml tồn tại và hợp lệ",
        category="II. INDEXABILITY",
        priority="mandatory",
        description="Sitemap tồn tại, được khai báo trong robots.txt, có đúng định dạng XML, lastmod hợp lệ.",
        check_method="auto",
        tool_hint="seo_check_sitemap",
    ),
    ChecklistItem(
        id="index_03",
        name="Trang quan trọng được index (không bị noindex)",
        category="II. INDEXABILITY",
        priority="mandatory",
        description="Trang chủ, danh mục, sản phẩm, bài viết không có meta robots noindex hoặc X-Robots-Tag: noindex.",
        check_method="auto",
        tool_hint="seo_crawl_page (meta_robots)",
    ),
    ChecklistItem(
        id="index_05",
        name="Không có trang 404 giả (soft 404)",
        category="II. INDEXABILITY",
        priority="high",
        description="Trang không tồn tại trả về đúng status 404/410, không trả về 200 với nội dung lỗi.",
        check_method="auto",
        tool_hint="seo_crawl_page (status_code) + seo_check_url_batch",
    ),
    ChecklistItem(
        id="index_06",
        name="Canonical tag đúng và nhất quán",
        category="II. INDEXABILITY",
        priority="mandatory",
        description="Mỗi trang có canonical self-referencing hoặc trỏ đúng trang gốc. Không có canonical vòng tròn.",
        check_method="auto",
        tool_hint="seo_crawl_page (canonical, canonical_matches_url)",
    ),
    # =========================================================
    # III. JAVASCRIPT SEO (1 item)
    # =========================================================
    ChecklistItem(
        id="js_01",
        name="Nội dung render được khi tắt JavaScript",
        category="III. JAVASCRIPT SEO",
        priority="high",
        description="Nội dung chính (title, heading, body text) có mặt trong HTML trả về, không phụ thuộc hoàn toàn vào JS để render.",
        check_method="auto",
        tool_hint="seo_crawl_page (word_count > 100)",
    ),
    # =========================================================
    # IV. WEBSITE STRUCTURE (11 items)
    # =========================================================
    ChecklistItem(
        id="struct_01",
        name="Cấu trúc URL ngắn gọn, thân thiện",
        category="IV. WEBSITE STRUCTURE",
        priority="mandatory",
        description="URL sử dụng dấu gạch ngang, không có ký tự đặc biệt, không quá 115 ký tự, phản ánh cấu trúc danh mục.",
        check_method="auto",
        tool_hint="seo_crawl_page (phân tích URL pattern)",
    ),
    ChecklistItem(
        id="struct_02",
        name="Cấu trúc phân cấp URL hợp lý (silo)",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description=(
            "URL phản ánh đúng cấu trúc danh mục. "
            "Sản phẩm/dịch vụ: domain.com/danh-muc/san-pham hoặc domain.com/danh-muc-lon/danh-muc-nho/san-pham — KHÔNG được ở root domain.com/san-pham. "
            "Bài viết: domain.com/danh-muc/bai-viet hoặc domain.com/danh-muc-lon/danh-muc-nho/bai-viet — KHÔNG được ở root domain.com/bai-viet. "
            "Danh mục: 1-2 cấp (/danh-muc/ hoặc /danh-muc-lon/danh-muc-nho/). "
            "Trang tĩnh: root level domain.com/ve-chung-toi là được."
        ),
        check_method="auto",
        tool_hint="Phân tích URL pattern từ crawl data: đếm path segments của product/article pages",
    ),
    ChecklistItem(
        id="struct_03",
        name="Breadcrumb HTML có mặt trên trang",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description="Breadcrumb hiển thị đúng đường dẫn, có thể click, phản ánh URL hierarchy.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_breadcrumb_html)",
    ),
    ChecklistItem(
        id="struct_04",
        name="BreadcrumbList Schema markup",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description="Schema BreadcrumbList JSON-LD có mặt, đúng cú pháp, khớp với breadcrumb HTML.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains BreadcrumbList)",
    ),
    ChecklistItem(
        id="struct_05",
        name="Organization Schema trên trang chủ",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description="Schema Organization hoặc LocalBusiness JSON-LD có trên trang chủ với name, url, logo, contactPoint.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains Organization|LocalBusiness)",
    ),
    ChecklistItem(
        id="struct_06",
        name="WebSite Schema + Sitelinks SearchBox",
        category="IV. WEBSITE STRUCTURE",
        priority="nicetohave",
        description="Schema WebSite có potentialAction SearchAction để kích hoạt Sitelinks SearchBox trên Google.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains WebSite)",
    ),
    ChecklistItem(
        id="struct_07",
        name="Product Schema trên trang sản phẩm",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description="Schema Product có name, image, description, offers (price, currency, availability). Review/Rating nếu có.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains Product)",
    ),
    ChecklistItem(
        id="struct_08",
        name="Article/BlogPosting Schema trên bài viết",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description="Schema Article hoặc BlogPosting có headline, author, datePublished, image.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains Article|BlogPosting)",
    ),
    ChecklistItem(
        id="struct_09",
        name="FAQPage Schema trên trang FAQ",
        category="IV. WEBSITE STRUCTURE",
        priority="nicetohave",
        description="Schema FAQPage với Question/Answer pairs đúng cú pháp.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains FAQPage)",
    ),
    ChecklistItem(
        id="struct_10",
        name="HowTo Schema trên trang hướng dẫn",
        category="IV. WEBSITE STRUCTURE",
        priority="nicetohave",
        description="Schema HowTo với các step cụ thể trên các trang hướng dẫn.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data_types contains HowTo)",
    ),
    ChecklistItem(
        id="struct_11",
        name="Schema không có lỗi cú pháp",
        category="IV. WEBSITE STRUCTURE",
        priority="mandatory",
        description="Toàn bộ JSON-LD hợp lệ, không có lỗi parse, required properties đầy đủ.",
        check_method="auto",
        tool_hint="seo_crawl_page (structured_data — parse JSON-LD và validate)",
    ),
    ChecklistItem(
        id="struct_13",
        name="Phân trang (pagination) đúng chuẩn",
        category="IV. WEBSITE STRUCTURE",
        priority="high",
        description="Trang phân trang sử dụng rel=next/prev hoặc canonical về trang 1. Không có infinite scroll không crawlable.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_pagination) + kiểm tra link rel=next/prev",
    ),
    # =========================================================
    # V. LINKS (2 items)
    # =========================================================
    ChecklistItem(
        id="links_01",
        name="Internal links không có 404",
        category="V. LINKS",
        priority="mandatory",
        description="Không có internal link nào trỏ đến trang 404. Tất cả internal links hoạt động.",
        check_method="auto",
        tool_hint="seo_crawl_page (internal_links) + seo_check_url_batch",
    ),
    ChecklistItem(
        id="links_02",
        name="External links có nofollow/noreferrer",
        category="V. LINKS",
        priority="high",
        description="External links ra ngoài domain có rel=nofollow hoặc rel=noreferrer để bảo vệ link equity.",
        check_method="auto",
        tool_hint="seo_crawl_page (external_links_without_nofollow)",
    ),
    # =========================================================
    # VI. METADATA & ON-PAGE (13 items)
    # =========================================================
    ChecklistItem(
        id="meta_01",
        name="Title tag tồn tại, độ dài hợp lý",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Title tag có mặt, độ dài 50-65 ký tự (tiếng Anh) hoặc 30-65 ký tự (tiếng Việt). Chứa từ khóa chính.",
        check_method="auto",
        tool_hint="seo_crawl_page (title, title_length)",
    ),
    ChecklistItem(
        id="meta_02",
        name="Meta description tồn tại, độ dài hợp lý",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Meta description có mặt, độ dài 120-160 ký tự. Mô tả đúng nội dung trang, có CTA.",
        check_method="auto",
        tool_hint="seo_crawl_page (meta_description, meta_description_length)",
    ),
    ChecklistItem(
        id="meta_03",
        name="Không có duplicate title/meta description",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Mỗi trang có title và meta description riêng biệt, không trùng lặp với trang khác.",
        check_method="auto",
        tool_hint="seo_parse_screaming_frog hoặc so sánh crawl data nhiều trang",
    ),
    ChecklistItem(
        id="meta_04",
        name="H1 tồn tại, đúng số lượng",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Mỗi trang có đúng 1 thẻ H1 chứa từ khóa chính. Không có trang thiếu H1 hoặc có nhiều H1.",
        check_method="auto",
        tool_hint="seo_crawl_page (h1_count, headings)",
    ),
    ChecklistItem(
        id="meta_05",
        name="Cấu trúc heading hợp lý (H1→H2→H3)",
        category="VI. METADATA & ON-PAGE",
        priority="high",
        description="Heading có thứ bậc logic: H2 nằm trong H1, H3 nằm trong H2. Không bỏ cấp.",
        check_method="auto",
        tool_hint="seo_crawl_page (headings structure)",
    ),
    ChecklistItem(
        id="meta_06",
        name="Hình ảnh có alt text",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Tất cả hình ảnh nội dung có alt text mô tả đúng, không để trống hoặc nhồi từ khóa.",
        check_method="auto",
        tool_hint="seo_crawl_page (images_without_alt)",
    ),
    ChecklistItem(
        id="meta_07",
        name="Open Graph tags đầy đủ",
        category="VI. METADATA & ON-PAGE",
        priority="high",
        description="Có og:title, og:description, og:image, og:url, og:type. og:image đúng kích thước 1200x630px.",
        check_method="auto",
        tool_hint="seo_crawl_page (og_tags)",
    ),
    ChecklistItem(
        id="meta_08",
        name="Viewport meta tag có mặt",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Có <meta name='viewport' content='width=device-width, initial-scale=1'>.",
        check_method="auto",
        tool_hint="seo_crawl_page (viewport_meta)",
    ),
    ChecklistItem(
        id="meta_09",
        name="Charset được khai báo",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Có <meta charset='UTF-8'> hoặc Content-Type header chứa charset=utf-8.",
        check_method="auto",
        tool_hint="seo_crawl_page (charset)",
    ),
    ChecklistItem(
        id="meta_10",
        name="Hreflang đúng (nếu đa ngôn ngữ)",
        category="VI. METADATA & ON-PAGE",
        priority="mandatory",
        description="Nếu website đa ngôn ngữ: hreflang tags có mặt, đúng locale, có self-referencing, có x-default.",
        check_method="auto",
        tool_hint="seo_crawl_page (hreflang)",
    ),
    ChecklistItem(
        id="meta_11",
        name="Favicon có mặt",
        category="VI. METADATA & ON-PAGE",
        priority="high",
        description="Favicon được khai báo (<link rel='icon'>), file tồn tại và load được.",
        check_method="auto",
        tool_hint="seo_crawl_page (favicon)",
    ),
    ChecklistItem(
        id="meta_12",
        name="Rich snippet markup (Review/Rating)",
        category="VI. METADATA & ON-PAGE",
        priority="nicetohave",
        description="Schema Review hoặc AggregateRating có mặt trên trang sản phẩm/dịch vụ để hiển thị sao trên SERP.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_rich_snippet_markup)",
    ),
    ChecklistItem(
        id="meta_13",
        name="Table of Contents trên bài viết dài",
        category="VI. METADATA & ON-PAGE",
        priority="nicetohave",
        description="Bài viết dài có TOC với anchor links đến các H2/H3 heading.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_toc)",
    ),
    # =========================================================
    # VII. UI & RESPONSIVE (1 item)
    # =========================================================
    ChecklistItem(
        id="ui_02",
        name="Font chữ và màu sắc đủ tương phản",
        category="VII. UI & RESPONSIVE",
        priority="high",
        description="Tỷ lệ tương phản màu chữ/nền đạt WCAG AA (≥4.5:1 cho text thường, ≥3:1 cho text lớn).",
        check_method="manual",
        tool_hint="Dùng Chrome DevTools > Accessibility > Contrast ratio hoặc tool webaim.org/resources/contrastchecker",
    ),
    # =========================================================
    # VIII. FEATURES & UX (8 items)
    # =========================================================
    ChecklistItem(
        id="feat_01",
        name="Thanh tìm kiếm nội bộ",
        category="VIII. FEATURES & UX",
        priority="high",
        description="Website có chức năng tìm kiếm nội bộ, kết quả tìm kiếm hiển thị đúng và có noindex.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_search_form)",
    ),
    ChecklistItem(
        id="feat_02",
        name="Form liên hệ hoạt động",
        category="VIII. FEATURES & UX",
        priority="high",
        description="Có form liên hệ, form hoạt động đúng, có xác nhận gửi thành công, trang thank-you noindex.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_contact_form)",
    ),
    ChecklistItem(
        id="feat_03",
        name="Live chat tích hợp",
        category="VIII. FEATURES & UX",
        priority="nicetohave",
        description="Live chat widget (Tawk.to, Crisp, Intercom, Zalo, v.v.) có mặt và load đúng.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_live_chat, live_chat_platform)",
    ),
    ChecklistItem(
        id="feat_04",
        name="Nút chia sẻ mạng xã hội",
        category="VIII. FEATURES & UX",
        priority="nicetohave",
        description="Bài viết/sản phẩm có nút share lên Facebook, Zalo, Twitter, Pinterest, v.v.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_social_share_buttons)",
    ),
    ChecklistItem(
        id="feat_05",
        name="Phần bình luận trên bài viết",
        category="VIII. FEATURES & UX",
        priority="nicetohave",
        description="Bài viết có hệ thống bình luận (WordPress comments, Disqus, Facebook Comments, v.v.).",
        check_method="auto",
        tool_hint="seo_crawl_page (has_comment_section)",
    ),
    ChecklistItem(
        id="feat_06",
        name="Tính năng thương mại điện tử đầy đủ",
        category="VIII. FEATURES & UX",
        priority="high",
        description="Trang sản phẩm có nút thêm vào giỏ, hiển thị giá rõ ràng, có ảnh sản phẩm chất lượng.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_cart_button, has_price_display)",
    ),
    ChecklistItem(
        id="feat_07",
        name="Newsletter signup form",
        category="VIII. FEATURES & UX",
        priority="nicetohave",
        description="Có form đăng ký nhận bản tin email để xây dựng danh sách khách hàng.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_newsletter_form)",
    ),
    ChecklistItem(
        id="feat_08",
        name="Nút Back-to-top",
        category="VIII. FEATURES & UX",
        priority="nicetohave",
        description="Trang dài có nút back-to-top giúp UX tốt hơn.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_back_to_top)",
    ),
    # =========================================================
    # IX. PAGE SPEED (4 items)
    # =========================================================
    ChecklistItem(
        id="speed_01",
        name="Core Web Vitals đạt ngưỡng tốt",
        category="IX. PAGE SPEED",
        priority="mandatory",
        description="LCP < 2.5s, INP < 200ms, CLS < 0.1 trên cả mobile và desktop theo PageSpeed Insights.",
        check_method="api",
        tool_hint="seo_check_pagespeed (LCP, INP, CLS)",
    ),
    ChecklistItem(
        id="speed_02",
        name="Performance score >= 70 (mobile)",
        category="IX. PAGE SPEED",
        priority="high",
        description="PageSpeed Insights Performance score >= 70 trên mobile.",
        check_method="api",
        tool_hint="seo_check_pagespeed (performance_score, strategy=mobile)",
    ),
    ChecklistItem(
        id="speed_03",
        name="Hình ảnh được tối ưu (next-gen format, lazy load)",
        category="IX. PAGE SPEED",
        priority="high",
        description="Ảnh sử dụng định dạng WebP/AVIF, có lazy loading, kích thước phù hợp với display size.",
        check_method="api",
        tool_hint="seo_check_pagespeed (opportunities: image optimization)",
    ),
    ChecklistItem(
        id="speed_04",
        name="Browser caching được kích hoạt",
        category="IX. PAGE SPEED",
        priority="high",
        description="Static assets có Cache-Control header với max-age hợp lý (CSS/JS: 1 năm, HTML: không cache).",
        check_method="auto",
        tool_hint="seo_crawl_page (cache_control)",
    ),
    # =========================================================
    # X. CMS & TECHNICAL SETUP (1 item)
    # =========================================================
    ChecklistItem(
        id="cms_14",
        name="llms.txt tồn tại (AI SEO)",
        category="X. CMS & TECHNICAL SETUP",
        priority="nicetohave",
        description="File /llms.txt cung cấp thông tin về website cho AI crawlers (ChatGPT, Perplexity, Claude).",
        check_method="auto",
        tool_hint="seo_check_robots (has_llms_txt)",
    ),
    # =========================================================
    # XI. MEASUREMENT & ANALYTICS (2 items)
    # =========================================================
    ChecklistItem(
        id="measure_01",
        name="Google Tag Manager được cài đặt",
        category="XI. MEASUREMENT & ANALYTICS",
        priority="mandatory",
        description="GTM container snippet có mặt trong <head> và <body>. GTM ID đúng.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_gtm, gtm_id)",
    ),
    ChecklistItem(
        id="measure_02",
        name="Google Analytics 4 được tracking",
        category="XI. MEASUREMENT & ANALYTICS",
        priority="mandatory",
        description="GA4 Measurement ID (G-XXXXXXX) có mặt, tracking qua GTM hoặc direct snippet.",
        check_method="auto",
        tool_hint="seo_crawl_page (has_ga4, ga4_id)",
    ),
    # =========================================================
    # XIV. LOG FILE ANALYSIS (4 items)
    # =========================================================
    ChecklistItem(
        id="log_01",
        name="Googlebot crawl frequency phù hợp",
        category="XIV. LOG FILE ANALYSIS",
        priority="high",
        description="Tần suất Googlebot crawl tương xứng với tốc độ publish nội dung mới. Không có gap crawl lớn.",
        check_method="manual",
        tool_hint="Phân tích access log: lọc theo Googlebot user-agent, xem tần suất và trang được crawl",
    ),
    ChecklistItem(
        id="log_02",
        name="Không có trang rác được Googlebot crawl nhiều",
        category="XIV. LOG FILE ANALYSIS",
        priority="high",
        description="Log không có pattern Googlebot crawl các URL rác (search result, filter, session ID) với tần suất cao.",
        check_method="manual",
        tool_hint="Phân tích access log: top URLs được Googlebot crawl, so sánh với danh sách URL quan trọng",
    ),
    ChecklistItem(
        id="log_03",
        name="Crawl budget được tối ưu",
        category="XIV. LOG FILE ANALYSIS",
        priority="high",
        description="Tỷ lệ % trang quan trọng trong total Googlebot requests >= 80%. Block trang không cần thiết.",
        check_method="manual",
        tool_hint="Phân tích access log: phân loại URL theo loại trang, tính % crawl budget cho trang quan trọng",
    ),
    ChecklistItem(
        id="log_04",
        name="Không có 5xx errors trong log",
        category="XIV. LOG FILE ANALYSIS",
        priority="mandatory",
        description="Log server không có lỗi 500/502/503/504. Nếu có, phải xử lý ngay để tránh mất index.",
        check_method="manual",
        tool_hint="Phân tích access log: lọc status 5xx, tìm URL và thời điểm xảy ra lỗi",
    ),
]


def get_checklist_by_category() -> dict[str, list[ChecklistItem]]:
    result: dict[str, list[ChecklistItem]] = {}
    for item in TECHNICAL_CHECKLIST:
        result.setdefault(item.category, []).append(item)
    return result


def get_checklist_as_dict() -> list[dict]:
    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "priority": item.priority,
            "description": item.description,
            "check_method": item.check_method,
            "tool_hint": item.tool_hint,
        }
        for item in TECHNICAL_CHECKLIST
    ]
