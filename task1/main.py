"""
Task 01 — Runner
Run: python task01/main.py
"""

from risk_calculator import (
    compute_risk_metrics,
    compute_both_scenarios,
    render_allocation_chart,
    render_crash_bar,
)

# ---------------------------------------------------------------------------
# Sample portfolio (from the assessment)
# ---------------------------------------------------------------------------

portfolio = {
    "total_value_inr": 10_000_000,   # ₹1 Crore
    "monthly_expenses_inr": 80_000,
    "assets" : [
        {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct":   0},
    ],
}


def print_metrics(label: str, metrics: dict) -> None:
    """Pretty-print a metrics dictionary."""
    total = portfolio["total_value_inr"]
    post  = metrics["post_crash_value"]
    loss  = total - post

    print(f"\n{'═' * 50}")
    print(f"  {label}")
    print(f"{'═' * 50}")
    print(f"  Pre-crash value      : ₹{total:>15,.2f}")
    print(f"  Post-crash value     : ₹{post:>15,.2f}")
    print(f"  Total loss           : ₹{loss:>15,.2f}  ({loss/total*100:.1f}%)")
    print(f"  Runway (months)      : {metrics['runway_months']:<6.1f}")
    print(f"  Ruin test            : {metrics['ruin_test']}")
    print(f"  Largest risk asset   : {metrics['largest_risk_asset']}")
    print(f"  Concentration warning: {'YES' if metrics['concentration_warning'] else 'NO'}")

    # Per-asset crash bars
    print("\n  Asset survival after crash:\n")
    for asset in portfolio["assets"]:
        alloc_value = total * (asset["allocation_pct"] / 100)
        # Derive crash scale from label
        scale = 0.5 if "moderate" in label.lower() else 1.0
        post_asset = alloc_value * (1 + (asset["expected_crash_pct"] / 100) * scale)
        print(render_crash_bar(asset["name"], alloc_value, post_asset))


def main():
    print("\n" + "═" * 50)
    print("  TIMECELL.AI — Portfolio Risk Calculator")
    print("═" * 50)

    # Allocation chart
    print(render_allocation_chart(portfolio))

    # Both scenarios
    scenarios = compute_both_scenarios(portfolio)
    print_metrics("FULL CRASH SCENARIO", scenarios["full_crash"])
    print_metrics("MODERATE CRASH SCENARIO (50% severity)", scenarios["moderate_crash"])

    print(f"\n{'═' * 50}\n")


if __name__ == "__main__":
    main()