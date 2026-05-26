import asyncio
import json
import re
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SEOAuditBot/1.0; +https://github.com/seo-audit)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

_LIVE_CHAT_PATTERNS: dict[str, list[str]] = {
    "Tawk.to": ["tawk.to", "tawkto"],
    "Crisp": ["crisp.chat", "client.crisp"],
    "Intercom": ["intercom.io", "intercomcdn"],
    "Zendesk": ["zendesk.com", "zopim.com"],
    "LiveChat": ["livechatinc.com", "livechat.com"],
    "Tidio": ["tidio.co"],
    "Zalo": ["zalo.me", "sp.zalo.me"],
    "Facebook Messenger": ["connect.facebook.net"],
    "HubSpot": ["js.hubspot.com", "js.hs-scripts.com"],
}

_SOCIAL_SHARE_PATTERNS = [
    "share", "sharer", "addthis", "addtoany", "sharethis",
    "facebook.com/sharer", "twitter.com/intent/tweet",
    "zalo.me/share", "linkedin.com/shareArticle",
]


def _get_text_content(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "meta", "link"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _detect_page_type(url: str, soup: BeautifulSoup, status_code: int) -> str:
    if status_code == 404:
        return "404"
    path = urlparse(url).path.rstrip("/").lower()
    if path in ("", "/"):
        return "homepage"
    slug = path.split("/")[-1]
    for kw in ("contact", "lien-he", "lienhe", "contact-us"):
        if kw in path:
            return "contact"
    for kw in ("about", "gioi-thieu", "ve-chung-toi", "about-us"):
        if kw in path:
            return "about"
    for kw in ("404", "not-found", "page-not-found"):
        if kw in path:
            return "404"
    # Check for article signals
    has_article_schema = bool(
        soup.find("script", type="application/ld+json", string=re.compile(r"Article|BlogPosting"))
    )
    has_author = bool(soup.find(class_=re.compile(r"author", re.I)))
    has_publish_date = bool(soup.find("time") or soup.find(class_=re.compile(r"date|published", re.I)))
    if has_article_schema or (has_author and has_publish_date):
        return "article"
    # Product detail vs category heuristics
    has_add_to_cart = bool(soup.find(string=re.compile(r"thêm vào giỏ|add.to.cart|buy now|mua ngay", re.I)))
    has_price = bool(soup.find(class_=re.compile(r"price|gia|woocommerce-Price", re.I)))
    if has_add_to_cart and has_price:
        return "product_detail"
    has_product_grid = bool(soup.find(class_=re.compile(r"product-?grid|products|woocommerce ul.products", re.I)))
    if has_product_grid:
        return "product_category"
    for kw in ("blog", "tin-tuc", "bai-viet", "news"):
        if kw in path:
            segment_count = len([s for s in path.split("/") if s])
            if segment_count <= 2:
                return "blog_category"
            return "article"
    return "unknown"


def _extract_structured_data(soup: BeautifulSoup) -> tuple[list[str], list[str]]:
    raw_scripts: list[str] = []
    types: list[str] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        text = tag.string or ""
        if not text.strip():
            continue
        raw_scripts.append(text.strip())
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                t = data.get("@type", "")
                if isinstance(t, list):
                    types.extend(t)
                elif t:
                    types.append(t)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        t = item.get("@type", "")
                        if isinstance(t, list):
                            types.extend(t)
                        elif t:
                            types.append(t)
        except (json.JSONDecodeError, ValueError):
            pass
    return raw_scripts, types


def _check_header_elements(soup: BeautifulSoup, base_url: str) -> dict:
    header = soup.find("header") or soup.find(id=re.compile(r"header", re.I)) or soup.find(class_=re.compile(r"header|site-header|navbar", re.I))
    if not header:
        return {
            "header_has_logo": False,
            "header_has_nav": False,
            "header_has_search": False,
            "header_has_cta": False,
            "header_has_phone": False,
            "header_has_social_links": False,
        }
    has_logo = bool(
        header.find("img", class_=re.compile(r"logo", re.I))
        or header.find(class_=re.compile(r"logo|site-logo|brand", re.I))
        or header.find("a", href="/")
    )
    has_nav = bool(header.find("nav") or header.find(class_=re.compile(r"nav|menu|navigation", re.I)))
    has_search = bool(header.find("input", type="search") or header.find("form", role="search") or header.find(class_=re.compile(r"search", re.I)))
    has_cta = bool(
        header.find("a", class_=re.compile(r"btn|button|cta", re.I))
        or header.find("button", class_=re.compile(r"btn|cta", re.I))
    )
    phone_pattern = re.compile(r"tel:", re.I)
    has_phone = bool(header.find("a", href=phone_pattern) or header.find(string=re.compile(r"\b0\d{9,10}\b|\+84")))
    social_domains = ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "zalo"]
    has_social = bool(header.find("a", href=re.compile("|".join(social_domains), re.I)))
    return {
        "header_has_logo": has_logo,
        "header_has_nav": has_nav,
        "header_has_search": has_search,
        "header_has_cta": has_cta,
        "header_has_phone": has_phone,
        "header_has_social_links": has_social,
    }


def _check_footer_elements(soup: BeautifulSoup) -> dict:
    footer = soup.find("footer") or soup.find(id=re.compile(r"footer", re.I)) or soup.find(class_=re.compile(r"footer|site-footer", re.I))
    if not footer:
        return {
            "footer_has_contact_info": False,
            "footer_has_nav_links": False,
            "footer_has_social_links": False,
            "footer_has_copyright": False,
            "footer_has_newsletter": False,
            "footer_has_map": False,
            "footer_has_logo": False,
            "footer_has_policy_links": False,
            "footer_has_business_hours": False,
        }
    contact_patterns = re.compile(r"địa chỉ|address|điện thoại|phone|email|@", re.I)
    has_contact = bool(footer.find(string=contact_patterns) or footer.find("address"))
    has_nav = bool(footer.find("nav") or footer.find("ul") or footer.find("a"))
    social_domains = ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "zalo"]
    has_social = bool(footer.find("a", href=re.compile("|".join(social_domains), re.I)))
    has_copyright = bool(footer.find(string=re.compile(r"©|copyright|bản quyền", re.I)))
    has_newsletter = bool(
        footer.find("input", type="email")
        or footer.find(string=re.compile(r"newsletter|bản tin|đăng ký nhận", re.I))
    )
    has_map = bool(
        footer.find("iframe", src=re.compile(r"google.com/maps|maps.google", re.I))
        or footer.find(string=re.compile(r"google map|xem bản đồ", re.I))
    )
    has_logo = bool(
        footer.find(class_=re.compile(r"logo|footer-logo|site-logo|brand", re.I))
        or footer.find("img", class_=re.compile(r"logo", re.I))
        or footer.find("svg", class_=re.compile(r"logo", re.I))
    )
    has_policy = bool(
        footer.find("a", string=re.compile(r"privacy|bảo mật|riêng tư|điều khoản|terms|policy|quy định|quy chế", re.I))
        or footer.find("a", href=re.compile(r"privacy|bao-mat|dieu-khoan|terms|policy|quy-dinh", re.I))
    )
    has_hours = bool(
        footer.find(string=re.compile(
            r"t\d[-–—]t\d|thứ\s+[2-7]|8[h:]\d{2}|9[h:]\d{2}|giờ làm việc|working hours|opening hours|\d{1,2}:\d{2}", re.I
        ))
    )
    return {
        "footer_has_contact_info": has_contact,
        "footer_has_nav_links": has_nav,
        "footer_has_social_links": has_social,
        "footer_has_copyright": has_copyright,
        "footer_has_newsletter": has_newsletter,
        "footer_has_map": has_map,
        "footer_has_logo": has_logo,
        "footer_has_policy_links": has_policy,
        "footer_has_business_hours": has_hours,
    }


def _check_page_sections(soup: BeautifulSoup, html_lower: str, internal_links: list[dict]) -> dict:
    # hero_has_cta
    hero = (
        soup.find(class_=re.compile(r"hero|banner|slider|jumbotron|intro-section|top-banner", re.I))
        or soup.find(id=re.compile(r"hero|banner|slider", re.I))
        or soup.find("section")
    )
    hero_has_cta = False
    if hero:
        hero_has_cta = bool(
            hero.find("a", class_=re.compile(r"btn|button|cta", re.I))
            or hero.find("button")
            or hero.find("a", string=re.compile(r"liên hệ|xem thêm|mua ngay|tư vấn|dùng thử|contact|buy|order|get started|khám phá|xem ngay", re.I))
        )

    # has_usp_section — 3+ feature/benefit cards
    icon_boxes = soup.find_all(class_=re.compile(r"icon.?box|feature.?box|benefit.?box|service.?box|info.?box|advantage", re.I))
    has_usp_section = len(icon_boxes) >= 3
    if not has_usp_section:
        feat_section = soup.find(class_=re.compile(r"features?|benefits?|advantages?|usp|why.?(us|choose)|strengths?", re.I))
        if feat_section:
            children = [c for c in feat_section.children if hasattr(c, "name") and c.name]
            has_usp_section = len(children) >= 3

    # has_featured_products — product grid section
    prod_cards = soup.find_all(class_=re.compile(r"product.?(card|item|thumb|box)|item.?product", re.I))
    has_featured_products = len(prod_cards) >= 2 or bool(
        soup.find(class_=re.compile(r"featured.?products?|san.pham.noi.bat|product.?section|products.?grid", re.I))
    )

    # has_testimonials
    has_testimonials = bool(
        soup.find(class_=re.compile(r"testimonial|nhan.xet|danh.gia.khach|feedback|review.?section|client.?say", re.I))
        or soup.find(id=re.compile(r"testimonial|feedback|reviews", re.I))
    )

    # has_partner_logos — 3+ logos in a logo strip
    logo_strip = soup.find(class_=re.compile(r"partner|client.?logo|logo.?(strip|grid|list|cloud|partner)|brand.?(list|strip|grid)", re.I))
    has_partner_logos = False
    if logo_strip:
        has_partner_logos = len(logo_strip.find_all("img")) >= 3

    # has_blog_section — 3+ article links or blog cards
    blog_section = soup.find(class_=re.compile(r"blog.?section|news.?section|latest.?post|tin.tuc.section|recent.?post", re.I))
    has_blog_section = False
    if blog_section:
        has_blog_section = len(blog_section.find_all("a")) >= 2
    if not has_blog_section:
        blog_links = [l for l in internal_links if re.search(r"/(blog|tin-tuc|news|bai-viet)/", l.get("href", ""), re.I)]
        has_blog_section = len(blog_links) >= 3

    # has_counter_stats — animated counters / achievement numbers
    has_counter_stats = bool(
        soup.find(class_=re.compile(r"counter|odometer|stat.?box|fun.?fact|achievement|so.?lieu|number.?box", re.I))
        or soup.find(id=re.compile(r"counter|stats|achievements", re.I))
        or soup.find(attrs={"data-count": True})
        or soup.find(attrs={"data-target": re.compile(r"^\d+$")})
    )

    # has_popup — modal / overlay elements (excluding menu overlays)
    has_popup = bool(
        soup.find(class_=re.compile(r"\bmodal\b|popup|lightbox|mfp-|fancybox|overlay.?(popup|modal)", re.I))
        or soup.find(id=re.compile(r"\bmodal\b|popup|overlay", re.I))
    )

    # has_product_count_display
    has_product_count_display = bool(
        soup.find(class_=re.compile(r"woocommerce-result-count|product.?count|showing.?results?|result.?count", re.I))
        or soup.find(string=re.compile(r"hiển thị\s+\d+|showing\s+\d+|kết quả|of\s+\d+\s+result", re.I))
    )

    # has_subcategory_links
    has_subcategory_links = bool(
        soup.find(class_=re.compile(r"subcategor|sub.?cat|child.?cat|product.?subcategor|danh.muc.con", re.I))
    )

    # has_shipping_info
    has_shipping_info = bool(
        soup.find(string=re.compile(r"vận chuyển|giao hàng|shipping|đổi trả|return policy|hoàn trả|bảo hành|delivery", re.I))
        or soup.find(class_=re.compile(r"shipping|delivery|return.?policy|warranty|van.chuyen|doi.tra", re.I))
    )

    # has_related_products
    has_related_products = bool(
        soup.find(class_=re.compile(r"related.?products?|san.pham.lien.quan|upsell|cross.sell|similar.?product", re.I))
        or soup.find(string=re.compile(r"sản phẩm liên quan|related products|bạn cũng thích|you may also like|có thể bạn thích", re.I))
    )

    # has_category_tags
    has_category_tags = bool(
        soup.find(class_=re.compile(r"post.?tag|tag.?label|entry.?tag|cat.?label|category.?badge", re.I))
        or soup.find("a", class_=re.compile(r"\btag\b", re.I))
    )

    # has_sidebar
    has_sidebar = bool(
        soup.find("aside")
        or soup.find(id=re.compile(r"sidebar|side.?bar", re.I))
        or soup.find(class_=re.compile(r"\bsidebar\b|side.?bar|widget.?area|widget.?column", re.I))
    )

    # has_related_posts
    has_related_posts = bool(
        soup.find(class_=re.compile(r"related.?posts?|bai.viet.lien.quan|similar.?posts?|more.?posts?", re.I))
        or soup.find(id=re.compile(r"related.?posts?", re.I))
        or soup.find(string=re.compile(r"bài viết liên quan|related posts|bạn có thể thích|you might also like", re.I))
    )

    # has_mission_text
    has_mission_text = bool(
        soup.find(class_=re.compile(r"mission|vision|values|su.?menh|tam.?nhin|gia.?tri.?cot.?loi", re.I))
        or soup.find(id=re.compile(r"mission|vision|values", re.I))
        or soup.find(string=re.compile(r"sứ mệnh|tầm nhìn|giá trị cốt lõi|mission statement|core values", re.I))
    )

    # has_team_section — 2+ team member cards
    team_wrap = soup.find(class_=re.compile(r"\bteam\b|member|staff|nhan.su|doi.ngu|our.?team", re.I))
    has_team_section = False
    if team_wrap:
        member_cards = team_wrap.find_all(class_=re.compile(r"team.?member|team.?item|member.?card|staff.?item", re.I))
        if not member_cards:
            member_cards = [c for c in team_wrap.children if hasattr(c, "name") and c.name in ("div", "li", "article")]
        has_team_section = len(member_cards) >= 2

    # has_certifications
    has_certifications = bool(
        soup.find(class_=re.compile(r"certif|award|achievement|chung.nhan|giai.thuong|iso.?cert|badge", re.I))
        or soup.find("img", alt=re.compile(r"certif|ISO|award|chứng nhận|giải thưởng", re.I))
        or soup.find(string=re.compile(r"ISO \d{4,5}|chứng nhận|certificate|giải thưởng|award.?winning", re.I))
    )

    # has_video_embed
    has_video_embed = bool(
        soup.find("iframe", src=re.compile(r"youtube\.com|youtu\.be|vimeo\.com|dailymotion", re.I))
        or soup.find("video", src=True)
        or soup.find(class_=re.compile(r"video.?(wrap|container|embed|section|player)|youtube.?(wrap|embed)", re.I))
    )

    # has_business_hours (full page — for contact page)
    has_business_hours = bool(
        soup.find(string=re.compile(
            r"t\d[-–—]t\d|thứ\s+[2-7]|8[h:]\d{2}|9[h:]\d{2}|giờ làm việc|working hours|opening hours|\d{1,2}:\d{2}", re.I
        ))
        or soup.find(class_=re.compile(r"opening.?hours?|business.?hours?|working.?hours?|gio.?lam.?viec", re.I))
    )

    return {
        "hero_has_cta": hero_has_cta,
        "has_usp_section": has_usp_section,
        "has_featured_products": has_featured_products,
        "has_testimonials": has_testimonials,
        "has_partner_logos": has_partner_logos,
        "has_blog_section": has_blog_section,
        "has_counter_stats": has_counter_stats,
        "has_popup": has_popup,
        "has_product_count_display": has_product_count_display,
        "has_subcategory_links": has_subcategory_links,
        "has_shipping_info": has_shipping_info,
        "has_related_products": has_related_products,
        "has_category_tags": has_category_tags,
        "has_sidebar": has_sidebar,
        "has_related_posts": has_related_posts,
        "has_mission_text": has_mission_text,
        "has_team_section": has_team_section,
        "has_certifications": has_certifications,
        "has_video_embed": has_video_embed,
        "has_business_hours": has_business_hours,
    }


def _check_ui_patterns(soup: BeautifulSoup, html_lower: str) -> dict:
    """Detect 7 UI structural patterns from HTML without JS rendering."""
    # has_sticky_header
    header_el = (
        soup.find("header")
        or soup.find(id=re.compile(r"^header", re.I))
        or soup.find(class_=re.compile(r"site-header|page-header|main-header", re.I))
    )
    has_sticky_header = False
    if header_el:
        style = header_el.get("style", "")
        classes = " ".join(header_el.get("class", []))
        has_sticky_header = bool(
            re.search(r"position\s*:\s*(sticky|fixed)", style, re.I)
            or re.search(r"\b(sticky|fixed-top|fixed-header|header-fixed|affix|is-stuck)\b", classes, re.I)
        )
    # Also check if any script/class globally marks sticky header
    if not has_sticky_header:
        has_sticky_header = bool(re.search(r"sticky.header|header.sticky|fixed.header|header.fixed", html_lower))

    # has_hamburger_menu
    has_hamburger_menu = bool(
        soup.find(class_=re.compile(r"hamburger|navbar-toggler|menu-toggle|nav-toggle|burger|toggle-menu|mobile-menu-btn|nav-icon|menu-icon", re.I))
        or soup.find(id=re.compile(r"hamburger|menu-toggle|nav-toggle|mobile-menu", re.I))
        or soup.find("button", attrs={"aria-label": re.compile(r"menu|navigation|nav|toggle", re.I)})
        or soup.find("button", attrs={"aria-controls": re.compile(r"menu|nav|navigation", re.I)})
    )

    # has_payment_logos
    payment_pattern = re.compile(
        r"visa|mastercard|vnpay|momo|zalopay|napas|jcb|amex|paypal|thanh.?toan|payment|secure.?pay|atm.?card", re.I
    )
    has_payment_logos = bool(
        soup.find("img", alt=payment_pattern)
        or soup.find("img", src=payment_pattern)
        or soup.find("img", title=payment_pattern)
        or soup.find(class_=re.compile(r"payment.?logo|thanh-toan|secure-badge|trust-badge|payment-method", re.I))
        or re.search(r"visa|mastercard|vnpay|momo|zalopay|napas", html_lower)
    )

    # has_product_filter
    has_product_filter = bool(
        soup.find(class_=re.compile(r"widget_layered_nav|woocommerce-widget-layered-nav|product-filter|filter-widget|shop-filter|catalog-filter|ajax-filter|bộ-lọc|bo-loc", re.I))
        or soup.find(id=re.compile(r"filter|layered-nav|product-filter|shop-filter", re.I))
        or soup.find("form", class_=re.compile(r"filter|ajax-filter", re.I))
        or soup.find(class_=re.compile(r"widget_product_categories|product-categories-widget", re.I))
    )

    # has_product_sort
    has_product_sort = bool(
        soup.find("select", attrs={"name": "orderby"})
        or soup.find("select", attrs={"name": re.compile(r"sort|order", re.I)})
        or soup.find(class_=re.compile(r"woocommerce-ordering|sort-select|product-sort|orderby-select", re.I))
        or soup.find("form", class_=re.compile(r"woocommerce-ordering", re.I))
    )

    # has_image_zoom (zoom/lightbox library detected)
    scripts_text = " ".join(
        (s.get("src", "") or "") + (s.string or "")
        for s in soup.find_all("script")
    )
    has_image_zoom = bool(
        soup.find(class_=re.compile(r"woocommerce-product-gallery__trigger|fancybox|lightbox|photoswipe|magnific|pswp|image-zoom|product-gallery__trigger", re.I))
        or soup.find(attrs={"data-fancybox": True})
        or soup.find(attrs={"data-lightbox": True})
        or soup.find(attrs={"data-zoom-image": True})
        or soup.find("a", class_=re.compile(r"\bzoom\b|fancybox|lightbox|photoswipe", re.I))
        or re.search(r"fancybox|photoswipe|lightbox|magnific.popup|wc-product-gallery", scripts_text, re.I)
    )

    # has_variant_selector (WooCommerce variations / custom swatches)
    has_variant_selector = bool(
        soup.find(class_=re.compile(r"\bvariations\b|variation-select|product-variants|variant-selector|swatch|color-swatch|size-swatch|attribute-select|woo-variation", re.I))
        or soup.find("select", attrs={"name": re.compile(r"^attribute_", re.I)})
        or soup.find("form", class_=re.compile(r"variations_form|variation-form", re.I))
    )

    return {
        "has_sticky_header": has_sticky_header,
        "has_hamburger_menu": has_hamburger_menu,
        "has_payment_logos": has_payment_logos,
        "has_product_filter": has_product_filter,
        "has_product_sort": has_product_sort,
        "has_image_zoom": has_image_zoom,
        "has_variant_selector": has_variant_selector,
    }


async def crawl_page(url: str, page_type: str = "auto", follow_redirects: bool = True, timeout: int = 15) -> dict:
    redirect_chain: list[str] = []
    start = time.monotonic()

    async with httpx.AsyncClient(
        headers=_HEADERS,
        follow_redirects=follow_redirects,
        timeout=timeout,
    ) as client:
        try:
            resp = await client.get(url)
            for r in resp.history:
                redirect_chain.append(str(r.url))
            final_url = str(resp.url)
            status_code = resp.status_code
            html = resp.text
            response_headers = dict(resp.headers)
        except httpx.TimeoutException:
            return {"url": url, "error": "timeout", "status_code": None}
        except httpx.RequestError as e:
            return {"url": url, "error": str(e), "status_code": None}

    response_time_ms = int((time.monotonic() - start) * 1000)

    soup = BeautifulSoup(html, "lxml")

    # ---- Title ----
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    title_length = len(title)

    # ---- Meta description ----
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""
    meta_description_length = len(meta_description)

    # ---- Meta robots ----
    meta_robots_tag = soup.find("meta", attrs={"name": re.compile(r"robots", re.I)})
    meta_robots = meta_robots_tag.get("content", "").strip() if meta_robots_tag else ""

    # ---- Canonical ----
    canonical_tag = soup.find("link", rel=lambda x: x and "canonical" in x)
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""
    canonical_matches_url = (canonical.rstrip("/") == final_url.rstrip("/")) if canonical else False

    # ---- Hreflang ----
    hreflang = []
    for tag in soup.find_all("link", rel=lambda x: x and "alternate" in x):
        hl = tag.get("hreflang")
        href = tag.get("href")
        if hl and href:
            hreflang.append({"hreflang": hl, "href": href})

    # ---- OG Tags ----
    og_tags: dict[str, str] = {}
    for tag in soup.find_all("meta", property=re.compile(r"^og:", re.I)):
        prop = tag.get("property", "").lower()
        content = tag.get("content", "")
        if prop and content:
            og_tags[prop] = content

    # ---- Viewport ----
    viewport_tag = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
    viewport_meta = viewport_tag.get("content", "").strip() if viewport_tag else ""

    # ---- Charset ----
    charset_tag = soup.find("meta", charset=True)
    if charset_tag:
        charset = charset_tag.get("charset", "")
    else:
        ct_tag = soup.find("meta", attrs={"http-equiv": re.compile(r"content-type", re.I)})
        if ct_tag:
            ct_content = ct_tag.get("content", "")
            m = re.search(r"charset=([^\s;]+)", ct_content, re.I)
            charset = m.group(1) if m else ""
        else:
            charset = response_headers.get("content-type", "")
            m = re.search(r"charset=([^\s;]+)", charset, re.I)
            charset = m.group(1) if m else ""

    # ---- Favicon ----
    favicon_tag = soup.find("link", rel=lambda x: x and any(r in x for r in ("icon", "shortcut icon")))
    favicon = urljoin(url, favicon_tag.get("href", "")) if favicon_tag else ""

    # ---- Headings ----
    headings: dict[str, list[str]] = {f"h{i}": [] for i in range(1, 7)}
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            headings[f"h{level}"].append(tag.get_text(strip=True))
    h1_count = len(headings["h1"])

    # ---- Structured data ----
    structured_data, structured_data_types = _extract_structured_data(soup)
    has_breadcrumb_html = bool(
        soup.find(class_=re.compile(r"breadcrumb", re.I))
        or soup.find("nav", aria_label=re.compile(r"breadcrumb", re.I))
        or "BreadcrumbList" in structured_data_types
    )

    # ---- Links ----
    base_domain = urlparse(final_url).netloc
    internal_links: list[dict] = []
    external_links: list[dict] = []
    external_links_without_nofollow: list[str] = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_href = urljoin(final_url, href)
        parsed = urlparse(abs_href)
        if not parsed.scheme.startswith("http"):
            continue
        rel_attr = a.get("rel", [])
        if isinstance(rel_attr, str):
            rel_attr = rel_attr.split()
        has_nofollow = "nofollow" in rel_attr
        link_info = {"href": abs_href, "text": a.get_text(strip=True)[:100], "nofollow": has_nofollow}
        if parsed.netloc == base_domain or parsed.netloc == "":
            internal_links.append(link_info)
        else:
            external_links.append(link_info)
            if not has_nofollow:
                external_links_without_nofollow.append(abs_href)

    # ---- Images ----
    images: list[dict] = []
    images_without_alt: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-src", "")
        alt = img.get("alt", "")
        has_alt = alt.strip() != ""
        if src:
            abs_src = urljoin(final_url, src)
            images.append({"src": abs_src, "alt": alt, "has_alt": has_alt})
            if not has_alt:
                images_without_alt.append(abs_src)

    # ---- GTM ----
    gtm_pattern = re.compile(r"GTM-[A-Z0-9]+")
    gtm_match = gtm_pattern.search(html)
    has_gtm = bool(gtm_match)
    gtm_id = gtm_match.group(0) if gtm_match else ""

    # ---- GA4 ----
    ga4_pattern = re.compile(r"G-[A-Z0-9]+")
    ga4_match = ga4_pattern.search(html)
    has_ga4 = bool(ga4_match)
    ga4_id = ga4_match.group(0) if ga4_match else ""

    # ---- Cache control ----
    cache_control = response_headers.get("cache-control", "")

    # ---- Feature detection ----
    html_lower = html.lower()

    has_search_form = bool(
        soup.find("input", type="search")
        or soup.find("form", role="search")
        or soup.find("input", attrs={"placeholder": re.compile(r"tìm kiếm|search", re.I)})
    )

    has_contact_form = bool(
        soup.find("form", class_=re.compile(r"contact|lien.he", re.I))
        or (soup.find("form") and soup.find("input", type=re.compile(r"text|email")))
    )

    # Live chat
    has_live_chat = False
    live_chat_platform = ""
    for platform, patterns in _LIVE_CHAT_PATTERNS.items():
        if any(p in html_lower for p in patterns):
            has_live_chat = True
            live_chat_platform = platform
            break

    has_newsletter_form = bool(
        soup.find("input", attrs={"placeholder": re.compile(r"email|newsletter|bản tin", re.I)})
        or soup.find(string=re.compile(r"đăng ký nhận|subscribe|newsletter", re.I))
    )

    has_comment_section = bool(
        soup.find(id=re.compile(r"comments?|respond|disqus", re.I))
        or soup.find(class_=re.compile(r"comments?|comment-section|fb-comments", re.I))
        or "disqus_thread" in html_lower
    )

    has_social_share_buttons = bool(
        any(p in html_lower for p in _SOCIAL_SHARE_PATTERNS)
        or soup.find(class_=re.compile(r"share|social.share", re.I))
    )

    has_back_to_top = bool(
        soup.find(id=re.compile(r"back.to.top|scroll.top|totop", re.I))
        or soup.find(class_=re.compile(r"back.to.top|scroll.top|totop", re.I))
        or soup.find(attrs={"title": re.compile(r"back to top|lên đầu trang", re.I)})
    )

    has_pagination = bool(
        soup.find(class_=re.compile(r"pagination|pager|wp-pagenavi|page-numbers", re.I))
        or soup.find("nav", aria_label=re.compile(r"pagination", re.I))
        or soup.find("link", rel="next")
    )

    has_toc = bool(
        soup.find(id=re.compile(r"toc|table.of.content|muc.luc", re.I))
        or soup.find(class_=re.compile(r"toc|table.of.content|ez-toc|wp-block-table-of-contents", re.I))
    )

    has_rich_snippet_markup = bool(
        "Review" in structured_data_types
        or "AggregateRating" in structured_data_types
        or soup.find(itemtype=re.compile(r"schema.org/Review|schema.org/AggregateRating", re.I))
    )

    has_cart_button = bool(
        soup.find("button", class_=re.compile(r"add.to.cart|addtocart|cart|giỏ.hàng", re.I))
        or soup.find("a", class_=re.compile(r"add.to.cart|addtocart", re.I))
        or soup.find(string=re.compile(r"thêm vào giỏ|add to cart|mua ngay|buy now", re.I))
    )

    has_price_display = bool(
        soup.find(class_=re.compile(r"price|gia|woocommerce-Price-amount", re.I))
        or soup.find(itemprop="price")
    )

    # ---- Header/Footer ----
    header_data = _check_header_elements(soup, final_url)
    footer_data = _check_footer_elements(soup)
    section_data = _check_page_sections(soup, html_lower, internal_links)
    ui_pattern_data = _check_ui_patterns(soup, html_lower)

    # ---- Content signals ----
    text_content = _get_text_content(soup)
    word_count = len(text_content.split())

    has_author_info = bool(
        soup.find(class_=re.compile(r"author|tac.gia", re.I))
        or soup.find(rel="author")
        or soup.find(itemprop="author")
    )

    has_publish_date = bool(
        soup.find("time")
        or soup.find(class_=re.compile(r"date|published|post.date|entry.date", re.I))
        or soup.find(itemprop="datePublished")
    )

    has_map_embed = bool(
        soup.find("iframe", src=re.compile(r"google.com/maps|maps.google", re.I))
        or soup.find("iframe", src=re.compile(r"www.google.com/maps/embed", re.I))
    )

    has_phone_links = bool(soup.find("a", href=re.compile(r"^tel:", re.I)))
    has_email_links = bool(soup.find("a", href=re.compile(r"^mailto:", re.I)))

    # ---- Page type ----
    if page_type == "auto":
        page_type_detected = _detect_page_type(final_url, soup, status_code)
    else:
        page_type_detected = page_type

    return {
        # Request info
        "url": final_url,
        "original_url": url,
        "status_code": status_code,
        "redirect_chain": redirect_chain,
        "response_time_ms": response_time_ms,
        # Metadata
        "title": title,
        "title_length": title_length,
        "meta_description": meta_description,
        "meta_description_length": meta_description_length,
        "meta_robots": meta_robots,
        "canonical": canonical,
        "canonical_matches_url": canonical_matches_url,
        "hreflang": hreflang,
        "og_tags": og_tags,
        "viewport_meta": viewport_meta,
        "charset": charset,
        "favicon": favicon,
        # Headings
        "headings": headings,
        "h1_count": h1_count,
        # Structured data
        "structured_data": structured_data,
        "structured_data_types": structured_data_types,
        "has_breadcrumb_html": has_breadcrumb_html,
        # Links
        "internal_links": internal_links,
        "external_links": external_links,
        "external_links_without_nofollow": external_links_without_nofollow,
        # Images
        "images": images,
        "images_without_alt": images_without_alt,
        # Measurement tags
        "has_gtm": has_gtm,
        "gtm_id": gtm_id,
        "has_ga4": has_ga4,
        "ga4_id": ga4_id,
        # Cache / performance
        "cache_control": cache_control,
        # Feature detection
        "has_search_form": has_search_form,
        "has_contact_form": has_contact_form,
        "has_live_chat": has_live_chat,
        "live_chat_platform": live_chat_platform,
        "has_newsletter_form": has_newsletter_form,
        "has_comment_section": has_comment_section,
        "has_social_share_buttons": has_social_share_buttons,
        "has_back_to_top": has_back_to_top,
        "has_pagination": has_pagination,
        "has_toc": has_toc,
        "has_rich_snippet_markup": has_rich_snippet_markup,
        "has_cart_button": has_cart_button,
        "has_price_display": has_price_display,
        # Header elements
        **header_data,
        # Footer elements
        **footer_data,
        # Page section detection
        **section_data,
        # UI structural patterns
        **ui_pattern_data,
        # Content signals
        "word_count": word_count,
        "has_author_info": has_author_info,
        "has_publish_date": has_publish_date,
        "has_map_embed": has_map_embed,
        "has_phone_links": has_phone_links,
        "has_email_links": has_email_links,
        # Page type
        "page_type_detected": page_type_detected,
    }


async def check_url_batch(urls: list[str], timeout: int = 10) -> list[dict]:
    async def _check_one(url: str) -> dict:
        try:
            async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=timeout) as client:
                start = time.monotonic()
                resp = await client.get(url)
                elapsed = int((time.monotonic() - start) * 1000)
                return {
                    "url": url,
                    "final_url": str(resp.url),
                    "status_code": resp.status_code,
                    "redirect_count": len(resp.history),
                    "response_time_ms": elapsed,
                }
        except httpx.TimeoutException:
            return {"url": url, "status_code": None, "error": "timeout"}
        except httpx.RequestError as e:
            return {"url": url, "status_code": None, "error": str(e)}

    batch = urls[:50]  # hard cap to avoid abuse
    results = await asyncio.gather(*[_check_one(u) for u in batch])
    return list(results)
