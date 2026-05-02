"""
Task 04 — Portfolio Scorecard Runner

No API keys. No LLM. Pure Python.
Run: python task04/main.py
"""

from scorecard import compute_scorecard, Scorecard

# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

DIVIDER = "═" * 62
THIN    = "─" * 62
COL_NAME  = 22
COL_GRADE = 5
COL_LABEL = 16


# ---------------------------------------------------------------------------
# Sample portfolios
# ---------------------------------------------------------------------------

PORTFOLIO_ASSESSMENT = {
    "name": "Assessment Portfolio  (BTC / NIFTY50 / GOLD / CASH)",
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct":   0},
    ],
}

PORTFOLIO_CONSERVATIVE = {
    "name": "Conservative Portfolio  (FD / GOLD / NIFTY50 / BTC)",
    "total_value_inr": 25_000_000,
    "monthly_expenses_inr": 150_000,
    "assets": [
        {"name": "FD",      "allocation_pct": 50, "expected_crash_pct":   0},
        {"name": "GOLD",    "allocation_pct": 25, "expected_crash_pct": -15},
        {"name": "NIFTY50", "allocation_pct": 15, "expected_crash_pct": -40},
        {"name": "BTC",     "allocation_pct": 10, "expected_crash_pct": -80},
    ],
}

PORTFOLIO_RISKY = {
    "name": "High-Risk Crypto Portfolio  (BTC / ETH / CASH)",
    "total_value_inr": 5_000_000,
    "monthly_expenses_inr": 120_000,
    "assets": [
        {"name": "BTC",  "allocation_pct": 60, "expected_crash_pct": -80},
        {"name": "ETH",  "allocation_pct": 30, "expected_crash_pct": -75},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct":   0},
    ],
}


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_scorecard(portfolio: dict) -> None:
    """Print a formatted scorecard for a portfolio."""
    card = compute_scorecard(portfolio)
    name = portfolio.get("name", "Portfolio")

    # Header
    print(f"\n{DIVIDER}")
    print(f"  TIMECELL.AI — Portfolio Scorecard")
    print(THIN)
    print(f"  {name}")
    print(DIVIDER)

    # Column headers
    print(
        f"\n  {'DIMENSION':<{COL_NAME}} "
        f"{'GRADE':<{COL_GRADE}} "
        f"{'RATING':<{COL_LABEL}} "
        f"DETAIL"
    )
    print(f"  {'─'*COL_NAME} {'─'*COL_GRADE} {'─'*COL_LABEL} {'─'*20}")

    # Dimension rows
    for r in card.dimensions:
        print(
            f"  {r.emoji} {r.name:<{COL_NAME - 2}} "
            f"{r.grade:<{COL_GRADE}} "
            f"{r.label:<{COL_LABEL}} "
            f"{r.detail}"
        )

    # Score bar
    print(f"\n  {'─' * 50}")
    filled = int((card.overall_score / 100) * 40)
    bar    = "█" * filled + "░" * (40 - filled)
    print(f"  Score  │{bar}│ {card.overall_score:.0f}/100")
    print(f"  {'─' * 50}")

    # Overall grade
    print(
        f"\n  {card.overall_emoji}  OVERALL GRADE : "
        f"{card.overall_grade}  —  {card.overall_label}"
    )
    print(f"\n  📝  {card.summary}")
    print(f"\n{DIVIDER}\n")


def main():
    print(f"\n{DIVIDER}")
    print("  TIMECELL.AI — Portfolio Scorecard")
    print("  Grade your portfolio across 5 risk dimensions.")
    print("  No API. No LLM. Pure math.")
    print(DIVIDER)

    for portfolio in [
        PORTFOLIO_ASSESSMENT,
        PORTFOLIO_CONSERVATIVE,
        PORTFOLIO_RISKY,
    ]:
        render_scorecard(portfolio)


if __name__ == "__main__":
    main()