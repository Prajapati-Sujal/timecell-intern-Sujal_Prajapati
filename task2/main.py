"""
Task 02 — Runner
Run: python task02/main.py
"""

from fetcher import fetch_all_assets
from display import render_table


def main():
    print("\n" + "═" * 70)
    print("  TIMECELL.AI — Live Market Data Fetcher")
    print("═" * 70)

    results = fetch_all_assets()
    render_table(results)


if __name__ == "__main__":
    main()