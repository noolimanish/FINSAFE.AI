"""
Pure, deterministic rule engine for FinSafe.
Evaluates the 5 India-specific financial security rules (R1 to R5) with zero LLM involvement.
All monetary calculations, ratios, and severities are computed here.
"""

from __future__ import annotations

from typing import Any, Dict, List


def format_inr(amount: float) -> str:
    """Formats a number using the Indian numbering system (Lakhs / Crores) with ₹ symbol."""
    amount = round(float(amount))
    if amount < 0:
        return "-" + format_inr(-amount)
    s = str(amount)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while len(rest) > 2:
        parts.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.append(rest)
    parts.reverse()
    return f"₹{','.join(parts)},{last3}"


def format_compact_inr(amount: float) -> str:
    """Formats large rupee values into compact Lakh (L) or Crore (Cr) strings."""
    val = float(amount)
    if val >= 1_00_00_000:
        return f"₹{val / 1_00_00_000:.2f} Cr"
    if val >= 1_00_000:
        return f"₹{val / 1_00_000:.1f} L"
    return format_inr(val)


def evaluate_r1_emergency_fund(
    liquid_assets: float, monthly_essential_burn: float
) -> Dict[str, Any]:
    """
    Rule R1: Emergency Fund Runway.
    - < 3 months of mandatory expenses = critical
    - 3 to < 6 months = warning
    - >= 6 months = info
    """
    burn = max(1.0, float(monthly_essential_burn))
    runway_months = liquid_assets / burn
    target_6m = burn * 6.0
    target_3m = burn * 3.0
    shortfall = max(0.0, target_6m - liquid_assets)

    if runway_months < 3.0:
        severity = "critical"
    elif runway_months < 6.0:
        severity = "warning"
    else:
        severity = "info"

    msg = (
        f"Your liquid emergency reserve of {format_inr(liquid_assets)} covers "
        f"{runway_months:.1f} months of mandatory expenses ({format_inr(burn)}/month), "
        f"against a recommended 6-month buffer of {format_inr(target_6m)} "
        f"(minimum survival floor: {format_inr(target_3m)})."
    )

    return {
        "rule_id": "R1",
        "title": "Emergency Fund Runway",
        "severity": severity,
        "deterministic_message": msg,
        "current_value_label": f"{runway_months:.1f} mos ({format_compact_inr(liquid_assets)})",
        "target_value_label": f"6.0 mos ({format_compact_inr(target_6m)})",
        "gap_inr": round(shortfall, 2),
        "runway_months": round(runway_months, 2),
        "target_6m_inr": round(target_6m, 2),
    }


def evaluate_r2_medical_insurance(
    employer_medical: float, personal_medical: float, annual_income: float
) -> Dict[str, Any]:
    """
    Rule R2: Medical Insurance Adequacy & Employer Dependency.
    - Relying solely on employer cover (personal_medical == 0) = critical
    - Total medical cover < 3x annual income (or personal < ₹10L) = warning
    - Personal cover >= ₹10L and total cover >= 3x annual income = info
    """
    total_medical = employer_medical + personal_medical
    recommended_cover = max(10_00_000.0, 3.0 * annual_income)
    shortfall = max(0.0, recommended_cover - personal_medical)

    if personal_medical <= 0:
        severity = "critical"
        msg = (
            f"You have ₹0 in standalone personal medical insurance and rely 100% on "
            f"employer group cover ({format_inr(employer_medical)}). Employer coverage "
            f"vanishes the day you switch jobs or face a layoff, and your total cover is "
            f"below the 3× annual income benchmark of {format_inr(recommended_cover)}."
        )
    elif total_medical < 3.0 * annual_income or personal_medical < 10_00_000.0:
        severity = "warning"
        msg = (
            f"Your total medical cover of {format_inr(total_medical)} "
            f"(Personal: {format_inr(personal_medical)}, Employer: {format_inr(employer_medical)}) "
            f"is below the recommended 3× annual income protection target of "
            f"{format_inr(recommended_cover)}."
        )
    else:
        severity = "info"
        msg = (
            f"Your medical coverage of {format_inr(total_medical)} "
            f"(including {format_inr(personal_medical)} in portable personal cover) "
            f"meets the 3× annual income benchmark ({format_inr(recommended_cover)})."
        )

    return {
        "rule_id": "R2",
        "title": "Medical Insurance & Job-Switch Continuity",
        "severity": severity,
        "deterministic_message": msg,
        "current_value_label": f"Personal: {format_compact_inr(personal_medical)} (Total: {format_compact_inr(total_medical)})",
        "target_value_label": format_compact_inr(recommended_cover),
        "gap_inr": round(shortfall, 2),
        "recommended_cover": round(recommended_cover, 2),
    }


def evaluate_r3_endowment_lock_in(
    lic_endowment_value: float, total_investments: float
) -> Dict[str, Any]:
    """
    Rule R3: Share of Net Worth Locked in LIC / Endowment / ULIP Products.
    - > 40% locked in low-yield endowment/ULIP plans = warning
    - <= 40% = info
    """
    if total_investments <= 0:
        locked_share_pct = 0.0
    else:
        locked_share_pct = (lic_endowment_value / total_investments) * 100.0

    threshold_inr = 0.40 * total_investments
    excess_locked = max(0.0, lic_endowment_value - threshold_inr)

    if locked_share_pct > 40.0:
        severity = "warning"
        msg = (
            f"{locked_share_pct:.1f}% of your investment portfolio ({format_inr(lic_endowment_value)} "
            f"out of {format_inr(total_investments)}) is locked in illiquid LIC/endowment/ULIP "
            f"policies, exceeding the 40% maximum concentration guideline by {format_inr(excess_locked)}."
        )
    else:
        severity = "info"
        msg = (
            f"{locked_share_pct:.1f}% of your portfolio ({format_inr(lic_endowment_value)} "
            f"out of {format_inr(total_investments)}) is held in LIC/endowment policies, "
            f"within the 40% concentration limit."
        )

    return {
        "rule_id": "R3",
        "title": "Illiquid LIC / Endowment Concentration",
        "severity": severity,
        "deterministic_message": msg,
        "current_value_label": f"{locked_share_pct:.1f}% ({format_compact_inr(lic_endowment_value)})",
        "target_value_label": "≤ 40.0% of portfolio",
        "gap_inr": round(excess_locked, 2),
        "locked_share_pct": round(locked_share_pct, 2),
    }


def evaluate_r4_accident_and_term_cover(
    personal_accident_cover: float,
    term_life_cover: float,
    annual_income: float,
    dependents: int,
) -> Dict[str, Any]:
    """
    Rule R4: Personal Accident & Term Life Protection.
    - Dependents > 0 with zero term life cover = critical
    - No personal accident cover (personal_accident_cover == 0) or term shortfall = warning
    - Adequate accident and term cover = info
    """
    recommended_pa = 3.0 * annual_income
    recommended_term = (10.0 * annual_income) if dependents > 0 else 0.0
    pa_gap = max(0.0, recommended_pa - personal_accident_cover)
    term_gap = max(0.0, recommended_term - term_life_cover)
    total_gap = pa_gap + term_gap

    if dependents > 0 and term_life_cover <= 0:
        severity = "critical"
        msg = (
            f"You support {dependents} dependent(s) but hold ₹0 in pure term life insurance "
            f"(recommended 10× income: {format_inr(recommended_term)}) and "
            f"{format_inr(personal_accident_cover)} in personal accident disability cover "
            f"(recommended: {format_inr(recommended_pa)})."
        )
    elif personal_accident_cover <= 0 or (dependents > 0 and term_life_cover < recommended_term):
        severity = "warning"
        msg = (
            f"Personal accident disability cover is {format_inr(personal_accident_cover)} "
            f"(recommended 3× income: {format_inr(recommended_pa)}) and pure term life cover "
            f"is {format_inr(term_life_cover)} for {dependents} dependent(s) "
            f"(recommended: {format_inr(recommended_term)})."
        )
    else:
        severity = "info"
        msg = (
            f"Income protection is well structured with {format_inr(personal_accident_cover)} "
            f"in personal accident cover and {format_inr(term_life_cover)} in pure term life cover."
        )

    return {
        "rule_id": "R4",
        "title": "Personal Accident & Term Life Protection",
        "severity": severity,
        "deterministic_message": msg,
        "current_value_label": f"PA: {format_compact_inr(personal_accident_cover)} | Term: {format_compact_inr(term_life_cover)}",
        "target_value_label": f"PA: {format_compact_inr(recommended_pa)} | Term: {format_compact_inr(recommended_term)}",
        "gap_inr": round(total_gap, 2),
        "recommended_pa": round(recommended_pa, 2),
        "recommended_term": round(recommended_term, 2),
    }


def evaluate_r5_retirement_readiness(
    age: int,
    retirement_age: int,
    current_retirement_corpus: float,
    monthly_retirement_contribution: float,
    monthly_lifestyle_expense: float,
) -> Dict[str, Any]:
    """
    Rule R5: Retirement Corpus Projection vs Inflation-Adjusted Target.
    Assumptions:
    - India CPI lifestyle inflation: 6.0% p.a.
    - Blended pre-retirement portfolio return: 10.0% p.a.
    - Required corpus at retirement: 25x inflation-adjusted annual expenses (4% rule)
    - Projected < 60% of target = critical
    - Projected 60% to < 100% of target = warning
    - Projected >= 100% of target = info
    """
    years_to_retire = max(1, retirement_age - age)
    inflation = 0.06
    annual_return = 0.10
    monthly_return = annual_return / 12.0
    months = years_to_retire * 12

    future_annual_expense = (monthly_lifestyle_expense * 12.0) * ((1.0 + inflation) ** years_to_retire)
    target_corpus = 25.0 * future_annual_expense

    fv_existing = current_retirement_corpus * ((1.0 + annual_return) ** years_to_retire)
    if monthly_retirement_contribution > 0:
        fv_sip = (
            monthly_retirement_contribution
            * (((1.0 + monthly_return) ** months - 1.0) / monthly_return)
            * (1.0 + monthly_return)
        )
    else:
        fv_sip = 0.0

    projected_corpus = fv_existing + fv_sip
    funded_pct = (projected_corpus / target_corpus * 100.0) if target_corpus > 0 else 100.0
    gap_inr = max(0.0, target_corpus - projected_corpus)

    if funded_pct < 60.0:
        severity = "critical"
    elif funded_pct < 100.0:
        severity = "warning"
    else:
        severity = "info"

    msg = (
        f"At age {retirement_age} ({years_to_retire} yrs away), your projected retirement corpus "
        f"is {format_compact_inr(projected_corpus)} against an inflation-adjusted target of "
        f"{format_compact_inr(target_corpus)} ({funded_pct:.1f}% funded; shortfall: {format_compact_inr(gap_inr)})."
    )

    return {
        "rule_id": "R5",
        "title": "Retirement Corpus Trajectory",
        "severity": severity,
        "deterministic_message": msg,
        "current_value_label": f"{format_compact_inr(projected_corpus)} ({funded_pct:.0f}%)",
        "target_value_label": format_compact_inr(target_corpus),
        "gap_inr": round(gap_inr, 2),
        "projected_corpus": round(projected_corpus, 2),
        "target_corpus": round(target_corpus, 2),
        "funded_pct": round(funded_pct, 1),
    }


def run_financial_health_check(
    profile: Dict[str, Any],
    policies: List[Dict[str, Any]],
    investments: List[Dict[str, Any]],
    expenses: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Orchestrates all 5 rules, computes the 0-100 Financial Security Score,
    and prepares chart metrics for the frontend dashboard.
    """
    annual_income = float(profile.get("annual_income", 12_00_000.0))
    age = int(profile.get("age", 28))
    retirement_age = int(profile.get("retirement_age", 60))
    dependents = int(profile.get("dependents", 0))
    monthly_retire_contrib = float(profile.get("monthly_retirement_contribution", 0.0))

    # Aggregate insurance
    employer_med = sum(
        float(p["sum_assured"]) for p in policies if p["policy_type"] == "medical_employer"
    )
    personal_med = sum(
        float(p["sum_assured"]) for p in policies if p["policy_type"] == "medical_personal"
    )
    term_life = sum(
        float(p["sum_assured"]) for p in policies if p["policy_type"] == "term_life"
    )
    personal_accident = sum(
        float(p["sum_assured"]) for p in policies if p["policy_type"] == "personal_accident"
    )

    # Aggregate investments
    liquid_assets = sum(
        float(i["current_value"]) for i in investments if i["category"] == "liquid"
    )
    equity_mf = sum(
        float(i["current_value"]) for i in investments if i["category"] == "equity_mf"
    )
    retire_epf_ppf = sum(
        float(i["current_value"]) for i in investments if i["category"] == "retirement_epf_ppf_nps"
    )
    lic_endowment = sum(
        float(i["current_value"]) for i in investments if i["category"] == "lic_endowment_ulip"
    )
    total_investments = liquid_assets + equity_mf + retire_epf_ppf + lic_endowment

    # Aggregate monthly expenses
    essential_exp = sum(
        float(e["monthly_amount"]) for e in expenses if e["category"] == "essential"
    )
    emi_exp = sum(
        float(e["monthly_amount"]) for e in expenses if e["category"] == "emi_debt"
    )
    discretionary_exp = sum(
        float(e["monthly_amount"]) for e in expenses if e["category"] == "discretionary"
    )

    monthly_essential_burn = essential_exp + emi_exp
    if monthly_essential_burn <= 0:
        monthly_essential_burn = (annual_income / 12.0) * 0.50

    monthly_lifestyle_expense = essential_exp + discretionary_exp
    if monthly_lifestyle_expense <= 0:
        monthly_lifestyle_expense = monthly_essential_burn * 0.85

    current_retirement_corpus = retire_epf_ppf + equity_mf + (0.50 * lic_endowment)

    r1 = evaluate_r1_emergency_fund(liquid_assets, monthly_essential_burn)
    r2 = evaluate_r2_medical_insurance(employer_med, personal_med, annual_income)
    r3 = evaluate_r3_endowment_lock_in(lic_endowment, total_investments)
    r4 = evaluate_r4_accident_and_term_cover(
        personal_accident, term_life, annual_income, dependents
    )
    r5 = evaluate_r5_retirement_readiness(
        age,
        retirement_age,
        current_retirement_corpus,
        monthly_retire_contrib,
        monthly_lifestyle_expense,
    )

    raw_findings = [r1, r2, r3, r4, r5]

    # Compute 0-100 score: start at 100, deduct 22 per critical, 12 per warning
    deductions = 0
    for f in raw_findings:
        if f["severity"] == "critical":
            deductions += 22
        elif f["severity"] == "warning":
            deductions += 12

    security_score = max(8, 100 - deductions)
    if security_score >= 75:
        score_band = "Resilient"
    elif security_score >= 50:
        score_band = "Vulnerable"
    else:
        score_band = "High Risk"

    liquid_share_pct = (
        ((liquid_assets + equity_mf) / total_investments * 100.0)
        if total_investments > 0
        else 0.0
    )

    metrics = {
        "annual_income": round(annual_income, 2),
        "monthly_essential_burn": round(monthly_essential_burn, 2),
        "monthly_total_expenses": round(essential_exp + emi_exp + discretionary_exp, 2),
        "liquid_assets": round(liquid_assets, 2),
        "emergency_runway_months": r1["runway_months"],
        "emergency_target_months": 6.0,
        "emergency_shortfall_inr": r1["gap_inr"],
        "employer_medical_cover": round(employer_med, 2),
        "personal_medical_cover": round(personal_med, 2),
        "total_medical_cover": round(employer_med + personal_med, 2),
        "recommended_medical_cover": r2["recommended_cover"],
        "medical_shortfall_inr": r2["gap_inr"],
        "total_investments": round(total_investments, 2),
        "locked_endowment_value": round(lic_endowment, 2),
        "locked_endowment_share_pct": r3["locked_share_pct"],
        "liquid_share_pct": round(liquid_share_pct, 1),
        "market_growth_value": round(equity_mf, 2),
        "retirement_locked_value": round(retire_epf_ppf, 2),
        "personal_accident_cover": round(personal_accident, 2),
        "recommended_pa_cover": r4["recommended_pa"],
        "term_life_cover": round(term_life, 2),
        "recommended_term_cover": r4["recommended_term"],
        "projected_retirement_corpus": r5["projected_corpus"],
        "target_retirement_corpus": r5["target_corpus"],
        "retirement_funded_pct": r5["funded_pct"],
        "retirement_gap_inr": r5["gap_inr"],
    }

    return {
        "security_score": security_score,
        "score_band": score_band,
        "metrics": metrics,
        "findings": raw_findings,
    }
