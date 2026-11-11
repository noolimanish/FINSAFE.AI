"""
FastAPI application entrypoint for FinSafe — Personal Financial Security Health Check.
Exposes REST endpoints for profile, insurance policies, investments, monthly expenses,
health check execution, latest report retrieval, action plan checklist toggling, and demo personas.
"""

from __future__ import annotations

import os
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.llm_service import generate_explanations_and_plan
from app.models import FinSafeRepository
from app.rules_engine import run_financial_health_check
from app.schemas import (
    AuditReportResponse,
    AuditRunRequest,
    DemoSeedRequest,
    ExpenseBulkUpsertRequest,
    ExpenseResponse,
    InsuranceBulkUpsertRequest,
    InsurancePolicyResponse,
    InvestmentBulkUpsertRequest,
    InvestmentResponse,
    ProfileResponse,
    ProfileUpsertRequest,
    RecommendationSchema,
    RecommendationToggleRequest,
)


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(
        title="FinSafe — Personal Financial Security Health Check API",
        description="Deterministic India-specific financial security audit engine with AI plain-language explanations.",
        version="1.0.0",
    )

    origins = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    repo = FinSafeRepository(db_path=db_path)
    app.state.repo = repo

    @app.get("/health")
    async def health_check() -> Dict[str, object]:
        return {
            "status": "ok",
            "llm_configured": bool(os.getenv("LLM_API_KEY", "").strip()),
            "version": "1.0.0",
        }

    @app.post("/api/v1/profile", response_model=ProfileResponse)
    async def upsert_profile(payload: ProfileUpsertRequest) -> Dict[str, object]:
        if payload.retirement_age <= payload.age:
            raise HTTPException(
                status_code=400,
                detail="retirement_age must be greater than current age.",
            )
        data = payload.dict() if hasattr(payload, "dict") else payload.model_dump()
        return app.state.repo.upsert_profile(payload.user_id, data)

    @app.get("/api/v1/profile", response_model=ProfileResponse)
    async def get_profile(user_id: int = Query(default=1, ge=1)) -> Dict[str, object]:
        prof = app.state.repo.get_profile(user_id)
        if not prof:
            raise HTTPException(status_code=404, detail="Profile not found.")
        return prof

    @app.post("/api/v1/insurance", response_model=List[InsurancePolicyResponse])
    async def save_insurance_policies(
        payload: InsuranceBulkUpsertRequest,
    ) -> List[Dict[str, object]]:
        items = [
            p.dict() if hasattr(p, "dict") else p.model_dump()
            for p in payload.policies
        ]
        return app.state.repo.replace_insurance_policies(payload.user_id, items)

    @app.get("/api/v1/insurance", response_model=List[InsurancePolicyResponse])
    async def list_insurance_policies(
        user_id: int = Query(default=1, ge=1)
    ) -> List[Dict[str, object]]:
        return app.state.repo.list_insurance_policies(user_id)

    @app.post("/api/v1/investments", response_model=List[InvestmentResponse])
    async def save_investments(
        payload: InvestmentBulkUpsertRequest,
    ) -> List[Dict[str, object]]:
        items = [
            i.dict() if hasattr(i, "dict") else i.model_dump()
            for i in payload.investments
        ]
        return app.state.repo.replace_investments(payload.user_id, items)

    @app.get("/api/v1/investments", response_model=List[InvestmentResponse])
    async def list_investments(
        user_id: int = Query(default=1, ge=1)
    ) -> List[Dict[str, object]]:
        return app.state.repo.list_investments(user_id)

    @app.post("/api/v1/expenses", response_model=List[ExpenseResponse])
    async def save_expenses(
        payload: ExpenseBulkUpsertRequest,
    ) -> List[Dict[str, object]]:
        items = [
            e.dict() if hasattr(e, "dict") else e.model_dump()
            for e in payload.expenses
        ]
        return app.state.repo.replace_expenses(payload.user_id, items)

    @app.get("/api/v1/expenses", response_model=List[ExpenseResponse])
    async def list_expenses(
        user_id: int = Query(default=1, ge=1)
    ) -> List[Dict[str, object]]:
        return app.state.repo.list_expenses(user_id)

    @app.post("/api/v1/audit/run", response_model=AuditReportResponse)
    async def run_audit(payload: AuditRunRequest) -> Dict[str, object]:
        prof = app.state.repo.get_profile(payload.user_id)
        if not prof:
            raise HTTPException(
                status_code=400,
                detail="Please complete your profile before running the financial health check.",
            )
        policies = app.state.repo.list_insurance_policies(payload.user_id)
        investments = app.state.repo.list_investments(payload.user_id)
        expenses = app.state.repo.list_expenses(payload.user_id)

        engine_out = run_financial_health_check(prof, policies, investments, expenses)
        enriched_findings, action_plan, llm_used = await generate_explanations_and_plan(
            prof, engine_out
        )
        saved = app.state.repo.save_audit_run(
            user_id=payload.user_id,
            security_score=engine_out["security_score"],
            score_band=engine_out["score_band"],
            metrics=engine_out["metrics"],
            findings=enriched_findings,
            action_plan=action_plan,
            llm_used=llm_used,
        )
        return saved

    @app.get("/api/v1/audit/latest", response_model=AuditReportResponse)
    async def get_latest_report(
        user_id: int = Query(default=1, ge=1)
    ) -> Dict[str, object]:
        report = app.state.repo.get_latest_audit_run(user_id)
        if not report:
            raise HTTPException(
                status_code=404,
                detail="No financial health check report found for this user.",
            )
        return report

    @app.get("/api/v1/audit/action-plan", response_model=List[RecommendationSchema])
    async def get_action_plan(
        user_id: int = Query(default=1, ge=1)
    ) -> List[Dict[str, object]]:
        report = app.state.repo.get_latest_audit_run(user_id)
        if not report:
            raise HTTPException(
                status_code=404,
                detail="No action plan found. Run a health check first.",
            )
        return report["action_plan"]

    @app.patch(
        "/api/v1/audit/action-plan/{item_id}",
        response_model=RecommendationSchema,
    )
    async def toggle_action_plan_item(
        item_id: int, payload: RecommendationToggleRequest
    ) -> Dict[str, object]:
        updated = app.state.repo.toggle_recommendation(item_id, payload.is_completed)
        if not updated:
            raise HTTPException(status_code=404, detail="Action plan item not found.")
        return updated

    @app.post("/api/v1/demo/seed", response_model=AuditReportResponse)
    async def seed_demo_persona(payload: DemoSeedRequest) -> Dict[str, object]:
        uid = payload.user_id
        if payload.persona == "anxious_tech_worker":
            app.state.repo.upsert_profile(
                uid,
                {
                    "alias": "Aarav Sharma (Bengaluru SDE-2)",
                    "age": 29,
                    "retirement_age": 60,
                    "annual_income": 18_00_000,
                    "dependents": 2,
                    "monthly_retirement_contribution": 12_000,
                },
            )
            app.state.repo.replace_insurance_policies(
                uid,
                [
                    {
                        "policy_type": "medical_employer",
                        "provider_name": "Corporate Group Health Floater",
                        "sum_assured": 5_00_000,
                        "annual_premium": 0,
                    }
                ],
            )
            app.state.repo.replace_investments(
                uid,
                [
                    {
                        "category": "liquid",
                        "instrument_name": "HDFC Salary Savings + Sweep FD",
                        "current_value": 1_35_000,
                        "is_locked": False,
                    },
                    {
                        "category": "equity_mf",
                        "instrument_name": "Nifty 50 & Flexi-Cap SIPs",
                        "current_value": 3_40_000,
                        "is_locked": False,
                    },
                    {
                        "category": "retirement_epf_ppf_nps",
                        "instrument_name": "Employee Provident Fund (EPF)",
                        "current_value": 4_10_000,
                        "is_locked": True,
                    },
                    {
                        "category": "lic_endowment_ulip",
                        "instrument_name": "LIC Jeevan Anand & Tax-Saver ULIP",
                        "current_value": 7_20_000,
                        "is_locked": True,
                    },
                ],
            )
            app.state.repo.replace_expenses(
                uid,
                [
                    {
                        "category": "essential",
                        "label": "Rent, Groceries, Utilities & Parents' Meds",
                        "monthly_amount": 48_000,
                    },
                    {
                        "category": "emi_debt",
                        "label": "Car Loan & Gadget EMIs",
                        "monthly_amount": 22_000,
                    },
                    {
                        "category": "discretionary",
                        "label": "Dining, Travel & Subscriptions",
                        "monthly_amount": 18_000,
                    },
                ],
            )
        elif payload.persona == "lic_heavy_saver":
            app.state.repo.upsert_profile(
                uid,
                {
                    "alias": "Priya Nair (Pune IT Lead)",
                    "age": 34,
                    "retirement_age": 58,
                    "annual_income": 24_00_000,
                    "dependents": 2,
                    "monthly_retirement_contribution": 22_000,
                },
            )
            app.state.repo.replace_insurance_policies(
                uid,
                [
                    {
                        "policy_type": "medical_employer",
                        "provider_name": "Employer Floater",
                        "sum_assured": 8_00_000,
                        "annual_premium": 0,
                    },
                    {
                        "policy_type": "medical_personal",
                        "provider_name": "Retail Family Health Plan",
                        "sum_assured": 10_00_000,
                        "annual_premium": 16_500,
                    },
                    {
                        "policy_type": "term_life",
                        "provider_name": "Pure Term Life Plan",
                        "sum_assured": 2_50_00_000,
                        "annual_premium": 24_000,
                    },
                ],
            )
            app.state.repo.replace_investments(
                uid,
                [
                    {
                        "category": "liquid",
                        "instrument_name": "Liquid Mutual Fund + Bank FD",
                        "current_value": 3_80_000,
                        "is_locked": False,
                    },
                    {
                        "category": "equity_mf",
                        "instrument_name": "Midcap & Index Mutual Funds",
                        "current_value": 6_20_000,
                        "is_locked": False,
                    },
                    {
                        "category": "retirement_epf_ppf_nps",
                        "instrument_name": "EPF + PPF Account",
                        "current_value": 9_50_000,
                        "is_locked": True,
                    },
                    {
                        "category": "lic_endowment_ulip",
                        "instrument_name": "4 Family LIC Endowment & Money-Back Plans",
                        "current_value": 18_50_000,
                        "is_locked": True,
                    },
                ],
            )
            app.state.repo.replace_expenses(
                uid,
                [
                    {
                        "category": "essential",
                        "label": "Household & School Fees",
                        "monthly_amount": 55_000,
                    },
                    {
                        "category": "emi_debt",
                        "label": "Home Loan EMI",
                        "monthly_amount": 35_000,
                    },
                    {
                        "category": "discretionary",
                        "label": "Family Outings & Shopping",
                        "monthly_amount": 15_000,
                    },
                ],
            )
        else:
            app.state.repo.upsert_profile(
                uid,
                {
                    "alias": "Rohan Verma (Hyderabad Staff Engineer)",
                    "age": 31,
                    "retirement_age": 60,
                    "annual_income": 28_00_000,
                    "dependents": 1,
                    "monthly_retirement_contribution": 55_000,
                },
            )
            app.state.repo.replace_insurance_policies(
                uid,
                [
                    {
                        "policy_type": "medical_employer",
                        "provider_name": "Employer Group Health",
                        "sum_assured": 10_00_000,
                        "annual_premium": 0,
                    },
                    {
                        "policy_type": "medical_personal",
                        "provider_name": "Base ₹15L + ₹75L Super Top-Up",
                        "sum_assured": 90_00_000,
                        "annual_premium": 22_000,
                    },
                    {
                        "policy_type": "term_life",
                        "provider_name": "Pure Term Life Cover",
                        "sum_assured": 3_00_00_000,
                        "annual_premium": 26_000,
                    },
                    {
                        "policy_type": "personal_accident",
                        "provider_name": "Standalone PA Disability Cover",
                        "sum_assured": 1_00_00_000,
                        "annual_premium": 3_200,
                    },
                ],
            )
            app.state.repo.replace_investments(
                uid,
                [
                    {
                        "category": "liquid",
                        "instrument_name": "Arbitrage + Liquid Fund + FD",
                        "current_value": 6_50_000,
                        "is_locked": False,
                    },
                    {
                        "category": "equity_mf",
                        "instrument_name": "Nifty 50 + Next 50 + Flexi Cap",
                        "current_value": 24_00_000,
                        "is_locked": False,
                    },
                    {
                        "category": "retirement_epf_ppf_nps",
                        "instrument_name": "EPF + NPS Tier-1",
                        "current_value": 16_00_000,
                        "is_locked": True,
                    },
                    {
                        "category": "lic_endowment_ulip",
                        "instrument_name": "Legacy Paid-Up LIC Policy",
                        "current_value": 2_00_000,
                        "is_locked": True,
                    },
                ],
            )
            app.state.repo.replace_expenses(
                uid,
                [
                    {
                        "category": "essential",
                        "label": "Rent, Groceries & Healthcare",
                        "monthly_amount": 52_000,
                    },
                    {
                        "category": "emi_debt",
                        "label": "Zero High-Interest Debt",
                        "monthly_amount": 20_000,
                    },
                    {
                        "category": "discretionary",
                        "label": "Travel & Hobbies",
                        "monthly_amount": 18_000,
                    },
                ],
            )

        return await run_audit(AuditRunRequest(user_id=uid))

    return app


app = create_app()
