"""
Test suite for FinSafe covering all 5 deterministic rules in rules_engine.py
and full end-to-end API workflow tests via FastAPI TestClient.
Compatible with both `pytest` and `python3 -m unittest`.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from fastapi.testclient import TestClient

from app.main import create_app
from app.rules_engine import (
    evaluate_r1_emergency_fund,
    evaluate_r2_medical_insurance,
    evaluate_r3_endowment_lock_in,
    evaluate_r4_accident_and_term_cover,
    evaluate_r5_retirement_readiness,
)


def test_r1_emergency_fund_thresholds() -> None:
    # < 3 months = critical
    res_crit = evaluate_r1_emergency_fund(liquid_assets=1_00_000, monthly_essential_burn=50_000)
    assert res_crit["severity"] == "critical"
    assert res_crit["runway_months"] == 2.0
    assert res_crit["gap_inr"] == 2_00_000

    # 3 to < 6 months = warning
    res_warn = evaluate_r1_emergency_fund(liquid_assets=2_00_000, monthly_essential_burn=50_000)
    assert res_warn["severity"] == "warning"
    assert res_warn["runway_months"] == 4.0

    # >= 6 months = info
    res_safe = evaluate_r1_emergency_fund(liquid_assets=3_50_000, monthly_essential_burn=50_000)
    assert res_safe["severity"] == "info"
    assert res_safe["gap_inr"] == 0.0


def test_r2_medical_insurance_employer_trap_and_3x_rule() -> None:
    # Relying 100% on employer cover (0 personal cover) = critical
    res_emp_only = evaluate_r2_medical_insurance(
        employer_medical=5_00_000, personal_medical=0, annual_income=15_00_000
    )
    assert res_emp_only["severity"] == "critical"

    # Personal cover exists (₹10L) + Employer (₹5L) = ₹15L, but < 3x annual income (₹36L) = warning
    res_warn = evaluate_r2_medical_insurance(
        employer_medical=5_00_000, personal_medical=10_00_000, annual_income=12_00_000
    )
    assert res_warn["severity"] == "warning"
    assert res_warn["recommended_cover"] == 36_00_000

    # Personal cover >= ₹10L and total >= 3x annual income = info
    res_safe = evaluate_r2_medical_insurance(
        employer_medical=10_00_000, personal_medical=30_00_000, annual_income=12_00_000
    )
    assert res_safe["severity"] == "info"


def test_r3_lic_endowment_lock_in_ratio() -> None:
    # > 40% locked in LIC/endowment = warning
    res_warn = evaluate_r3_endowment_lock_in(
        lic_endowment_value=5_00_000, total_investments=10_00_000
    )
    assert res_warn["severity"] == "warning"
    assert res_warn["locked_share_pct"] == 50.0
    assert res_warn["gap_inr"] == 1_00_000

    # <= 40% = info
    res_info = evaluate_r3_endowment_lock_in(
        lic_endowment_value=2_00_000, total_investments=10_00_000
    )
    assert res_info["severity"] == "info"
    assert res_info["locked_share_pct"] == 20.0


def test_r4_personal_accident_and_term_cover() -> None:
    # Dependents > 0 and zero term cover = critical
    res_crit = evaluate_r4_accident_and_term_cover(
        personal_accident_cover=0, term_life_cover=0, annual_income=12_00_000, dependents=2
    )
    assert res_crit["severity"] == "critical"

    # No dependents, but no personal accident cover = warning
    res_warn = evaluate_r4_accident_and_term_cover(
        personal_accident_cover=0, term_life_cover=0, annual_income=12_00_000, dependents=0
    )
    assert res_warn["severity"] == "warning"

    # Adequate PA and term cover = info
    res_info = evaluate_r4_accident_and_term_cover(
        personal_accident_cover=40_00_000,
        term_life_cover=1_50_00_000,
        annual_income=12_00_000,
        dependents=1,
    )
    assert res_info["severity"] == "info"


def test_r5_retirement_corpus_projection() -> None:
    # Low corpus & low contribution = critical
    res_crit = evaluate_r5_retirement_readiness(
        age=30,
        retirement_age=60,
        current_retirement_corpus=2_00_000,
        monthly_retirement_contribution=5_000,
        monthly_lifestyle_expense=50_000,
    )
    assert res_crit["severity"] == "critical"
    assert res_crit["funded_pct"] < 60.0

    # High corpus & strong SIP = info
    res_safe = evaluate_r5_retirement_readiness(
        age=30,
        retirement_age=60,
        current_retirement_corpus=25_00_000,
        monthly_retirement_contribution=45_000,
        monthly_lifestyle_expense=40_000,
    )
    assert res_safe["severity"] == "info"
    assert res_safe["funded_pct"] >= 100.0


def test_api_health_endpoint() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = TestClient(create_app(db_path=db_path))
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "llm_configured" in body


def test_api_full_onboarding_and_audit_workflow() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = TestClient(create_app(db_path=db_path))

        # 1. Create profile
        r_prof = client.post(
            "/api/v1/profile",
            json={
                "user_id": 1,
                "alias": "Vikram",
                "age": 28,
                "retirement_age": 60,
                "annual_income": 15_00_000,
                "dependents": 1,
                "monthly_retirement_contribution": 10_000,
            },
        )
        assert r_prof.status_code == 200
        assert r_prof.json()["alias"] == "Vikram"

        # 2. Add insurance policies
        r_ins = client.post(
            "/api/v1/insurance",
            json={
                "user_id": 1,
                "policies": [
                    {
                        "policy_type": "medical_employer",
                        "provider_name": "CorpCover",
                        "sum_assured": 4_00_000,
                        "annual_premium": 0,
                    }
                ],
            },
        )
        assert r_ins.status_code == 200
        assert len(r_ins.json()) == 1

        # 3. Add investments
        r_inv = client.post(
            "/api/v1/investments",
            json={
                "user_id": 1,
                "investments": [
                    {
                        "category": "liquid",
                        "instrument_name": "Savings Account",
                        "current_value": 90_000,
                    },
                    {
                        "category": "lic_endowment_ulip",
                        "instrument_name": "LIC Endowment",
                        "current_value": 4_00_000,
                    },
                ],
            },
        )
        assert r_inv.status_code == 200

        # 4. Add monthly expenses
        r_exp = client.post(
            "/api/v1/expenses",
            json={
                "user_id": 1,
                "expenses": [
                    {"category": "essential", "label": "Rent & Food", "monthly_amount": 40_000},
                    {"category": "emi_debt", "label": "Bike Loan", "monthly_amount": 10_000},
                ],
            },
        )
        assert r_exp.status_code == 200

        # 5. Run health check
        r_audit = client.post("/api/v1/audit/run", json={"user_id": 1})
        assert r_audit.status_code == 200
        report = r_audit.json()
        assert 0 <= report["security_score"] <= 100
        assert len(report["findings"]) == 5
        assert len(report["action_plan"]) == 4

        # 6. Toggle action plan item
        first_item_id = report["action_plan"][0]["id"]
        r_toggle = client.patch(
            f"/api/v1/audit/action-plan/{first_item_id}",
            json={"is_completed": True},
        )
        assert r_toggle.status_code == 200
        assert r_toggle.json()["is_completed"] is True


def test_api_demo_seed_endpoint() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = TestClient(create_app(db_path=db_path))
        resp = client.post(
            "/api/v1/demo/seed",
            json={"persona": "anxious_tech_worker", "user_id": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["alias"].startswith("Aarav")
        assert len(data["findings"]) == 5


class FinSafeUnitTestSuite(unittest.TestCase):
    def test_all(self) -> None:
        test_r1_emergency_fund_thresholds()
        test_r2_medical_insurance_employer_trap_and_3x_rule()
        test_r3_lic_endowment_lock_in_ratio()
        test_r4_personal_accident_and_term_cover()
        test_r5_retirement_corpus_projection()
        test_api_health_endpoint()
        test_api_full_onboarding_and_audit_workflow()
        test_api_demo_seed_endpoint()


if __name__ == "__main__":
    unittest.main()
