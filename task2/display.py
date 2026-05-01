"""
Task 02 — Terminal Table Renderer
Draws a clean Unicode box table. No external libraries.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fetcher import AssetPrice

IST = timezone(timedelta(hours=5, minutes=30))

# Column widths
COL_ASSET = 12
COL_PRICE = 16
COL_CURRENCY = 12
COL_SOURCE = 28
COL_TIME = 25

def _row(asset: str, price: str, currency: str, source: str,time : str) -> str:
    return (
        f"│ {asset:<{COL_ASSET}} "
        f"│ {price:<{COL_PRICE}} "
        f"│ {currency:<{COL_CURRENCY}} "
        f"│ {source:<{COL_SOURCE}} "
        f"│ {time:<{COL_TIME}} │"
    )


def _divider(left: str, mid: str, right: str, cross: str) -> str:
    return (
        left
        + cross * (COL_ASSET + 2)
        + mid
        + cross * (COL_PRICE + 2)
        + mid
        + cross * (COL_CURRENCY + 2)
        + mid
        + cross * (COL_SOURCE + 2)
        + mid
        + cross * (COL_TIME + 2)
        + right
    )


def render_table(results: list[Optional[AssetPrice]]) -> None:
    """Print a formatted price table to the terminal."""

    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    print(f"\n  Asset Prices — fetched at {now_ist}\n")

    print(_divider("┌", "┬", "┐", "─"))
    print(_row("Asset", "Price", "Currency", "Source","Time"))
    print(_divider("├", "┼", "┤", "─"))

    successful = 0
    for item in results:
        if item is None:
            print(_row("FETCH FAILED", "—", "—", "See logs above"))
        else:
            print(_row(
                item.name,
                item.price_display(),
                item.currency,
                item.source,
                item.time_display()
            ))
            successful += 1

    print(_divider("└", "┴", "┘", "─"))

    # Summary line
    total   = len(results)
    failed  = total - successful
    status  = "All assets fetched successfully." if failed == 0 \
              else f"⚠️   {failed}/{total} asset(s) failed — check logs above."
    print(f"\n  {status}\n")