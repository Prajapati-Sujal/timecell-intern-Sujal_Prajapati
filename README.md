# timecell-intern-<your-name>

## Task 01 — Portfolio Risk Calculator

### How to Run
```bash
cd task01
python main.py
```

### Approach
The core logic lives in `risk_calculator.py` with `compute_risk_metrics()` as a pure function
that accepts a `crash_scale` parameter — this made adding the moderate-crash bonus scenario
trivial (just call with `crash_scale=0.5`).

I modelled each asset as an `AssetRisk` dataclass with a `risk_score` property
(`allocation % × |crash %|`) — this cleanly identifies the `largest_risk_asset` without
any nested conditionals.

Edge cases handled:
- Allocations not summing to ~100% → raises `ValueError` with a clear message
- Zero monthly expenses → runway set to `infinity` (won't divide by zero)
- 100% cash portfolio → still computes correctly (all crashes = 0%)

### AI Usage
Used Claude to:
- Validate the math for `post_crash_value` against manual calculations
- Suggest the `crash_scale` parameter pattern to unify both scenarios
- Review variable naming for clarity

Used Gemini to : 
- Cross varify the requirements and edge cases

All logic was written and understood by me line-by-line.

### Bonus
- Moderate crash scenario (50% severity) computed and displayed side by side
- CLI bar chart using only Python built-ins (`█` / `░` characters)


## Task 02 — Live Market Data Fetch

### How to Run
```bash
pip install requests yfinance
cd task02
python main.py
```

### Assets & APIs
| Asset   | API                        | Key Required? |
|---------|----------------------------|---------------|
| BTC     | CoinGecko `/simple/price`  |      No       |
| NIFTY50 | Yahoo Finance via yfinance |      No       |
| GOLD    | Yahoo Finance (GC=F×INR=X) |      No       |

### Error Handling
- Each fetcher is isolated — one failure never crashes the others
- Specific exceptions caught: `ConnectionError`, `Timeout`, `HTTPError`, bad JSON
- Failed rows render as `FETCH FAILED` in the table with a pointer to logs
- NaN guard on yfinance prices (market closed edge case)

### Gold Price Logic
Gold futures (`GC=F`) quote in USD/troy oz. Converted to INR/10g:
`price = (usd_per_oz ÷ 31.1035) × 10 × usd_inr_rate`

### AI Usage
Used Claude to validate the gold unit conversion math and suggest
the `fast_info` attribute over the slower `history()` call in yfinance.



## Task 03 — AI-Powered Portfolio Explainer

### How to Run
```bash
pip install groq python-dotenv
```
```
Create a `.env` file in the project root:
GROQ_API_KEY=gsk_...
```
Get key: console.groq.com

```bash
cd task03
python main.py
```

---

### API Used
**Groq — Llama 3.3 70B Versatile** (completely free)

Chosen because:
- Free tier with good rate limits, no billing setup needed
- Llama 3.3 70B produces high-quality structured output comparable to GPT-4o for financial reasoning tasks
- Fast inference (~2–3s per call) suitable for a CLI tool

---

### Architecture — 3 Files, Clean Separation

| File                  | Responsibility                            |
| `prompt_builder.py`   | All prompt engineering — zero API logic   |
| `explainer.py`        | Groq API calls + robust XML parsing       |
| `main.py`             | Demo runner — 3 portfolios × 3 tones      |


---

### Prompt Engineering — Full Iteration Log

**v1 — Basic role priming + XML output format**

```python
prompt = f"""You are a financial advisor. Analyse this portfolio and respond with:
<summary>...</summary>
<verdict>...</verdict>"""
```

Problems :
- tones felt identical (just slight rephrasing)
- model invented
return/income claims ("FD covers ₹1.5L monthly expenses")
- Verdict had no reasoning
- too agreeable — approved everything

---

**v2 — Added STRICT RULES block to stop hallucinations**

Added Strict Rules:
1. NEVER assume investment returns or yield unless explicitly provided.
2. NEVER say "FD earns ₹X" — you do not have return data.
3. Runway can only be discussed in context of SELLING assets.
4. Every numerical claim must trace back to portfolio data above.

Fixed: hallucinated income claims disappeared entirely.

Problem : 
- tone differentiation, shallow verdict, agreeable critic.

---

**v3 — Explicit banned word lists per tone**

Instead of just describing the tone, added hard vocabulary rules:

- Added per-tone banned vocabulary (e.g. BEGINNER bans "volatility, drawdown, correlation"). 
- Forced analogies for beginners, quant terms required for expert. 


Fixed: tone differentiation completely.


**v4 — Added `<verdict_reason>` tag + deterministic verdict logic**

- Added `<verdict_reason>` tag — the model must now justify its verdict in one auditable sentence. This means one can trace exactly why the verdict was chosen.

Fixed: verdicts are now consistent, reasoned, and auditable.
---

**Critic prompt — special fix required**

v1 critic was too agreeable — it approved everything with minor caveats.

Fix: changed person from "reviewer" to "strict risk compliance officer" and added the explicit instruction:


fixed : it now finds specific errors rather than offering generic validation.

---

### Robust XML Parser — 3 Levels

The parser in `explainer.py` never raises an exception:

```
Level 1 — Standard: <tag>...</tag> matched normally
Level 2 — Fallback: tag opened but not closed → greedy match to next tag
Level 3 — Missing: tag not found at all → returns empty string, logs warning
```

Missing tags are tracked in `output.missing_tags` and printed as warnings.
`parse_success` is only `True` when all 5 tags are present and verdict is valid.

---

### Features

| Feature                                                   | Status |

| 3–4 sentence risk summary 
| Doing well (with concrete number)                         |   ✅  |
| Consider changing (with consequence)                      |   ✅  |
| Verdict (Aggressive / Balanced / Conservative)            |   ✅  |
| Verdict reason (auditable 1-sentence justification)       |   ✅  |
| Configurable tone: beginner / experienced / expert        |   ✅  |
| Critic LLM call (adversarial accuracy review)             |   ✅  |
| Raw API response printed separately                       |   ✅  |
| Robust fallback XML parser                                |   ✅  |
| Works with any portfolio dict                             |   ✅  |
| Pre-computed risk metrics passed to LLM                   |   ✅  |

---

### Integration with Task 01

`main.py` calls `compute_risk_metrics()` from Task 01 and passes the
results directly into the prompt:

The LLM receives pre-computed values (post-crash value, runway, ruin test)
and is explicitly told: *"do NOT recompute or contradict these."*
This prevents the LLM from doing its own math — it only interprets.

---

### Demo Portfolios

| Portfolio                         | Description               | Expected Verdict |
|                                   |                           |                  |
| Assessment (BTC/NIFTY/GOLD/CASH)  | From the task spec        | Aggressive       |
| Conservative (FD/GOLD/NIFTY/BTC)  | Low-risk family office    | Conservative     |
| High-Risk Crypto (BTC/ETH/CASH)   | 90% crypto                | Aggressive       |

Each runs across all 3 tones. Conservative portfolio also runs the
critic review to demonstrate the second LLM call.



## Task 04 — Portfolio Scorecard

### What I Built & Why
A letter-grade report card for any portfolio — scored across 5 risk
dimensions the way a CIO would assess a family office position.

Timecell's core value is making complex risk math legible to principals.
A scorecard does exactly that — it takes numbers and turns them into something a client can immediately understand and act on.

### How to Run
```bash
cd task04
python main.py
```

### 5 Dimensions Graded

| Dimension             | What it measures                                      |
|-----------------------|-------------------------------------------------------|
| Crash Survival        | % of portfolio retained after full crash              |
| Runway Coverage       | Months of expenses covered post-crash                 |
| Concentration Risk    | Single-asset overweight, adjusted for crash magnitude |
| Asset Diversity       | Number of uncorrelated asset classes present          |
| Overall Risk Load     | Allocation-weighted average crash exposure            |

Each dimension scores 0–100 and converts to a letter grade (A+ → F).
Overall grade = average across all 5 dimensions.

### Design Decisions
- Concentration score penalises heavy allocation in high-crash assets
  (40% in CASH is fine; 40% in BTC is not — both penalised differently)
- Asset classifier uses keyword matching so it works with any asset name
- Score bar rendered in CLI using block characters — no libraries needed