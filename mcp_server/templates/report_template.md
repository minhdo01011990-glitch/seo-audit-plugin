# Báo Cáo SEO Audit — {{ config.domain }}

**Ngày tạo:** {{ generated_at }}
**Domain:** {{ config.domain }}
**Thương hiệu:** {{ config.brand_info }}
**Mục đích:** {{ config.audit_purpose }}
**Ngôn ngữ báo cáo:** {{ "Tiếng Việt" if config.language == "vi" else "English" }}

---

## Tổng Điểm SEO

| Chỉ số | Giá trị |
|--------|---------|
| **Điểm tổng thể** | {{ results.score.percentage }}% |
| **Xếp loại** | {{ results.score.grade }} |
| ✅ Đạt | {{ results.score.passed }} tiêu chí |
| ❌ Lỗi | {{ results.score.failed }} tiêu chí |
| ⚠️ Cần cải thiện | {{ results.score.warning }} tiêu chí |
| 🔍 Cần kiểm tra thủ công | {{ results.score.manual }} tiêu chí |

### Điểm Theo Nhóm

| Nhóm | Điểm | Xếp loại | Đạt | Lỗi | Cần cải thiện |
|------|------|----------|-----|-----|--------------|
{% for cat in results.score.categories -%}
| {{ cat.category }} | {{ cat.percentage }}% | {{ cat.grade }} | {{ cat.passed }} | {{ cat.failed }} | {{ cat.warning }} |
{% endfor %}

---

## Top 10 Vấn Đề Ưu Tiên Cần Xử Lý

{% for issue in results.top_issues %}
### {{ loop.index }}. {{ issue.name }}

- **Nhóm:** {{ issue.category }}
- **Mức độ ưu tiên:** {{ issue.priority | upper }}
- **Trạng thái:** {{ "❌ Lỗi" if issue.status == "failed" else "⚠️ Cần cải thiện" }}
- **Ghi nhận:** {{ issue.evidence if issue.evidence else "_Không có dữ liệu cụ thể_" }}
{% if issue.recommendation %}
- **Đề xuất xử lý:** {{ issue.recommendation }}
{% endif %}

{% endfor %}

---

## Chi Tiết Phân Tích Theo Nhóm

{% for cat_name, items in results.categories.items() %}
### {{ cat_name }}

| # | Tiêu chí | Mức độ | Trạng thái | Ghi nhận |
|---|----------|--------|-----------|----------|
{% for item in items -%}
| {{ loop.index }} | {{ item.name }} | {{ item.priority }} | {% if item.status == "passed" %}✅{% elif item.status == "failed" %}❌{% elif item.status == "warning" %}⚠️{% else %}🔍{% endif %} | {{ item.evidence | truncate(80) if item.evidence else "—" }} |
{% endfor %}

{% if config.include_recommendations %}
**Đề xuất cho nhóm này:**

{% for item in items if item.status in ("failed", "warning") and item.recommendation %}
- **{{ item.name }}:** {{ item.recommendation }}
{% endfor %}
{% endif %}

{% endfor %}

---

## Phân Tích UI / Giao Diện

{% if results.ui_results %}
{% for page_type, items in results.ui_results.items() %}
### {{ page_type | title | replace("_", " ") }}

| # | Tiêu chí | Mức độ | Trạng thái | Ghi chú |
|---|----------|--------|-----------|---------|
{% for item in items -%}
| {{ loop.index }} | {{ item.name }} | {{ item.priority }} | {% if item.status == "passed" %}✅{% elif item.status == "failed" %}❌{% elif item.status == "warning" %}⚠️{% else %}🔍{% endif %} | {{ item.evidence if item.evidence else item.manual_guide | truncate(60) if item.manual_guide else "—" }} |
{% endfor %}

{% endfor %}
{% else %}
_Dữ liệu UI chưa được phân tích._
{% endif %}

---

## Dữ Liệu PageSpeed Insights

{% if results.pagespeed %}
{% for strategy, ps_data in results.pagespeed.items() %}
### {{ strategy | title }}

| Metric | Giá trị | Đánh giá |
|--------|---------|---------|
| Performance Score | {{ ps_data.performance_score }}/100 | {{ "🟢 Tốt" if ps_data.performance_score >= 90 else "🟡 Cần cải thiện" if ps_data.performance_score >= 50 else "🔴 Kém" }} |
| LCP | {{ ps_data.metrics.LCP.display }} | {{ "🟢" if ps_data.metrics.LCP.rating == "good" else "🟡" if ps_data.metrics.LCP.rating == "needs_improvement" else "🔴" }} |
| CLS | {{ ps_data.metrics.CLS.display }} | {{ "🟢" if ps_data.metrics.CLS.rating == "good" else "🟡" if ps_data.metrics.CLS.rating == "needs_improvement" else "🔴" }} |
| TBT | {{ ps_data.metrics.TBT.display }} | {{ "🟢" if ps_data.metrics.TBT.rating == "good" else "🟡" if ps_data.metrics.TBT.rating == "needs_improvement" else "🔴" }} |
| FCP | {{ ps_data.metrics.FCP.display }} | {{ "🟢" if ps_data.metrics.FCP.rating == "good" else "🟡" if ps_data.metrics.FCP.rating == "needs_improvement" else "🔴" }} |

**Top cơ hội tối ưu:**
{% for opp in ps_data.top_opportunities %}
- {{ opp.title }} (tiết kiệm ~{{ (opp.savings_ms / 1000) | round(1) }}s)
{% endfor %}

{% endfor %}
{% else %}
_PageSpeed Insights không được chạy (không có API key hoặc bị bỏ qua)._
{% endif %}

---

## Roadmap Đề Xuất

### Tuần 1 — Xử lý lỗi Critical (mandatory + failed)

{% for issue in results.top_issues if issue.priority == "mandatory" and issue.status == "failed" %}
- [ ] {{ issue.name }}
{% endfor %}

### Tuần 2 — Tối ưu ưu tiên cao (high + failed/warning)

{% for issue in results.top_issues if issue.priority == "high" %}
- [ ] {{ issue.name }}
{% endfor %}

### Tuần 3-4 — Cải thiện bổ sung (nicetohave + manual checks)

{% for issue in results.top_issues if issue.priority == "nicetohave" or issue.status == "manual" %}
- [ ] {{ issue.name }}
{% endfor %}

---

_Báo cáo được tạo tự động bởi SEO Audit MCP Server_
_Một số tiêu chí (🔍) cần kiểm tra thủ công theo hướng dẫn trong chi tiết phân tích._
