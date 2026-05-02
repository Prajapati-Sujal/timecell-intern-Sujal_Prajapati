"""
Task 04 — Portfolio Scorecard

Takes any portfolio → grades it across 5 risk dimensions → outputs a
clean letter-grade report card a wealth manager could show a client.

"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Grade scale
# ---------------------------------------------------------------------------

GRADE_SCALE = [
    (95, "A+", "Exceptional"),
    (88, "A",  "Excellent"),
    (80, "A-", "Very Good"),
    (73, "B+", "Good"),
    (65, "B",  "Above Average"),
    (58, "B-", "Adequate"),
    (50, "C+", "Below Average"),
    (42, "C",  "Weak"),
    (35, "C-", "Poor"),
    (25, "D",  "Dangerous"),
    (0,  "F",  "Critical Risk"),
]

 
DIMENSION_WEIGHTS = {
    "Crash Survival":     0.30,   # most important — raw survival
    "Runway Coverage":    0.30,   # equally important — can you live through it
    "Concentration Risk": 0.20,   # important but context-dependent
    "Asset Diversity":    0.10,   # useful signal, not decisive
    "Overall Risk Load":  0.10,   # partially captured by crash survival
}


def _score_to_grade(score: float) -> tuple[str, str]:
    """Convert a 0–100 score to a letter grade and label."""
    for threshold, grade, label in GRADE_SCALE:
        if score >= threshold:
            return grade, label
    return "F", "Critical Risk"


def _grade_emoji(grade: str) -> str:
    if grade.startswith("A"):  return "🟢"
    if grade.startswith("B"):  return "🟡"
    if grade.startswith("C"):  return "🟠"
    return "🔴"


# ---------------------------------------------------------------------------
# Replaces step functions with smooth scoring.
# ---------------------------------------------------------------------------

def _interpolate(value: float, anchors: list[tuple[float, float]]) -> float:
    """
    Linearly interpolate a score from a set of (metric_value, score) anchors.
    anchors must be sorted descending by metric_value.

    Example:
        anchors = [(100, 100), (70, 75), (40, 40), (0, 5)]
        value = 55 → interpolates between (70, 75) and (40, 40)
        result = 75 + (55-70)/(40-70) * (40-75) = 75 + 0.5*(-35) = 57.5
    """
    # Above highest anchor
    if value >= anchors[0][0]:
        return anchors[0][1]

    # Below lowest anchor
    if value <= anchors[-1][0]:
        return anchors[-1][1]

    # Find bracket
    for i in range(len(anchors) - 1):
        high_val, high_score = anchors[i]
        low_val,  low_score  = anchors[i + 1]
        if low_val <= value <= high_val:
            t = (value - low_val) / (high_val - low_val)
            return low_score + t * (high_score - low_score)

    return anchors[-1][1]


# ---------------------------------------------------------------------------
# Individual dimension scorers
# ---------------------------------------------------------------------------

def _score_crash_survival(portfolio: dict) -> tuple[float, str]:
    """
    How much of the portfolio survives a full crash?
    Scored on post-crash retention percentage — linearly interpolated.
    """
    total  = portfolio["total_value_inr"]
    assets = portfolio["assets"]

    post_crash = sum(
        total * (a["allocation_pct"] / 100) * (1 + a["expected_crash_pct"] / 100)
        for a in assets
    )
    retention_pct = (post_crash / total) * 100

    # Anchors: (retention_pct, score)
    anchors = [
        (100, 100),
        (90,  95),
        (80,  82),
        (70,  68),
        (60,  54),
        (50,  40),
        (40,  25),
        (30,  12),
        (0,    5),
    ]
    score  = _interpolate(retention_pct, anchors)
    detail = f"{retention_pct:.1f}% of portfolio survives a full crash"
    return round(score, 1), detail


def _score_runway(portfolio: dict) -> tuple[float, str]:
    """
    How many months can the post-crash portfolio cover expenses?
    Score based on runway in months.
    """
    total    = portfolio["total_value_inr"]
    expenses = portfolio["monthly_expenses_inr"]
    assets   = portfolio["assets"]

    if expenses <= 0:
        return 100.0, "No monthly expenses — infinite runway"

    post_crash = sum(
        total * (a["allocation_pct"] / 100) * (1 + a["expected_crash_pct"] / 100)
        for a in assets
    )
    runway = post_crash / expenses

    # Anchors: (runway_months, score)
    anchors = [
        (120, 100),
        (84,   88),
        (60,   75),
        (36,   60),
        (24,   48),
        (12,   32),
        (6,    18),
        (0,     5),
    ]
    score  = _interpolate(runway, anchors)
    detail = f"{runway:.1f} months of post-crash runway"
    return round(score, 1), detail


def _score_concentration(portfolio: dict) -> tuple[float, str]:
    """
    Is any single asset dangerously over-weighted?
    Penalises heavy concentration in volatile assets.
    """
    assets = portfolio["assets"]

    # Find the asset with highest raw allocation
    max_asset   = max(assets, key=lambda a: a["allocation_pct"])
    max_alloc   = max_asset["allocation_pct"]
    crash_mag   = abs(max_asset["expected_crash_pct"])

    # Risk-adjusted concentration: how dangerous is this concentration?
    risk_adjusted = max_alloc * (crash_mag / 100)

    # Anchors: (risk_adjusted_score, score)
    # risk_adjusted = 0   → asset is safe (like FD, CASH) → no penalty
    # risk_adjusted = 40  → moderately risky concentration
    # risk_adjusted = 64  → 80% BTC = catastrophic
    anchors = [
        (64,  8),   # worst: 80% BTC
        (50, 22),
        (40, 38),
        (30, 52),
        (20, 68),
        (10, 82),
        (5,  92),
        (0,  98),   # best: safe asset (FD/CASH) → no penalty
    ]

    # Apply crash penalty — up to -20 pts if concentrated in volatile asset
    score = _interpolate(risk_adjusted, anchors)

    detail = (
        f"Largest position: {max_asset['name']} at {max_alloc}% "
        f"(crash: {max_asset['expected_crash_pct']}%, "
        f"risk-adjusted concentration: {risk_adjusted:.0f})"
    )
    return round(score, 1), detail


def _score_diversity(portfolio: dict) -> tuple[float, str]:
    """
    How well diversified across uncorrelated asset types?
    Keyword-based classification into buckets.
    """
    assets = portfolio["assets"]

    # Classify assets into buckets
    crypto_keywords = {"BTC", "ETH", "CRYPTO", "SOL", "XRP"}
    equity_keywords = {"NIFTY", "SENSEX", "NIFTY50", "STOCK", "EQUITY",
                       "SMALLCAP", "MIDCAP", "LARGECAP"}
    stable_keywords = {"GOLD", "FD", "CASH", "BOND", "DEBT", "SILVER"}

    buckets = {"crypto": 0.0, "equity": 0.0, "stable": 0.0, "other": 0.0}

    for asset in assets:
        name = asset["name"].upper()
        if any(k in name for k in crypto_keywords):
            buckets["crypto"] += asset["allocation_pct"]
        elif any(k in name for k in equity_keywords):
            buckets["equity"] += asset["allocation_pct"]
        elif any(k in name for k in stable_keywords):
            buckets["stable"] += asset["allocation_pct"]
        else:
            buckets["other"]  += asset["allocation_pct"]

    # Count how many buckets have meaningful allocation (>5%)
    active_buckets = sum(1 for v in buckets.values() if v > 5)

    # Base score from number of meaningful asset classes
    base_scores = {1: 20, 2: 55, 3: 82, 4: 95}
    score = base_scores.get(active_buckets, 95)

    # Penalise if one bucket dominates (> 80%)
    dominant = max(buckets.values())
    if dominant > 80:
        score = max(score - 20, 5)

    active_names = [k for k, v in buckets.items() if v > 5]
    detail = (
        f"{active_buckets} asset class(es): "
        f"{', '.join(active_names)}"
    )
    return float(score), detail


def _score_ruin_risk(portfolio: dict) -> tuple[float, str]:
    """
    Weighted-average crash exposure across the whole portfolio.
    Lower weighted crash = better score. Linearly interpolated.
    """
    assets = portfolio["assets"]
    weighted_crash = sum(
        (a["allocation_pct"] / 100) * abs(a["expected_crash_pct"])
        for a in assets
    )

    # Anchors: (weighted_crash_pct, score)
    anchors = [
        (80,  8),
        (60, 18),
        (50, 33),
        (40, 48),
        (30, 62),
        (20, 78),
        (10, 92),
        (0, 100),
    ]
    score  = _interpolate(weighted_crash, anchors)
    detail = f"Weighted crash exposure: {weighted_crash:.1f}% of portfolio at risk"
    return round(score, 1), detail


# ---------------------------------------------------------------------------
# Dimension config — order controls display order
# ---------------------------------------------------------------------------

DIMENSIONS = [
    ("Crash Survival",     _score_crash_survival),
    ("Runway Coverage",    _score_runway),
    ("Concentration Risk", _score_concentration),
    ("Asset Diversity",    _score_diversity),
    ("Overall Risk Load",  _score_ruin_risk),
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class DimensionResult:
    name:   str
    score:  float
    grade:  str
    label:  str
    detail: str
    emoji:  str
    weight: float


@dataclass
class Scorecard:
    dimensions:    list[DimensionResult]
    overall_score: float
    overall_grade: str
    overall_label: str
    overall_emoji: str
    summary:       str


# ---------------------------------------------------------------------------
# Summary generator
# ---------------------------------------------------------------------------

def _build_summary(grade: str, results: list[DimensionResult]) -> str:
    """Generate a one-line plain-English portfolio verdict."""
    weakest   = min(results, key=lambda r: r.score)
    strongest = max(results, key=lambda r: r.score)

    if grade.startswith("A"):
        return (
            f"Well-structured portfolio with strong scores across all dimensions. "
            f"Best feature: {strongest.name}."
        )
    if grade.startswith("B"):
        return (
            f"Solid portfolio with room to improve. "
            f"Biggest strength: {strongest.name}. "
            f"Focus area: {weakest.name}."
        )
    if grade.startswith("C"):
        return (
            f"Portfolio carries meaningful risk. "
            f"{weakest.name} needs attention. "
            f"Consider reducing volatile asset exposure."
        )
    return (
        f"High-risk portfolio. {weakest.name} is at critical levels. "
        f"Significant restructuring recommended."
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute_scorecard(portfolio: dict) -> Scorecard:
    """
    Compute the full portfolio scorecard.
    Each dimension scored 0–100, letter graded, then averaged for overall.
    """
    results = []
    for name, scorer_fn in DIMENSIONS:
        score, detail = scorer_fn(portfolio)
        grade, label  = _score_to_grade(score)
        weight        = DIMENSION_WEIGHTS[name]
        results.append(DimensionResult(
            name   = name,
            score  = score,
            grade  = grade,
            label  = label,
            detail = detail,
            emoji  = _grade_emoji(grade),
            weight = weight,
        ))

    overall_score = sum(r.score * r.weight for r in results)
    overall_grade, overall_label = _score_to_grade(overall_score)

    return Scorecard(
        dimensions    = results,
        overall_score = round(overall_score, 1),
        overall_grade = overall_grade,
        overall_label = overall_label,
        overall_emoji = _grade_emoji(overall_grade),
        summary       = _build_summary(overall_grade, results),
    )