"""
Pydantic request and response models for FinSafe API contract.
Compatible with Pydantic v2 (and seamlessly falls back if run on Pydantic v1).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


PolicyTypeLiteral = Literal[
    "medical_employer",
    "medical_personal",
    "term_life",
    "personal_accident",
]

InvestmentCategoryLiteral = Literal[
    "liquid",
    "equity_mf",
    "retirement_epf_ppf_nps",
    "lic_endowment_ulip",
]

ExpenseCategoryLiteral = Literal[
    "essential",
    "emi_debt",
    "discretionary",
]

SeverityLiteral = Literal["critical", "warning", "info"]


class ProfileUpsertRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    alias: str = Field(default="Aarav", min_length=1, max_length=64)
    age: int = Field(..., ge=18, le=80, description="Current age in years")
    retirement_age: int = Field(default=60, ge=40, le=85, description="Target retirement age")
    annual_income: float = Field(..., gt=0, description="Gross annual income in INR")
    dependents: int = Field(default=0, ge=0, le=15, description="Number of financial dependents")
    monthly_retirement_contribution: float = Field(
        default=0.0,
        ge=0,
        description="Monthly EPF + NPS + retirement SIP contribution in INR",
    )


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    alias: str
    age: int
    retirement_age: int
    annual_income: float
    dependents: int
    monthly_retirement_contribution: float
    updated_at: str


class InsurancePolicyItem(BaseModel):
    policy_type: PolicyTypeLiteral
    provider_name: str = Field(..., min_length=1, max_length=128)
    sum_assured: float = Field(..., ge=0)
    annual_premium: float = Field(default=0.0, ge=0)


class InsuranceBulkUpsertRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    policies: List[InsurancePolicyItem]


class InsurancePolicyResponse(InsurancePolicyItem):
    id: int
    user_id: int


class InvestmentItem(BaseModel):
    category: InvestmentCategoryLiteral
    instrument_name: str = Field(..., min_length=1, max_length=128)
    current_value: float = Field(..., ge=0)
    is_locked: Optional[bool] = None


class InvestmentBulkUpsertRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    investments: List[InvestmentItem]


class InvestmentResponse(BaseModel):
    id: int
    user_id: int
    category: InvestmentCategoryLiteral
    instrument_name: str
    current_value: float
    is_locked: bool


class ExpenseItem(BaseModel):
    category: ExpenseCategoryLiteral
    label: str = Field(..., min_length=1, max_length=128)
    monthly_amount: float = Field(..., ge=0)


class ExpenseBulkUpsertRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)
    expenses: List[ExpenseItem]


class ExpenseResponse(ExpenseItem):
    id: int
    user_id: int


class AuditRunRequest(BaseModel):
    user_id: int = Field(default=1, ge=1)


class FindingSchema(BaseModel):
    rule_id: str
    title: str
    severity: SeverityLiteral
    deterministic_message: str
    plain_explanation: str
    current_value_label: str
    target_value_label: str
    gap_inr: float


class RecommendationSchema(BaseModel):
    id: Optional[int] = None
    priority_order: int
    week_bucket: str
    rule_id: str
    title: str
    description: str
    is_completed: bool = False


class RecommendationToggleRequest(BaseModel):
    is_completed: bool


class DashboardMetricsSchema(BaseModel):
    annual_income: float
    monthly_essential_burn: float
    monthly_total_expenses: float
    liquid_assets: float
    emergency_runway_months: float
    emergency_target_months: float
    emergency_shortfall_inr: float
    employer_medical_cover: float
    personal_medical_cover: float
    total_medical_cover: float
    recommended_medical_cover: float
    medical_shortfall_inr: float
    total_investments: float
    locked_endowment_value: float
    locked_endowment_share_pct: float
    liquid_share_pct: float
    market_growth_value: float
    retirement_locked_value: float
    personal_accident_cover: float
    recommended_pa_cover: float
    term_life_cover: float
    recommended_term_cover: float
    projected_retirement_corpus: float
    target_retirement_corpus: float
    retirement_funded_pct: float
    retirement_gap_inr: float


class AuditReportResponse(BaseModel):
    audit_run_id: int
    user_id: int
    alias: str
    security_score: int
    score_band: str
    llm_used: bool
    created_at: str
    metrics: DashboardMetricsSchema
    findings: List[FindingSchema]
    action_plan: List[RecommendationSchema]


class DemoSeedRequest(BaseModel):
    persona: Literal["anxious_tech_worker", "lic_heavy_saver", "well_prepared"] = "anxious_tech_worker"
    user_id: int = Field(default=1, ge=1)
