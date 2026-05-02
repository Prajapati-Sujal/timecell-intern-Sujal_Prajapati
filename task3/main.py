"""
Task 03 — Runner
Demonstrates the explainer on multiple portfolios and all 3 tone levels.

Set your API key before running:
  Windows PowerShell : $env:GROQ_API_KEY = "gsk_..."
  Mac/Linux          : export GROQ_API_KEY="gsk_..."

Get a FREE key at: console.groq.com (no credit card required)

Run:
  cd task03
  python main.py
"""

import logging
from task3.explainer import explain_portfolio, critique_explanation
from task1.risk_calculator import compute_risk_metrics

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt= "%H:%M:%S",
)

# ---------------------------------------------------------------------------
# Sample portfolios
# ---------------------------------------------------------------------------

PORTFOLIO_AGGRESSIVE = {
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
    "total_value_inr": 5_000_000,
    "monthly_expenses_inr": 120_000,
    "assets": [
        {"name": "BTC",  "allocation_pct": 60, "expected_crash_pct": -80},
        {"name": "ETH",  "allocation_pct": 30, "expected_crash_pct": -75},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct":   0},
    ],
}

# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

DIVIDER = "═" * 68
THIN    = "─" * 68

VERDICT_STYLE = {
    "Aggressive":   ("🔴", "HIGH RISK"),
    "Balanced":     ("🟡", "MODERATE RISK"),
    "Conservative": ("🟢", "LOW RISK"),
}


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_explanation(output, label: str = "") -> None:
    """Pretty-print a parsed ExplainerOutput."""
    emoji, risk_label = VERDICT_STYLE.get(output.verdict, ("⚪", "UNKNOWN"))

    print(f"\n{THIN}")
    print(f"{label}")
    print(THIN)

    # Raw response — always shown (spec requirement)
    print("\n  RAW API RESPONSE (unmodified from Groq):")
    print()
    for line in output.raw_response.splitlines():
        print(f"    {line}")

    print(f"\n{THIN}")
    print("  PARSED STRUCTURED OUTPUT:")
    print(THIN)

    if output.missing_tags:
        print(f"\n  WARNING — Missing tags: {output.missing_tags}")

    print(f"\n  SUMMARY:")
    print(f"  {output.summary}\n")

    print(f"  DOING WELL:")
    print(f"  {output.doing_well}\n")

    print(f"  CONSIDER CHANGING:")
    print(f"  {output.consider_changing}\n")

    print(f"  {emoji}  VERDICT:  {output.verdict}  —  {risk_label}")
    print(f"  REASON:   {output.verdict_reason}")


def print_critique(critique) -> None:
    """Pretty-print a CriticOutput."""
    print(f"\n{THIN}")
    print("  🔍  CRITIC REVIEW  (second LLM call — adversarial accuracy check)")
    print(THIN)

    print("\n  RAW CRITIC RESPONSE (unmodified from Groq):")
    print()
    for line in critique.raw_response.splitlines():
        print(f"    {line}")

    print(f"\n{THIN}")
    print("  PARSED CRITIC OUTPUT:")
    print(THIN)

    if critique.missing_tags:
        print(f"\n  WARNING — Missing tags: {critique.missing_tags}")

    print(f"\n  ACCURACY CHECK:")
    print(f"  {critique.accuracy}\n")

    print(f"  MISSED RISKS:")
    print(f"  {critique.missed_risks}\n")

    print(f"  VERDICT REVIEW:")
    print(f"  {critique.verdict_review}")


def demo(portfolio: dict, name: str, tone: str, run_critic: bool = False) -> None:
    print(f"\n{DIVIDER}")
    print(f"  Portfolio : {name}")
    print(f"  Tone      : {tone.upper()}")
    print(f"  Model     : Groq — Llama 3.3 70B Versatile  (Free Tier)")
    print(DIVIDER)

    risk_metrics = compute_risk_metrics(portfolio)

    explanation = explain_portfolio(portfolio, tone=tone, risk_metrics=risk_metrics)
    print_explanation(explanation, label=f"Explanation  [{tone} tone]")

    if run_critic:
        critique = critique_explanation(portfolio, explanation)
        print_critique(critique)

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n{DIVIDER}")
    print("  TIMECELL.AI — AI-Powered Portfolio Explainer")
    print("  Powered by Groq  ·  Llama 3.3 70B Versatile  ·  Free Tier")
    print(DIVIDER)

    # Demo 1: Assessment portfolio — all 3 tones
    for tone in ["beginner", "experienced", "expert"]:
        demo(
            portfolio = PORTFOLIO_AGGRESSIVE,
            name      = "Assessment Portfolio  (BTC / NIFTY50 / GOLD / CASH)",
            tone      = tone,
        )

    # Demo 2: Conservative portfolio + critic review
    demo(
        portfolio  = PORTFOLIO_CONSERVATIVE,
        name       = "Conservative Portfolio  (FD / GOLD / NIFTY50 / BTC)",
        tone       = "experienced",
        run_critic = True,
    )

    # Demo 3: High-risk crypto portfolio
    demo(
        portfolio = PORTFOLIO_RISKY,
        name      = "High-Risk Crypto Portfolio  (BTC / ETH / CASH)",
        tone      = "beginner",
    )

    print(DIVIDER)
    print("All demos complete.")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()