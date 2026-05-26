from dataclasses import dataclass, field


PRIORITY_WEIGHTS = {
    "mandatory": 3,
    "high": 2,
    "nicetohave": 1,
}

STATUS_VALUES = {
    "passed": 1.0,
    "warning": 0.5,
    "failed": 0.0,
    "manual": None,  # excluded from auto score
}

GRADE_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0, "F"),
]


@dataclass
class ChecklistResult:
    id: str
    name: str
    category: str
    priority: str
    status: str          # passed | failed | warning | manual
    evidence: str = ""   # what was observed
    recommendation: str = ""  # fix suggestion (if include_recommendations=True)


@dataclass
class CategoryScore:
    category: str
    earned_points: float
    max_points: float
    percentage: float
    grade: str
    passed: int
    failed: int
    warning: int
    manual: int
    items: list[ChecklistResult] = field(default_factory=list)


@dataclass
class AuditScore:
    total_earned: float
    total_max: float
    percentage: float
    grade: str
    passed: int
    failed: int
    warning: int
    manual: int
    categories: list[CategoryScore] = field(default_factory=list)


def _compute_grade(percentage: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if percentage >= threshold:
            return grade
    return "F"


def score_category(items: list[ChecklistResult]) -> CategoryScore:
    if not items:
        return CategoryScore(
            category="",
            earned_points=0,
            max_points=0,
            percentage=0,
            grade="F",
            passed=0,
            failed=0,
            warning=0,
            manual=0,
            items=[],
        )

    category = items[0].category
    earned = 0.0
    max_pts = 0.0
    passed = failed = warning = manual = 0

    for item in items:
        weight = PRIORITY_WEIGHTS.get(item.priority, 1)
        value = STATUS_VALUES.get(item.status)

        if value is None:
            # manual check — excluded from scoring
            manual += 1
            continue

        max_pts += weight
        earned += weight * value

        if item.status == "passed":
            passed += 1
        elif item.status == "failed":
            failed += 1
        elif item.status == "warning":
            warning += 1

    percentage = round((earned / max_pts * 100) if max_pts > 0 else 0, 1)
    grade = _compute_grade(percentage)

    return CategoryScore(
        category=category,
        earned_points=round(earned, 2),
        max_points=round(max_pts, 2),
        percentage=percentage,
        grade=grade,
        passed=passed,
        failed=failed,
        warning=warning,
        manual=manual,
        items=items,
    )


def score_audit(results_by_category: dict[str, list[ChecklistResult]]) -> AuditScore:
    category_scores: list[CategoryScore] = []
    total_earned = 0.0
    total_max = 0.0
    total_passed = total_failed = total_warning = total_manual = 0

    for category, items in results_by_category.items():
        cat_score = score_category(items)
        cat_score.category = category
        category_scores.append(cat_score)
        total_earned += cat_score.earned_points
        total_max += cat_score.max_points
        total_passed += cat_score.passed
        total_failed += cat_score.failed
        total_warning += cat_score.warning
        total_manual += cat_score.manual

    percentage = round((total_earned / total_max * 100) if total_max > 0 else 0, 1)
    grade = _compute_grade(percentage)

    return AuditScore(
        total_earned=round(total_earned, 2),
        total_max=round(total_max, 2),
        percentage=percentage,
        grade=grade,
        passed=total_passed,
        failed=total_failed,
        warning=total_warning,
        manual=total_manual,
        categories=category_scores,
    )


def get_top_issues(
    results_by_category: dict[str, list[ChecklistResult]],
    n: int = 10,
) -> list[ChecklistResult]:
    """Return top N failed/warning items sorted by priority weight."""
    issues: list[ChecklistResult] = []
    for items in results_by_category.values():
        for item in items:
            if item.status in ("failed", "warning"):
                issues.append(item)

    issues.sort(
        key=lambda x: PRIORITY_WEIGHTS.get(x.priority, 0),
        reverse=True,
    )
    return issues[:n]


def audit_score_to_dict(score: AuditScore) -> dict:
    return {
        "total_earned": score.total_earned,
        "total_max": score.total_max,
        "percentage": score.percentage,
        "grade": score.grade,
        "summary": {
            "passed": score.passed,
            "failed": score.failed,
            "warning": score.warning,
            "manual": score.manual,
        },
        "categories": [
            {
                "category": c.category,
                "earned": c.earned_points,
                "max": c.max_points,
                "percentage": c.percentage,
                "grade": c.grade,
                "passed": c.passed,
                "failed": c.failed,
                "warning": c.warning,
                "manual": c.manual,
            }
            for c in score.categories
        ],
    }
