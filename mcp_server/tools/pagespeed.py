import httpx

_PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Metric thresholds (Good / Needs Improvement / Poor)
_THRESHOLDS = {
    "LCP": {"good": 2500, "poor": 4000},       # ms
    "FCP": {"good": 1800, "poor": 3000},        # ms
    "TBT": {"good": 200, "poor": 600},          # ms
    "CLS": {"good": 0.1, "poor": 0.25},         # unitless
    "INP": {"good": 200, "poor": 500},          # ms (replaces FID)
    "TTFB": {"good": 800, "poor": 1800},        # ms
}


def _rating(key: str, value: float) -> str:
    t = _THRESHOLDS.get(key)
    if t is None:
        return "unknown"
    if value <= t["good"]:
        return "good"
    if value <= t["poor"]:
        return "needs_improvement"
    return "poor"


def _extract_metric(audits: dict, audit_id: str) -> dict | None:
    audit = audits.get(audit_id)
    if not audit:
        return None
    numeric = audit.get("numericValue")
    display = audit.get("displayValue", "")
    score = audit.get("score")
    return {"raw": numeric, "display": display, "score": score}


async def check_pagespeed(url: str, strategy: str = "mobile", api_key: str = "") -> dict:
    params: dict = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "seo"],
    }
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.get(_PAGESPEED_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            return {"url": url, "strategy": strategy, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.RequestError as e:
            return {"url": url, "strategy": strategy, "error": str(e)}

    categories = data.get("lighthouseResult", {}).get("categories", {})
    audits = data.get("lighthouseResult", {}).get("audits", {})

    perf_score = int((categories.get("performance", {}).get("score") or 0) * 100)
    seo_score = int((categories.get("seo", {}).get("score") or 0) * 100)
    a11y_score = int((categories.get("accessibility", {}).get("score") or 0) * 100)

    # Core Web Vitals
    lcp_raw = (audits.get("largest-contentful-paint", {}).get("numericValue") or 0)
    fcp_raw = (audits.get("first-contentful-paint", {}).get("numericValue") or 0)
    tbt_raw = (audits.get("total-blocking-time", {}).get("numericValue") or 0)
    cls_raw = (audits.get("cumulative-layout-shift", {}).get("numericValue") or 0)
    inp_raw = (audits.get("interaction-to-next-paint", {}).get("numericValue") or 0)
    ttfb_raw = (audits.get("server-response-time", {}).get("numericValue") or 0)

    # Top opportunities (audits with type=opportunity and low score)
    opportunities: list[dict] = []
    for audit_id, audit in audits.items():
        if audit.get("details", {}).get("type") == "opportunity":
            score = audit.get("score")
            if score is not None and score < 0.9:
                savings_ms = audit.get("details", {}).get("overallSavingsMs", 0)
                opportunities.append({
                    "id": audit_id,
                    "title": audit.get("title", ""),
                    "score": score,
                    "savings_ms": savings_ms,
                })
    opportunities.sort(key=lambda x: x["score"])
    top_opportunities = opportunities[:5]

    return {
        "url": url,
        "strategy": strategy,
        "performance_score": perf_score,
        "seo_score": seo_score,
        "accessibility_score": a11y_score,
        "metrics": {
            "LCP": {"value_ms": round(lcp_raw), "display": audits.get("largest-contentful-paint", {}).get("displayValue", ""), "rating": _rating("LCP", lcp_raw)},
            "FCP": {"value_ms": round(fcp_raw), "display": audits.get("first-contentful-paint", {}).get("displayValue", ""), "rating": _rating("FCP", fcp_raw)},
            "TBT": {"value_ms": round(tbt_raw), "display": audits.get("total-blocking-time", {}).get("displayValue", ""), "rating": _rating("TBT", tbt_raw)},
            "CLS": {"value": round(cls_raw, 3), "display": audits.get("cumulative-layout-shift", {}).get("displayValue", ""), "rating": _rating("CLS", cls_raw)},
            "INP": {"value_ms": round(inp_raw), "display": audits.get("interaction-to-next-paint", {}).get("displayValue", ""), "rating": _rating("INP", inp_raw)},
            "TTFB": {"value_ms": round(ttfb_raw), "display": audits.get("server-response-time", {}).get("displayValue", ""), "rating": _rating("TTFB", ttfb_raw)},
        },
        "top_opportunities": top_opportunities,
    }
