import os
from pathlib import Path

import pandas as pd


# ── Screaming Frog ────────────────────────────────────────────────────────────

_SF_COLUMN_MAP = {
    # Canonical Screaming Frog column names (may vary by export type)
    "address": "url",
    "status_code": "status_code",
    "status": "status",
    "title_1": "title",
    "meta_description_1": "meta_description",
    "h1_1": "h1",
    "h2_1": "h2",
    "meta_robots_1": "meta_robots",
    "canonical_link_element_1": "canonical",
    "word_count": "word_count",
    "size": "size_bytes",
    "crawl_depth": "crawl_depth",
    "indexability": "indexability",
    "indexability_status": "indexability_status",
    "inlinks": "inlinks",
    "outlinks": "outlinks",
    "unique_inlinks": "unique_inlinks",
    "redirect_url": "redirect_url",
    "redirect_type": "redirect_type",
    "alt_text": "alt_text",
    "image_src": "image_src",
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    rename_map = {k: v for k, v in _SF_COLUMN_MAP.items() if k in df.columns}
    return df.rename(columns=rename_map)


def parse_screaming_frog(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(path, dtype=str)
        else:
            df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}

    df = _normalise_columns(df)
    df = df.fillna("")

    total = len(df)

    # Status codes
    status_counts: dict[str, int] = {}
    if "status_code" in df.columns:
        status_counts = df["status_code"].value_counts().to_dict()

    # Missing titles
    missing_titles = []
    if "title" in df.columns and "url" in df.columns:
        mask = df["title"].str.strip() == ""
        missing_titles = df.loc[mask, "url"].tolist()

    # Duplicate titles
    duplicate_titles: list[dict] = []
    if "title" in df.columns and "url" in df.columns:
        dup_mask = df["title"].str.strip() != ""
        dup_df = df[dup_mask]
        dupes = dup_df[dup_df.duplicated("title", keep=False)]
        for title_val, group in dupes.groupby("title"):
            duplicate_titles.append({
                "title": title_val,
                "urls": group["url"].tolist(),
            })

    # Missing meta descriptions
    missing_meta = []
    if "meta_description" in df.columns and "url" in df.columns:
        mask = df["meta_description"].str.strip() == ""
        missing_meta = df.loc[mask, "url"].tolist()

    # Missing H1
    missing_h1 = []
    if "h1" in df.columns and "url" in df.columns:
        mask = df["h1"].str.strip() == ""
        missing_h1 = df.loc[mask, "url"].tolist()

    # 4xx/5xx errors
    error_urls: list[dict] = []
    if "status_code" in df.columns and "url" in df.columns:
        error_mask = df["status_code"].str.match(r"^[45]\d{2}$", na=False)
        for _, row in df[error_mask].iterrows():
            error_urls.append({"url": row.get("url", ""), "status_code": row.get("status_code", "")})

    # Images missing alt text — None means "column not present in this export"
    # (SF Images tab export has alt_text + image_src; All Crawl Data export does not)
    images_no_alt: list[str] | None = None
    if "alt_text" in df.columns and "image_src" in df.columns:
        mask = df["alt_text"].str.strip() == ""
        images_no_alt = df.loc[mask, "image_src"].tolist()

    # Non-indexable pages
    non_indexable: list[dict] = []
    if "indexability" in df.columns and "url" in df.columns:
        mask = df["indexability"].str.lower() != "indexable"
        for _, row in df[mask].iterrows():
            non_indexable.append({
                "url": row.get("url", ""),
                "reason": row.get("indexability_status", ""),
            })

    return {
        "file": str(path),
        "total_urls": total,
        "status_code_breakdown": status_counts,
        "missing_titles": missing_titles[:50],
        "duplicate_titles": duplicate_titles[:20],
        "missing_meta_descriptions": missing_meta[:50],
        "missing_h1": missing_h1[:50],
        "error_urls": error_urls[:50],
        "images_missing_alt": images_no_alt[:50] if images_no_alt is not None else None,
        "non_indexable": non_indexable[:50],
    }


# ── Google Search Console ─────────────────────────────────────────────────────

def parse_gsc_data(file_path: str, report_type: str = "performance") -> dict:
    """
    report_type: 'performance' | 'coverage'
    Performance CSV columns: Query, Page, Clicks, Impressions, CTR, Position
    Coverage CSV columns: URL, Status, Reason, Last crawled
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.fillna("")

    if report_type == "performance":
        return _parse_gsc_performance(df, str(path))
    elif report_type == "coverage":
        return _parse_gsc_coverage(df, str(path))
    else:
        return {"error": f"Unknown report_type: {report_type}. Use 'performance' or 'coverage'."}


def _parse_gsc_performance(df: pd.DataFrame, file: str) -> dict:
    total_rows = len(df)

    # Numeric conversion
    for col in ("clicks", "impressions", "ctr", "position"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace("%", "").str.strip(), errors="coerce")

    total_clicks = int(df["clicks"].sum()) if "clicks" in df.columns else 0
    total_impressions = int(df["impressions"].sum()) if "impressions" in df.columns else 0
    avg_ctr = round(float(df["ctr"].mean()), 4) if "ctr" in df.columns else 0.0
    avg_position = round(float(df["position"].mean()), 2) if "position" in df.columns else 0.0

    # Top queries by clicks
    top_queries: list[dict] = []
    if "query" in df.columns and "clicks" in df.columns:
        top_q = df.sort_values("clicks", ascending=False).head(20)
        for _, row in top_q.iterrows():
            top_queries.append({
                "query": row.get("query", ""),
                "clicks": int(row.get("clicks") or 0),
                "impressions": int(row.get("impressions") or 0),
                "ctr": round(float(row.get("ctr") or 0), 4),
                "position": round(float(row.get("position") or 0), 1),
            })

    # Low CTR high impression queries (opportunity)
    opportunities: list[dict] = []
    if all(c in df.columns for c in ("query", "impressions", "ctr", "position")):
        mask = (df["impressions"] > 100) & (df["ctr"] < 0.02) & (df["position"] <= 20)
        for _, row in df[mask].sort_values("impressions", ascending=False).head(20).iterrows():
            opportunities.append({
                "query": row.get("query", ""),
                "impressions": int(row.get("impressions") or 0),
                "ctr": round(float(row.get("ctr") or 0), 4),
                "position": round(float(row.get("position") or 0), 1),
            })

    return {
        "file": file,
        "report_type": "performance",
        "total_queries": total_rows,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "avg_ctr": avg_ctr,
        "avg_position": avg_position,
        "top_queries": top_queries,
        "low_ctr_opportunities": opportunities,
    }


def _parse_gsc_coverage(df: pd.DataFrame, file: str) -> dict:
    total_rows = len(df)

    # Status breakdown
    status_col = next((c for c in df.columns if "status" in c), None)
    status_counts: dict[str, int] = {}
    if status_col:
        status_counts = df[status_col].value_counts().to_dict()

    # Valid vs excluded vs error
    valid_urls: list[str] = []
    excluded_urls: list[dict] = []
    error_urls: list[dict] = []

    url_col = next((c for c in df.columns if c in ("url", "page")), None)
    reason_col = next((c for c in df.columns if "reason" in c), None)

    if url_col and status_col:
        for _, row in df.iterrows():
            url = row.get(url_col, "")
            status = str(row.get(status_col, "")).lower()
            reason = str(row.get(reason_col, "")) if reason_col else ""
            if "valid" in status and "excluded" not in status:
                valid_urls.append(url)
            elif "excluded" in status or "error" not in status:
                excluded_urls.append({"url": url, "reason": reason})
            else:
                error_urls.append({"url": url, "reason": reason})

    return {
        "file": file,
        "report_type": "coverage",
        "total_urls": total_rows,
        "status_breakdown": status_counts,
        "valid_count": len(valid_urls),
        "excluded_count": len(excluded_urls),
        "error_count": len(error_urls),
        "excluded_urls": excluded_urls[:50],
        "error_urls": error_urls[:50],
    }


# ── Ahrefs ────────────────────────────────────────────────────────────────────

def parse_ahrefs(file_path: str) -> dict:
    """Parse Ahrefs broken links / site audit export CSV."""
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.fillna("")

    total = len(df)

    # Detect URL column
    url_col = next((c for c in df.columns if c in ("url", "source", "broken_link", "target_url")), None)
    http_code_col = next((c for c in df.columns if "http" in c or "status" in c or "code" in c), None)
    source_col = next((c for c in df.columns if c in ("referring_page", "source", "from")), None)

    broken_links: list[dict] = []
    if url_col and http_code_col:
        error_mask = df[http_code_col].str.match(r"^[45]\d{2}$", na=False)
        for _, row in df[error_mask].iterrows():
            broken_links.append({
                "url": row.get(url_col, ""),
                "status_code": row.get(http_code_col, ""),
                "referring_page": row.get(source_col, "") if source_col else "",
            })

    return {
        "file": str(path),
        "total_rows": total,
        "broken_links": broken_links[:100],
        "broken_count": len(broken_links),
    }
