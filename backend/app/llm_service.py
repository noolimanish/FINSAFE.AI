"""
Provider-agnostic LLM explanation and 30-day action plan generator.
- Works with any OpenAI-compatible chat completions endpoint via LLM_API_KEY and LLM_BASE_URL.
- Never computes numbers: strictly consumes the rule engine output.
- Includes a deterministic fallback that returns the exact same JSON schema when no API key is configured.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple
import httpx

from app.rules_engine import format_compact_inr, format_inr

SYSTEM_PROMPT = """You are FinSafe's Financial Clarity Assistant for salaried professionals in India.
STRICT GUARDRAILS:
1. NEVER invent, recalculate, or alter any financial numbers, percentages, or rupee amounts. Use ONLY the exact numbers provided in the input JSON.
2. NEVER recommend specific stock tickers, mutual fund scheme names, or insurance company brands.
3. NEVER promise guaranteed returns or offer personalized SEBI-regulated investment advice.
4. Your sole job is to:
   (a) Rewrite each deterministic rule finding into a warm, empathetic, plain-English 2-3 sentence explanation (`plain_explanation`) that explains WHY this matters in everyday life.
   (b) Generate a prioritized 4-step 30-day action plan (`action_plan`, one action per week for Weeks 1 to 4) addressing the highest-severity findings first, citing the exact rupee gaps from the input.
5. Respond ONLY with valid JSON matching the exact schema:
{
  "explanations": [{"rule_id": "R1", "plain_explanation": "..."}],
  "action_plan": [{"priority_order": 1, "week_bucket": "Week 1", "rule_id": "R1", "title": "...", "description": "..."}]
}
"""


def build_deterministic_fallback(
    profile: Dict[str, Any], engine_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministic fallback producing the exact same JSON shape as the LLM.
    Uses the pre-computed metrics from `engine_output` to craft warm, specific Indian context guidance.
    """
    m = engine_output["metrics"]
    findings = engine_output["findings"]
    dependents = int(profile.get("dependents", 0))

    explanations_map: Dict[str, str] = {}

    # R1 explanation
    r1 = next(f for f in findings if f["rule_id"] == "R1")
    if r1["severity"] == "critical":
        explanations_map["R1"] = (
            f"If your salary paused tomorrow due to a layoff or medical emergency, your accessible cash of "
            f"{format_inr(m['liquid_assets'])} would last only {m['emergency_runway_months']:.1f} months against "
            f"your {format_inr(m['monthly_essential_burn'])} monthly bills and EMIs. Building an untouched buffer "
            f"toward {format_inr(m['monthly_essential_burn'] * 6)} ensures you never have to swipe a credit card "
            f"or break long-term compounding assets under stress."
        )
    elif r1["severity"] == "warning":
        explanations_map["R1"] = (
            f"You have crossed the basic 3-month survival floor with {m['emergency_runway_months']:.1f} months "
            f"({format_inr(m['liquid_assets'])}) in liquid reserves, which is a solid start. Adding another "
            f"{format_inr(m['emergency_shortfall_inr'])} in a sweep-in FD or liquid fund will bring you to a "
            f"comfortable 6-month cushion."
        )
    else:
        explanations_map["R1"] = (
            f"With {m['emergency_runway_months']:.1f} months ({format_inr(m['liquid_assets'])}) of mandatory "
            f"expenses readily accessible, your household can weather career transitions or unexpected expenses "
            f"with zero short-term borrowing stress."
        )

    # R2 explanation
    r2 = next(f for f in findings if f["rule_id"] == "R2")
    if m["personal_medical_cover"] <= 0:
        explanations_map["R2"] = (
            f"Relying solely on your employer's {format_inr(m['employer_medical_cover'])} group health policy is "
            f"one of the most common blind spots for Indian salaried employees—that cover ends the day you resign "
            f"or get laid off. Securing an independent base policy + super top-up toward "
            f"{format_compact_inr(m['recommended_medical_cover'])} protects your savings from Tier-1 private hospital inflation."
        )
    elif r2["severity"] == "warning":
        explanations_map["R2"] = (
            f"You wisely hold {format_inr(m['personal_medical_cover'])} in personal health insurance outside work, "
            f"so you won't be uninsured between jobs. However, a single ICU hospitalization in a metro city can "
            f"consume ₹10L–₹15L; bridging your {format_compact_inr(m['medical_shortfall_inr'])} gap via an affordable "
            f"super top-up policy keeps your investment portfolio ring-fenced."
        )
    else:
        explanations_map["R2"] = (
            f"Your personal medical cover of {format_inr(m['personal_medical_cover'])} (combined total "
            f"{format_inr(m['total_medical_cover'])}) comfortably meets the 3× income protection benchmark, ensuring "
            f"continuity even if you change employers."
        )

    # R3 explanation
    r3 = next(f for f in findings if f["rule_id"] == "R3")
    if r3["severity"] == "warning":
        explanations_map["R3"] = (
            f"Right now, {m['locked_endowment_share_pct']:.1f}% of your net worth ({format_inr(m['locked_endowment_value'])}) "
            f"is tied up in traditional LIC/endowment or ULIP policies that typically yield 4.5%–5.5% (below Indian "
            f"medical and lifestyle inflation) while penalizing early exits. Avoid adding new endowment policies and "
            f"evaluate converting low-yield plans to 'paid-up' status so future savings flow into transparent, liquid assets."
        )
    else:
        explanations_map["R3"] = (
            f"Only {m['locked_endowment_share_pct']:.1f}% of your investments ({format_inr(m['locked_endowment_value'])}) "
            f"sit in traditional locked insurance-cum-saving plans, keeping most of your capital flexible and compounding efficiently."
        )

    # R4 explanation
    r4 = next(f for f in findings if f["rule_id"] == "R4")
    if r4["severity"] in ("critical", "warning"):
        explanations_map["R4"] = (
            f"Health insurance pays the hospital, but it does not replace your monthly salary if an accident leaves "
            f"you temporarily or permanently unable to work. Adding a standalone Personal Accident policy of "
            f"{format_compact_inr(m['recommended_pa_cover'])} (which costs roughly ₹1,500–₹2,500/year) "
            + (
                f"and pure term life cover of {format_compact_inr(m['recommended_term_cover'])} for your {dependents} dependent(s) "
                if dependents > 0
                else ""
            )
            + "closes a major income-replacement blind spot."
        )
    else:
        explanations_map["R4"] = (
            f"Your pure term life ({format_compact_inr(m['term_life_cover'])}) and personal accident disability cover "
            f"({format_compact_inr(m['personal_accident_cover'])}) provide strong income replacement against unforeseen life events."
        )

    # R5 explanation
    r5 = next(f for f in findings if f["rule_id"] == "R5")
    if r5["severity"] in ("critical", "warning"):
        explanations_map["R5"] = (
            f"At 6% annual inflation, your current lifestyle will require a retirement corpus of roughly "
            f"{format_compact_inr(m['target_retirement_corpus'])} by age {profile.get('retirement_age', 60)}, whereas your "
            f"current trajectory projects to {format_compact_inr(m['projected_retirement_corpus'])} ({m['retirement_funded_pct']:.1f}% funded). "
            f"Stepping up your monthly retirement contribution by 10% each year as your salary grows is the simplest way to close the "
            f"{format_compact_inr(m['retirement_gap_inr'])} gap without feeling pinched today."
        )
    else:
        explanations_map["R5"] = (
            f"Your current retirement base and monthly contributions project to {format_compact_inr(m['projected_retirement_corpus'])}, "
            f"putting you on track ({m['retirement_funded_pct']:.1f}% funded) against your inflation-adjusted target of "
            f"{format_compact_inr(m['target_retirement_corpus'])}."
        )

    # Build prioritized 30-day action plan sorted by severity (critical -> warning -> info)
    severity_rank = {"critical": 0, "warning": 1, "info": 2}
    sorted_findings = sorted(findings, key=lambda x: severity_rank.get(x["severity"], 3))

    candidate_actions = []
    for f in sorted_findings:
        rid = f["rule_id"]
        if rid == "R2":
            candidate_actions.append(
                {
                    "rule_id": "R2",
                    "title": (
                        "Buy a standalone retail health policy outside your employer"
                        if m["personal_medical_cover"] <= 0
                        else f"Add a super top-up health cover to reach {format_compact_inr(m['recommended_medical_cover'])}"
                    ),
                    "description": (
                        f"Get quotes for a ₹10L–₹15L personal base health policy (plus a super top-up toward "
                        f"{format_compact_inr(m['recommended_medical_cover'])}) with zero room-rent capping so a job change never leaves you uncovered."
                    ),
                }
            )
        elif rid == "R1":
            candidate_actions.append(
                {
                    "rule_id": "R1",
                    "title": f"Automate an emergency reserve transfer for your {format_compact_inr(m['emergency_shortfall_inr'])} buffer gap",
                    "description": (
                        f"Open a dedicated high-liquidity savings account or overnight/liquid fund and automate a monthly transfer "
                        f"on payday until your {format_inr(m['liquid_assets'])} reserve reaches 6 months of mandatory burn "
                        f"({format_inr(m['monthly_essential_burn'] * 6)})."
                    ),
                }
            )
        elif rid == "R4":
            candidate_actions.append(
                {
                    "rule_id": "R4",
                    "title": (
                        f"Secure {format_compact_inr(m['recommended_term_cover'])} pure term cover & {format_compact_inr(m['recommended_pa_cover'])} accident cover"
                        if dependents > 0 and m["term_life_cover"] < m["recommended_term_cover"]
                        else f"Add a standalone {format_compact_inr(m['recommended_pa_cover'])} Personal Accident disability policy"
                    ),
                    "description": (
                        f"Purchase a pure term life policy without return-of-premium riders (if supporting dependents) and a standalone "
                        f"Personal Accident policy covering permanent total and partial disability equal to 3× annual income ({format_compact_inr(m['recommended_pa_cover'])})."
                    ),
                }
            )
        elif rid == "R3":
            candidate_actions.append(
                {
                    "rule_id": "R3",
                    "title": "Audit locked LIC/endowment policies and halt new low-yield lock-ins",
                    "description": (
                        f"List all {format_inr(m['locked_endowment_value'])} in traditional endowment/ULIP plans ({m['locked_endowment_share_pct']:.1f}% of net worth). "
                        f"Calculate their XIRR; if a policy has completed 3+ years with <5.5% return, request a 'paid-up' conversion quote instead of paying fresh premiums."
                    ),
                }
            )
        elif rid == "R5":
            candidate_actions.append(
                {
                    "rule_id": "R5",
                    "title": f"Set up an annual 10% step-up on your retirement contributions",
                    "description": (
                        f"To bridge your {format_compact_inr(m['retirement_gap_inr'])} projected retirement gap by age {profile.get('retirement_age', 60)}, "
                        f"enable an automated 10% annual step-up on your long-term diversified index/flexi-cap SIPs and VPF/NPS contributions."
                    ),
                }
            )

    action_plan = []
    for idx, act in enumerate(candidate_actions[:4], start=1):
        action_plan.append(
            {
                "priority_order": idx,
                "week_bucket": f"Week {idx}",
                "rule_id": act["rule_id"],
                "title": act["title"],
                "description": act["description"],
            }
        )

    return {
        "explanations": [
            {"rule_id": f["rule_id"], "plain_explanation": explanations_map[f["rule_id"]]}
            for f in findings
        ],
        "action_plan": action_plan,
    }


async def generate_explanations_and_plan(
    profile: Dict[str, Any], engine_output: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool]:
    """
    Calls the configured OpenAI-compatible LLM if `LLM_API_KEY` is set;
    otherwise (or on network/schema error) falls back deterministically.
    Returns (enriched_findings, action_plan, llm_used).
    """
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    fallback_payload = build_deterministic_fallback(profile, engine_output)
    llm_payload = None
    llm_used = False

    if api_key:
        user_prompt = (
            f"User Profile Context: Age {profile.get('age')}, "
            f"Annual Income {format_inr(profile.get('annual_income', 0))}, "
            f"Dependents: {profile.get('dependents', 0)}, "
            f"Security Score: {engine_output['security_score']}/100.\n"
            f"Deterministic Rule Findings JSON:\n"
            f"{json.dumps(engine_output['findings'], indent=2)}"
        )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if "explanations" in parsed and "action_plan" in parsed:
                    llm_payload = parsed
                    llm_used = True
        except Exception:
            llm_payload = None
            llm_used = False

    active_payload = llm_payload or fallback_payload
    exp_by_rule = {
        item["rule_id"]: item["plain_explanation"]
        for item in active_payload.get("explanations", [])
    }

    enriched_findings = []
    for f in engine_output["findings"]:
        rid = f["rule_id"]
        enriched_findings.append(
            {
                "rule_id": rid,
                "title": f["title"],
                "severity": f["severity"],
                "deterministic_message": f["deterministic_message"],
                "plain_explanation": exp_by_rule.get(
                    rid,
                    next(
                        x["plain_explanation"]
                        for x in fallback_payload["explanations"]
                        if x["rule_id"] == rid
                    ),
                ),
                "current_value_label": f["current_value_label"],
                "target_value_label": f["target_value_label"],
                "gap_inr": f["gap_inr"],
            }
        )

    action_plan = active_payload.get("action_plan") or fallback_payload["action_plan"]
    return enriched_findings, action_plan, llm_used
