"""
Task 03 — Explainer
Groq API calls (Llama 3.3 70B Versatile) + robust response parsing.
Free API — get key at console.groq.com
"""

import re
import logging
from dataclasses import dataclass, field

from groq import Groq, AuthenticationError, RateLimitError, APIError
from task3.prompt_builder import build_explainer_prompt, build_critic_prompt
from dotenv import load_dotenv
load_dotenv()

log = logging.getLogger(__name__)

MODEL      = "llama-3.3-70b-versatile"
MAX_TOKENS = 1024


# ---------------------------------------------------------------------------
# Response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExplainerOutput:
    summary:           str  = ""
    doing_well:        str  = ""
    consider_changing: str  = ""
    verdict:           str  = ""
    verdict_reason:    str  = ""
    raw_response:      str  = ""
    parse_success:     bool = False
    missing_tags:      list = field(default_factory=list)


@dataclass
class CriticOutput:
    accuracy:       str  = ""
    missed_risks:   str  = ""
    verdict_review: str  = ""
    raw_response:   str  = ""
    parse_success:  bool = False
    missing_tags:   list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Robust XML parser 
# ---------------------------------------------------------------------------

def _extract_tag(text: str, tag: str) -> str:
    """
    Extract content between <tag>...</tag>.
    Handles: extra whitespace, newlines, partial closes, nested content.
    Returns empty string (never raises) if tag not found.
    """
    # Primary: standard XML match
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match   = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback 1: tag opened but not closed — grab until next opening tag
    pattern_open = rf"<{tag}>(.*?)(?=<[a-z]|$)"
    match = re.search(pattern_open, text, re.DOTALL | re.IGNORECASE)
    if match:
        log.warning(f"Tag <{tag}> was not closed properly — used fallback parser.")
        return match.group(1).strip()

    # Fallback 2: tag missing entirely
    return ""


def _validate_verdict(verdict: str) -> str:
    """Normalise verdict to one of three allowed words."""
    allowed = {"Aggressive", "Balanced", "Conservative"}
    for word in allowed:
        if word.lower() in verdict.lower():
            return word
    log.warning(f"Verdict '{verdict}' not in allowed set — returning raw value.")
    return verdict


def _check_missing(output_dict: dict, required_tags: list) -> list:
    """Return list of tag names that are empty."""
    return [tag for tag in required_tags if not output_dict.get(tag, "")]


# ---------------------------------------------------------------------------
# Core API call
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    """
    Call Groq (Llama 3.3 70B Versatile).
    Model: llama-3.3-70b-versatile  |  Provider: Groq  |  Cost: Free
    Temperature 0.4 — controlled creativity, consistent structure.
    """
    client = Groq()   # reads GROQ_API_KEY from env

    response = client.chat.completions.create(
        model      = MODEL,
        max_tokens = MAX_TOKENS,
        temperature= 0.4,
        messages   = [
            {
                "role": "system",
                "content": (
                    "You are a senior wealth advisor at Timecell.ai, an AI-powered "
                    "wealth management platform for high-net-worth Indian families. "
                    "Always respond using ONLY the XML tags requested in the prompt. "
                    "Never add commentary, greetings, or text outside those tags."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Explainer
# ---------------------------------------------------------------------------

def explain_portfolio(portfolio: dict, tone: str = "experienced", risk_metrics: dict = None) -> ExplainerOutput:
    """
    Generate a plain-English portfolio risk explanation using Llama 3.3 70B.
    Returns a fully parsed ExplainerOutput with robust fallback handling.
    """
    prompt = build_explainer_prompt(portfolio, tone, risk_metrics)
    log.info(f"Calling Groq [{MODEL}] — tone: {tone}")

    try:
        raw = call_llm(prompt)
    except AuthenticationError:
        log.error("GROQ_API_KEY is missing or invalid. Get one free at console.groq.com")
        raise
    except RateLimitError:
        log.error("Rate limit hit — wait a moment and retry.")
        raise
    except APIError as e:
        log.error(f"Groq API error: {e}")
        raise

    verdict_raw = _extract_tag(raw, "verdict")

    output = ExplainerOutput(
        raw_response      = raw,
        summary           = _extract_tag(raw, "summary"),
        doing_well        = _extract_tag(raw, "doing_well"),
        consider_changing = _extract_tag(raw, "consider_changing"),
        verdict           = _validate_verdict(verdict_raw),
        verdict_reason    = _extract_tag(raw, "verdict_reason"),
    )

    required = ["summary", "doing_well", "consider_changing", "verdict", "verdict_reason"]
    output.missing_tags  = _check_missing(output.__dict__, required)
    output.parse_success = (
        len(output.missing_tags) == 0
        and output.verdict in {"Aggressive", "Balanced", "Conservative"}
    )

    if output.missing_tags:
        log.warning(f"Missing tags: {output.missing_tags} — check raw response.")

    return output


# ---------------------------------------------------------------------------
# Critic (bonus second LLM call)
# ---------------------------------------------------------------------------

def critique_explanation(portfolio: dict, explanation: ExplainerOutput) -> CriticOutput:
    """
    Second Llama call — adversarial review of the first explanation.
    """
    explanation_dict = {
        "summary":           explanation.summary,
        "doing_well":        explanation.doing_well,
        "consider_changing": explanation.consider_changing,
        "verdict":           explanation.verdict,
        "verdict_reason":    explanation.verdict_reason,
    }
    prompt = build_critic_prompt(portfolio, explanation_dict)
    log.info(f"Calling Groq [{MODEL}] — critic review")

    try:
        raw = call_llm(prompt)
    except Exception as e:
        log.error(f"Critic call failed: {e}")
        return CriticOutput(raw_response=str(e), parse_success=False)

    output = CriticOutput(
        raw_response   = raw,
        accuracy       = _extract_tag(raw, "accuracy"),
        missed_risks   = _extract_tag(raw, "missed_risks"),
        verdict_review = _extract_tag(raw, "verdict_review"),
    )

    required             = ["accuracy", "missed_risks", "verdict_review"]
    output.missing_tags  = _check_missing(output.__dict__, required)
    output.parse_success = len(output.missing_tags) == 0

    return output