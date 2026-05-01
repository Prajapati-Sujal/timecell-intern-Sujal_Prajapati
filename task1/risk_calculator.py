"""
Task 01 — Portfolio Risk Calculator
Timecell.ai Engineering Intern Assessment 2025

Computes crash-scenario risk metrics for a given portfolio,
including a moderate-crash bonus scenario and a CLI bar chart.
"""

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

@dataclass
class AssetRisk:
    name: str
    allocation_pct: float
    expected_crash_pct: float

    @property
    def risk_score(self) -> float:
        """Allocation-weighted crash magnitude (positive = worse)."""
        return self.allocation_pct * abs(self.expected_crash_pct)

    def crash_value(self, total_value: float, crash_scale: float = 1.0) -> float:
        """Value of this asset after a crash scaled by crash_scale (0–1)."""
        allocation_value = total_value * (self.allocation_pct / 100)
        crash_return = (self.expected_crash_pct / 100) * crash_scale
        return allocation_value * (1 + crash_return)


# ---------------------------------------------------------------------------
# Core metric computation
# ---------------------------------------------------------------------------

def compute_risk_metrics(portfolio: dict, crash_scale: float = 1.0) -> dict:
    """
    Compute risk metrics for a portfolio under a given crash scenario.

    Args:
        portfolio:   dict with keys total_value_inr, monthly_expenses_inr, assets
        crash_scale: 1.0 = full crash, 0.5 = moderate crash (50% of expected)

    Returns:
        dict with post_crash_value, runway_months, ruin_test,
             largest_risk_asset, concentration_warning
    """
    total_value: float = portfolio["total_value_inr"]
    monthly_expenses: float = portfolio["monthly_expenses_inr"]
    raw_assets: list[dict] = portfolio["assets"]

    # Validate allocations sum to ~100%
    total_alloc = sum(a["allocation_pct"] for a in raw_assets)
    if not (99.0 <= total_alloc <= 101.0):
        raise ValueError(f"Asset allocations sum to {total_alloc:.1f}%, expected arond 100%.")

    assets = [
        AssetRisk(
            name=a["name"],
            allocation_pct=a["allocation_pct"],
            expected_crash_pct=a["expected_crash_pct"],
        )
        for a in raw_assets
    ]

    # --- post_crash_value ---
    post_crash_value = sum(a.crash_value(total_value, crash_scale) for a in assets)

    # --- runway_months ---
    if monthly_expenses <= 0:
        runway_months = float("inf")
    else:
        runway_months = post_crash_value / monthly_expenses

    # --- ruin_test ---
    ruin_test: Literal["PASS", "FAIL"] = "PASS" if runway_months > 12 else "FAIL"

    # --- largest_risk_asset ---
    largest_risk_asset = max(assets, key=lambda a: a.risk_score).name

    # --- concentration_warning ---
    concentration_warning = any(a.allocation_pct > 40 for a in assets)

    return {
        "post_crash_value": round(post_crash_value, 2),
        "runway_months": round(runway_months, 1),
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning,
    }


def compute_both_scenarios(portfolio: dict) -> dict:
    """
    Bonus: Compute full crash AND moderate crash (50% severity) side by side.
    """
    return {
        "full_crash": compute_risk_metrics(portfolio, crash_scale=1.0),
        "moderate_crash": compute_risk_metrics(portfolio, crash_scale=0.5),
    }


# ---------------------------------------------------------------------------
# CLI bar chart (no external libraries)
# ---------------------------------------------------------------------------

def render_allocation_chart(portfolio: dict, bar_width: int = 40) -> str:
    """
    Renders a simple ASCII bar chart of asset allocations.
    No external plotting libraries used.
    """
    assets = portfolio["assets"]
    lines = ["\nPortfolio Allocation", "─" * (bar_width + 20)]

    for asset in assets:
        pct = asset["allocation_pct"]
        filled = int((pct / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        lines.append(f"  {asset['name']:<10} │{bar}│ {pct:>5.1f}%\n")

    lines.append("─" * (bar_width + 20))
    return "\n".join(lines)


def render_crash_bar(asset_name: str, pre: float, post: float, bar_width: int = 30) -> str:
    """Single asset before/after crash bar."""
    ratio = post / pre if pre > 0 else 0
    filled = int(ratio * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    return f"  {asset_name:<10} [{bar}] {ratio * 100:.1f}% remaining\n"