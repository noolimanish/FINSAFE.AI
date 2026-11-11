"use client";

import React, { useEffect, useState } from "react";
import { Shield, SlidersHorizontal, Sparkles, RefreshCw } from "lucide-react";
import { finsafeApi } from "@/lib/api";
import {
  AuditReport,
  ExpenseInput,
  InsurancePolicyInput,
  InvestmentInput,
  ProfileInput,
} from "@/lib/types";
import { ScoreGauge } from "@/components/ScoreGauge";
import { FindingsList } from "@/components/FindingsList";
import { ChartsSection } from "@/components/ChartsSection";
import { ActionPlanChecklist } from "@/components/ActionPlanChecklist";
import { OnboardingWizard } from "@/components/OnboardingWizard";

const DEFAULT_PROFILE: ProfileInput = {
  alias: "Aarav Sharma (Bengaluru SDE-2)",
  age: 29,
  retirement_age: 60,
  annual_income: 1800000,
  dependents: 2,
  monthly_retirement_contribution: 12000,
};

const DEFAULT_POLICIES: InsurancePolicyInput[] = [
  {
    policy_type: "medical_employer",
    provider_name: "Corporate Group Health Floater",
    sum_assured: 500000,
    annual_premium: 0,
  },
];

const DEFAULT_INVESTMENTS: InvestmentInput[] = [
  {
    category: "liquid",
    instrument_name: "HDFC Salary Savings + Sweep FD",
    current_value: 135000,
  },
  {
    category: "equity_mf",
    instrument_name: "Nifty 50 & Flexi-Cap SIPs",
    current_value: 340000,
  },
  {
    category: "retirement_epf_ppf_nps",
    instrument_name: "Employee Provident Fund (EPF)",
    current_value: 410000,
  },
  {
    category: "lic_endowment_ulip",
    instrument_name: "LIC Jeevan Anand & Tax-Saver ULIP",
    current_value: 720000,
  },
];

const DEFAULT_EXPENSES: ExpenseInput[] = [
  {
    category: "essential",
    label: "Rent, Groceries & Parents' Meds",
    monthly_amount: 48000,
  },
  {
    category: "emi_debt",
    label: "Car Loan & Gadget EMIs",
    monthly_amount: 22000,
  },
  {
    category: "discretionary",
    label: "Dining, Travel & Subscriptions",
    monthly_amount: 18000,
  },
];

export default function FinSafePage() {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPersona = async (
    persona: "anxious_tech_worker" | "lic_heavy_saver" | "well_prepared"
  ) => {
    setLoading(true);
    setError(null);
    try {
      const data = await finsafeApi.seedPersona(persona);
      setReport(data);
      setShowWizard(false);
    } catch (err: any) {
      setError(
        err.message ||
          "Could not reach FastAPI backend at http://localhost:8000. Ensure uvicorn is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPersona("anxious_tech_worker");
  }, []);

  const handleFullSubmit = async (
    profile: ProfileInput,
    policies: InsurancePolicyInput[],
    investments: InvestmentInput[],
    expenses: ExpenseInput[]
  ) => {
    setLoading(true);
    setError(null);
    try {
      await finsafeApi.saveProfile(profile);
      await finsafeApi.saveInsurance(policies);
      await finsafeApi.saveInvestments(investments);
      await finsafeApi.saveExpenses(expenses);
      const updated = await finsafeApi.runAudit();
      setReport(updated);
      setShowWizard(false);
    } catch (err: any) {
      setError(err.message || "Failed to run audit.");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleChecklist = async (id: number, nextState: boolean) => {
    if (!report) return;
    // Optimistic UI update
    const prevPlan = report.action_plan;
    setReport({
      ...report,
      action_plan: report.action_plan.map((item) =>
        item.id === id ? { ...item, is_completed: nextState } : item
      ),
    });
    try {
      await finsafeApi.toggleActionItem(id, nextState);
    } catch {
      setReport({ ...report, action_plan: prevPlan });
    }
  };

  const criticalCount =
    report?.findings.filter((f) => f.severity === "critical").length ?? 0;
  const warningCount =
    report?.findings.filter((f) => f.severity === "warning").length ?? 0;

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Navigation */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/10">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight font-display">
                FinSafe
              </h1>
              <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                India Financial Security Check
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic downside-risk rules engine + AI plain-language clarity. Zero PII stored.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => loadPersona("anxious_tech_worker")}
            className="text-xs px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-colors"
          >
            Demo: Bengaluru SDE-2
          </button>
          <button
            type="button"
            onClick={() => loadPersona("lic_heavy_saver")}
            className="text-xs px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-colors"
          >
            Demo: LIC-Heavy Saver
          </button>
          <button
            type="button"
            onClick={() => loadPersona("well_prepared")}
            className="text-xs px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-colors"
          >
            Demo: Resilient Planner
          </button>
          <button
            type="button"
            onClick={() => setShowWizard(!showWizard)}
            className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            {showWizard ? "View Dashboard" : "Edit Financial Snapshot"}
          </button>
        </div>
      </header>

      {error && (
        <div className="rounded-2xl bg-rose-500/15 border border-rose-500/40 p-4 text-sm text-rose-200 flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => loadPersona("anxious_tech_worker")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-100 text-xs font-semibold"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      )}

      {showWizard ? (
        <OnboardingWizard
          initialProfile={DEFAULT_PROFILE}
          initialPolicies={DEFAULT_POLICIES}
          initialInvestments={DEFAULT_INVESTMENTS}
          initialExpenses={DEFAULT_EXPENSES}
          onSubmitAll={handleFullSubmit}
          isSubmitting={loading}
        />
      ) : loading || !report ? (
        <div className="space-y-6 animate-pulse">
          <div className="h-48 rounded-2xl bg-slate-900/80 border border-slate-800" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="h-72 rounded-2xl bg-slate-900/80 border border-slate-800" />
            <div className="h-72 rounded-2xl bg-slate-900/80 border border-slate-800" />
            <div className="h-72 rounded-2xl bg-slate-900/80 border border-slate-800" />
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          <ScoreGauge
            score={report.security_score}
            band={report.score_band}
            alias={report.alias}
            llmUsed={report.llm_used}
            criticalCount={criticalCount}
            warningCount={warningCount}
          />

          <ChartsSection metrics={report.metrics} />

          <FindingsList findings={report.findings} />

          <ActionPlanChecklist
            items={report.action_plan}
            onToggle={handleToggleChecklist}
          />
        </div>
      )}
    </main>
  );
}
