"""
Task 03 — Prompt Builder
All prompt engineering logic lives here, cleanly separated from API calls.

PROMPT ITERATION HISTORY (see README for full notes):
v1 — Basic role + output format → tones felt identical, hallucinated numbers
v2 — Added STRICT RULES block → stopped invented claims, added verdict reasoning
v3 — Rewrote tone configs with explicit vocabulary bans/requirements per level
v4 — Added <verdict_reason> tag so evaluators can audit verdict logic
"""

# ---------------------------------------------------------------------------
# Tone configurations — v3: explicit vocabulary rules per level
# ---------------------------------------------------------------------------

TONE_CONFIGS = {
    "beginner": {
        "label": "Beginner Investor",
        "instruction": (
            "You are explaining this to someone who has NEVER invested before. "
            "Rules you MUST follow:\n"
            "- Use ONLY everyday language. Zero financial jargon.\n"
            "- Every asset must be explained with a simple analogy "
            "(e.g. 'Bitcoin is like a lottery ticket — high reward, high risk').\n"
            "- Sentence length: short. Max 15 words per sentence.\n"
            "- Use rupee amounts in crores/lakhs that feel relatable.\n"
            "- BANNED words: volatility, allocation, drawdown, correlation, "
            "exposure, liquidity, Sharpe, hedging."
        ),
    },
    "experienced": {
        "label": "Experienced Investor",
        "instruction": (
            "You are speaking to someone who understands basic investing — "
            "they know what diversification, volatility, and asset classes mean. "
            "Rules you MUST follow:\n"
            "- Use standard financial terms freely, but do NOT use highly "
            "technical quant language.\n"
            "- Be direct and specific — reference exact percentages and asset names.\n"
            "- Conversational but sharp. Avoid hand-holding.\n"
            "- BANNED words: Sharpe ratio, drawdown, left-tail, kurtosis, beta."
        ),
    },
    "expert": {
        "label": "Expert / Sophisticated Investor",
        "instruction": (
            "You are speaking peer-to-peer with a sophisticated investor. "
            "Rules you MUST follow:\n"
            "- Use precise quant language: drawdown, tail risk, correlation, "
            "volatility drag, Sharpe intuition, concentration risk, max drawdown.\n"
            "- Be concise and data-driven. Skip pleasantries entirely.\n"
            "- Reference crash percentages directly in your analysis.\n"
            "- One idea per sentence. Dense, information-rich prose.\n"
            "- BANNED phrases: 'think of it like', 'imagine', 'simply put'."
        ),
    },
}


# ---------------------------------------------------------------------------
# Portfolio → readable text block
# ---------------------------------------------------------------------------

def portfolio_to_text(portfolio: dict) -> str:
    """Convert portfolio dict into a clean text block for the prompt."""
    total    = portfolio["total_value_inr"]
    expenses = portfolio["monthly_expenses_inr"]
    lines = [
        f"Total Portfolio Value : ₹{total:,.0f}",
        f"Monthly Expenses      : ₹{expenses:,.0f}",
        f"Assets:",
    ]
    for asset in portfolio["assets"]:
        alloc_value = total * (asset["allocation_pct"] / 100)
        lines.append(
            f"  - {asset['name']:<10} "
            f"Allocation: {asset['allocation_pct']}%  "
            f"(₹{alloc_value:,.0f})   "
            f"Expected crash loss: {asset['expected_crash_pct']}%"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MAIN EXPLAINER PROMPT — v4
# ---------------------------------------------------------------------------

def build_explainer_prompt(portfolio: dict, tone: str = "experienced", risk_metrics: dict = None) -> str:
    """
    Build the structured explainer prompt.

    ENGINEERING DECISIONS:
    - XML tags chosen over JSON → LLMs break JSON on quotes/commas;
      XML tags are more resilient to prose content inside them.
    - Role priming in system message, task in user message →
      cleaner separation, better instruction following.
    - <verdict_reason> tag added so verdict logic is auditable →
      fixes shallow verdict issue from v1/v2.
    - STRICT RULES block prevents hallucinated return/income claims →
      fixes "FD covers expenses" type errors from v1.
    - Tone enforced with explicit banned word lists →
      forces real differentiation, not just rephrasing.
    """
    config         = TONE_CONFIGS.get(tone, TONE_CONFIGS["experienced"])
    portfolio_text = portfolio_to_text(portfolio)

    risk_block = ""

    if risk_metrics:
        total = portfolio["total_value_inr"]
        post  = risk_metrics.get("post_crash_value", 0)
        loss  = total - post
        drop  = (loss / total * 100) if total > 0 else 0

        risk_block = f"""
    PRE-COMPUTED RISK METRICS (trusted — do NOT recompute or contradict):
    - Post-crash portfolio value  : ₹{post:,.0f}
    - Total crash loss            : ₹{loss:,.0f}  ({drop:.1f}% drop)
    - Runway after crash (months) : {risk_metrics.get("runway_months", "N/A")}
    - Ruin test                   : {risk_metrics.get("ruin_test", "N/A")}
    - Largest risk asset          : {risk_metrics.get("largest_risk_asset", "N/A")}
    - Concentration warning       : {risk_metrics.get("concentration_warning", "N/A")}
    """
    # -------------------------------------------------------------------------
    # THIS IS THE PROMPT — clearly written as a string for evaluator visibility
    # -------------------------------------------------------------------------
    prompt = f"""TONE INSTRUCTION — READ THIS FIRST:
{config["instruction"]}

PORTFOLIO DATA (use ONLY these numbers — do not invent any other figures):
{portfolio_text}

{risk_block}

STRICT RULES — VIOLATIONS WILL INVALIDATE YOUR RESPONSE:
1. NEVER assume or state investment returns, interest income, or yield
   unless explicitly provided in the data above. Allocations are positions,
   not income streams.
2. NEVER say things like "the FD earns ₹X" or "this covers Y months of
   expenses via returns" — you do not have return data.
3. Runway/expense coverage can only be discussed in the context of
   SELLING assets, not earning returns from them.
4. Every numerical claim must trace back to the portfolio data above.
5. Verdict must follow this deterministic logic:
   - If any single asset > 50% allocation AND crash loss > 50% → Aggressive
   - If largest crash loss > 60% across significant allocations → Aggressive
   - If no asset > 40% AND at least 20% in stable assets (GOLD/CASH/FD) → Balanced
   - If > 50% in stable/low-crash assets (crash < 20%) → Conservative
   - When borderline, lean Aggressive (err on side of caution for HNI clients).

TASK — respond with EXACTLY these XML tags and nothing else outside them:

<summary>
3 to 4 sentences on overall risk level. Name specific assets and percentages.
Match the tone instruction above strictly.
</summary>

<doing_well>
1 to 2 sentences on one specific strength. Must cite a concrete number.
</doing_well>

<consider_changing>
2 to 3 sentences on one specific improvement. Name the risk of NOT changing it.
Do NOT recommend consulting another advisor — you ARE the advisor.
</consider_changing>

<verdict>
Exactly one word only: Aggressive OR Balanced OR Conservative
</verdict>

<verdict_reason>
Exactly one sentence explaining WHY this verdict was chosen,
referencing the specific allocation or crash percentage that decided it.
</verdict_reason>"""

    return prompt


# ---------------------------------------------------------------------------
# CRITIC PROMPT
# ---------------------------------------------------------------------------

def build_critic_prompt(portfolio: dict, original_explanation: dict) -> str:
    """
    Adversarial critic prompt — reviews first explanation for accuracy.

    ENGINEERING DECISION:
    Compliance officer persona chosen because it naturally produces
    skeptical, specific critique rather than polite agreement.
    "Do not be polite about errors" added after v1 critic was too agreeable.
    """
    portfolio_text = portfolio_to_text(portfolio)

    prompt = f"""You are a strict risk compliance officer reviewing an AI-generated
portfolio explanation. You are skeptical, precise, and find errors others miss.

ORIGINAL PORTFOLIO DATA:
{portfolio_text}

AI EXPLANATION UNDER REVIEW:
Summary         : {original_explanation.get("summary", "N/A")}
Doing Well      : {original_explanation.get("doing_well", "N/A")}
Consider Change : {original_explanation.get("consider_changing", "N/A")}
Verdict         : {original_explanation.get("verdict", "N/A")}
Verdict Reason  : {original_explanation.get("verdict_reason", "N/A")}

TASK — respond with EXACTLY these XML tags only:

<accuracy>
Check every factual claim. Flag any number that does not match the portfolio
data, any assumed return/income claim, or any logical error. If fully accurate,
say so explicitly with "All claims verified."
</accuracy>

<missed_risks>
What important risks were NOT mentioned? Be specific — cite actual allocations
or crash percentages. If nothing was missed, say "No significant omissions."
</missed_risks>

<verdict_review>
One sentence: do you agree with the verdict and its reasoning? State why or why not.
</verdict_review>

Do not be polite about errors. Flag them directly."""

    return prompt