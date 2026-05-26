import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import httpx


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SEOAuditBot/1.0)",
}


async def check_robots(domain: str) -> dict:
    base = domain if domain.startswith("http") else f"https://{domain}"
    robots_url = urljoin(base.rstrip("/") + "/", "robots.txt")
    llms_url = urljoin(base.rstrip("/") + "/", "llms.txt")

    result = {
        "robots_url": robots_url,
        "robots_exists": False,
        "robots_content": "",
        "googlebot_allowed": True,
        "googlebot_disallowed_paths": [],
        "sitemap_in_robots": [],
        "has_llms_txt": False,
        "llms_txt_url": llms_url,
        "errors": [],
    }

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=10) as client:
        # robots.txt
        try:
            r = await client.get(robots_url)
            if r.status_code == 200:
                result["robots_exists"] = True
                content = r.text
                result["robots_content"] = content
                # Parse directives
                current_agent: list[str] = []
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        continue
                    key, _, value = line.partition(":")
                    key = key.strip().lower()
                    value = value.strip()
                    if key == "user-agent":
                        current_agent = [v.strip().lower() for v in value.split(",")]
                    elif key == "disallow":
                        if any(a in ("googlebot", "*") for a in current_agent):
                            if value:
                                result["googlebot_disallowed_paths"].append(value)
                    elif key == "sitemap":
                        result["sitemap_in_robots"].append(value)
                # Check if Googlebot is effectively blocked
                critical_blocks = [p for p in result["googlebot_disallowed_paths"] if p in ("/", "")]
                if critical_blocks:
                    result["googlebot_allowed"] = False
            else:
                result["errors"].append(f"robots.txt returned {r.status_code}")
        except httpx.RequestError as e:
            result["errors"].append(f"robots.txt fetch error: {e}")

        # llms.txt
        try:
            r2 = await client.get(llms_url)
            result["has_llms_txt"] = r2.status_code == 200
        except httpx.RequestError:
            result["has_llms_txt"] = False

    return result


async def check_sitemap(domain: str, validate_urls: bool = False, max_validate: int = 20) -> dict:
    base = domain if domain.startswith("http") else f"https://{domain}"
    sitemap_url = urljoin(base.rstrip("/") + "/", "sitemap.xml")

    result = {
        "sitemap_url": sitemap_url,
        "sitemap_exists": False,
        "is_index": False,
        "child_sitemaps": [],
        "url_count": 0,
        "urls": [],
        "invalid_urls": [],
        "has_lastmod": False,
        "errors": [],
    }

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        try:
            r = await client.get(sitemap_url)
            if r.status_code != 200:
                result["errors"].append(f"sitemap.xml returned {r.status_code}")
                return result
            result["sitemap_exists"] = True
            xml_content = r.text
        except httpx.RequestError as e:
            result["errors"].append(f"sitemap fetch error: {e}")
            return result

    try:
        root = ET.fromstring(xml_content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        # Detect sitemap index
        sitemaps = root.findall("sm:sitemap", ns)
        if sitemaps:
            result["is_index"] = True
            child_urls = [sm.findtext("sm:loc", namespaces=ns) for sm in sitemaps if sm.findtext("sm:loc", namespaces=ns)]
            result["child_sitemaps"] = child_urls
            # Aggregate URLs from first child sitemap
            if child_urls:
                async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
                    try:
                        cr = await client.get(child_urls[0])
                        if cr.status_code == 200:
                            child_root = ET.fromstring(cr.text)
                            urls = _extract_urls_from_sitemap(child_root, ns)
                            result["urls"] = urls[:100]
                            result["url_count"] = len(urls)
                    except (httpx.RequestError, ET.ParseError):
                        pass
        else:
            urls = _extract_urls_from_sitemap(root, ns)
            result["urls"] = urls[:100]
            result["url_count"] = len(urls)
            # Check lastmod
            first_url = root.find("sm:url", ns)
            if first_url is not None and first_url.find("sm:lastmod", ns) is not None:
                result["has_lastmod"] = True
    except ET.ParseError as e:
        result["errors"].append(f"XML parse error: {e}")
        return result

    if validate_urls and result["urls"]:
        to_validate = result["urls"][:max_validate]
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=10) as client:
            for url_entry in to_validate:
                url = url_entry if isinstance(url_entry, str) else url_entry.get("loc", "")
                if not url:
                    continue
                try:
                    resp = await client.get(url)
                    if resp.status_code >= 400:
                        result["invalid_urls"].append({"url": url, "status": resp.status_code})
                except httpx.RequestError as e:
                    result["invalid_urls"].append({"url": url, "error": str(e)})

    return result


def _extract_urls_from_sitemap(root: ET.Element, ns: dict) -> list[dict]:
    urls = []
    for url_el in root.findall("sm:url", ns):
        loc = url_el.findtext("sm:loc", namespaces=ns) or ""
        lastmod = url_el.findtext("sm:lastmod", namespaces=ns) or ""
        changefreq = url_el.findtext("sm:changefreq", namespaces=ns) or ""
        priority = url_el.findtext("sm:priority", namespaces=ns) or ""
        if loc:
            urls.append({"loc": loc, "lastmod": lastmod, "changefreq": changefreq, "priority": priority})
    return urls


async def check_redirect_chain(url: str, max_redirects: int = 10) -> dict:
    chain: list[dict] = []
    async with httpx.AsyncClient(
        headers=_HEADERS,
        follow_redirects=True,
        max_redirects=max_redirects,
        timeout=15,
    ) as client:
        try:
            resp = await client.get(url)
            for r in resp.history:
                chain.append({"url": str(r.url), "status": r.status_code})
            chain.append({"url": str(resp.url), "status": resp.status_code})
        except httpx.TooManyRedirects:
            return {"url": url, "error": "Too many redirects (possible loop)", "chain": chain}
        except httpx.RequestError as e:
            return {"url": url, "error": str(e), "chain": chain}

    has_loop = len(set(c["url"] for c in chain)) < len(chain)
    return {
        "url": url,
        "final_url": chain[-1]["url"] if chain else url,
        "redirect_count": len(chain) - 1,
        "chain": chain,
        "has_loop": has_loop,
        "too_many_hops": len(chain) - 1 > 3,
    }
