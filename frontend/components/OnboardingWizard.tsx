"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Plus,
  Shield,
  Trash2,
  User,
  Wallet,
  CreditCard,
} from "lucide-react";
import {
  ExpenseInput,
  InsurancePolicyInput,
  InvestmentInput,
  ProfileInput,
} from "@/lib/types";
import { formatCompactINR } from "@/lib/api";

interface OnboardingWizardProps {
  initialProfile: ProfileInput;
  initialPolicies: InsurancePolicyInput[];
  initialInvestments: InvestmentInput[];
  initialExpenses: ExpenseInput[];
  onSubmitAll: (
    profile: ProfileInput,
    policies: InsurancePolicyInput[],
    investments: InvestmentInput[],
    expenses: ExpenseInput[]
  ) => Promise<void>;
  isSubmitting: boolean;
}

const STEPS = [
  { id: 1, label: "Profile & Income", icon: User },
  { id: 2, label: "Insurance Cover", icon: Shield },
  { id: 3, label: "Investments & LIC", icon: Wallet },
  { id: 4, label: "Monthly Expenses", icon: CreditCard },
];

export function OnboardingWizard({
  initialProfile,
  initialPolicies,
  initialInvestments,
  initialExpenses,
  onSubmitAll,
  isSubmitting,
}: OnboardingWizardProps) {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState<ProfileInput>(initialProfile);
  const [policies, setPolicies] = useState<InsurancePolicyInput[]>(initialPolicies);
  const [investments, setInvestments] = useState<InvestmentInput[]>(initialInvestments);
  const [expenses, setExpenses] = useState<ExpenseInput[]>(initialExpenses);
  const [error, setError] = useState<string | null>(null);

  const validateStep = (): boolean => {
    setError(null);
    if (step === 1) {
      if (!profile.alias.trim()) {
        setError("Please enter your first name or alias.");
        return false;
      }
      if (profile.age < 18 || profile.age >= profile.retirement_age) {
        setError("Retirement age must be greater than your current age (18+).");
        return false;
      }
      if (profile.annual_income <= 0) {
        setError("Annual income must be greater than ₹0.");
        return false;
      }
    }
    return true;
  };

  const handleNext = async () => {
    if (!validateStep()) return;
    if (step < 4) {
      setStep(step + 1);
    } else {
      await onSubmitAll(profile, policies, investments, expenses);
    }
  };

  return (
    <div className="rounded-2xl bg-ink-900/95 border border-slate-800 p-6 shadow-2xl space-y-6">
      {/* Stepper Header */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {STEPS.map((s) => {
          const Icon = s.icon;
          const active = step === s.id;
          const done = step > s.id;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                if (s.id < step || validateStep()) setStep(s.id);
              }}
              className={`flex items-center gap-2.5 p-3 rounded-xl border text-left transition-all ${
                active
                  ? "bg-emerald-500/15 border-emerald-500/50 text-white"
                  : done
                  ? "bg-slate-900/90 border-emerald-500/30 text-emerald-300"
                  : "bg-slate-900/40 border-slate-800 text-slate-400"
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                  active
                    ? "bg-emerald-500 text-slate-950"
                    : done
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {done ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
              </div>
              <div className="truncate">
                <div className="text-[10px] uppercase tracking-wider opacity-75">
                  Step {s.id}
                </div>
                <div className="text-xs font-semibold truncate">{s.label}</div>
              </div>
            </button>
          );
        })}
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl bg-rose-500/15 border border-rose-500/40 p-3 text-xs text-rose-200"
        >
          {error}
        </div>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="space-y-4"
        >
          {step === 1 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  First Name / Alias (No PII stored)
                </label>
                <input
                  type="text"
                  value={profile.alias}
                  onChange={(e) => setProfile({ ...profile, alias: e.target.value })}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Annual Pre-Tax Income (₹) —{" "}
                  <span className="text-emerald-400">
                    {formatCompactINR(profile.annual_income)}
                  </span>
                </label>
                <input
                  type="number"
                  value={profile.annual_income}
                  onChange={(e) =>
                    setProfile({ ...profile, annual_income: Number(e.target.value) })
                  }
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Current Age (Years)
                </label>
                <input
                  type="number"
                  value={profile.age}
                  onChange={(e) => setProfile({ ...profile, age: Number(e.target.value) })}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Target Retirement Age
                </label>
                <input
                  type="number"
                  value={profile.retirement_age}
                  onChange={(e) =>
                    setProfile({ ...profile, retirement_age: Number(e.target.value) })
                  }
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Financial Dependents (Parents / Spouse / Kids)
                </label>
                <input
                  type="number"
                  value={profile.dependents}
                  onChange={(e) =>
                    setProfile({ ...profile, dependents: Number(e.target.value) })
                  }
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Monthly Retirement Saving (EPF + NPS + SIP in ₹)
                </label>
                <input
                  type="number"
                  value={profile.monthly_retirement_contribution}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      monthly_retirement_contribution: Number(e.target.value),
                    })
                  }
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-300">
                  Separate your employer group health policy from standalone personal policies.
                </p>
                <button
                  type="button"
                  onClick={() =>
                    setPolicies([
                      ...policies,
                      {
                        policy_type: "medical_personal",
                        provider_name: "Personal Health Cover",
                        sum_assured: 1000000,
                        annual_premium: 12000,
                      },
                    ])
                  }
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Policy
                </button>
              </div>
              {policies.map((p, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-center bg-slate-950/80 p-3 rounded-xl border border-slate-800"
                >
                  <select
                    value={p.policy_type}
                    onChange={(e) => {
                      const next = [...policies];
                      next[idx].policy_type = e.target.value as any;
                      setPolicies(next);
                    }}
                    className="sm:col-span-4 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  >
                    <option value="medical_employer">Medical (Employer Group)</option>
                    <option value="medical_personal">Medical (Personal Retail)</option>
                    <option value="term_life">Pure Term Life Cover</option>
                    <option value="personal_accident">Personal Accident Cover</option>
                  </select>
                  <input
                    type="text"
                    value={p.provider_name}
                    onChange={(e) => {
                      const next = [...policies];
                      next[idx].provider_name = e.target.value;
                      setPolicies(next);
                    }}
                    placeholder="Policy Name"
                    className="sm:col-span-4 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  />
                  <input
                    type="number"
                    value={p.sum_assured}
                    onChange={(e) => {
                      const next = [...policies];
                      next[idx].sum_assured = Number(e.target.value);
                      setPolicies(next);
                    }}
                    placeholder="Sum Assured (₹)"
                    className="sm:col-span-3 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  />
                  <button
                    type="button"
                    onClick={() => setPolicies(policies.filter((_, i) => i !== idx))}
                    className="sm:col-span-1 text-rose-400 hover:text-rose-300 flex justify-center"
                    aria-label="Remove policy"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-300">
                  Include bank/FD liquid cash, mutual funds, EPF/PPF, and locked LIC/endowment plans.
                </p>
                <button
                  type="button"
                  onClick={() =>
                    setInvestments([
                      ...investments,
                      {
                        category: "liquid",
                        instrument_name: "Emergency FD",
                        current_value: 100000,
                      },
                    ])
                  }
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Asset
                </button>
              </div>
              {investments.map((inv, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-center bg-slate-950/80 p-3 rounded-xl border border-slate-800"
                >
                  <select
                    value={inv.category}
                    onChange={(e) => {
                      const next = [...investments];
                      next[idx].category = e.target.value as any;
                      setInvestments(next);
                    }}
                    className="sm:col-span-4 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  >
                    <option value="liquid">Liquid (Savings / FD / Liquid MF)</option>
                    <option value="equity_mf">Equity & Mutual Funds</option>
                    <option value="retirement_epf_ppf_nps">EPF / PPF / NPS</option>
                    <option value="lic_endowment_ulip">Locked LIC / Endowment / ULIP</option>
                  </select>
                  <input
                    type="text"
                    value={inv.instrument_name}
                    onChange={(e) => {
                      const next = [...investments];
                      next[idx].instrument_name = e.target.value;
                      setInvestments(next);
                    }}
                    placeholder="Instrument Label"
                    className="sm:col-span-4 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  />
                  <input
                    type="number"
                    value={inv.current_value}
                    onChange={(e) => {
                      const next = [...investments];
                      next[idx].current_value = Number(e.target.value);
                      setInvestments(next);
                    }}
                    placeholder="Current Value (₹)"
                    className="sm:col-span-3 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  />
                  <button
                    type="button"
                    onClick={() =>
                      setInvestments(investments.filter((_, i) => i !== idx))
                    }
                    className="sm:col-span-1 text-rose-400 hover:text-rose-300 flex justify-center"
                    aria-label="Remove investment"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {step === 4 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-300">
                  Essential expenses + EMIs determine your mandatory monthly survival burn rate.
                </p>
                <button
                  type="button"
                  onClick={() =>
                    setExpenses([
                      ...expenses,
                      {
                        category: "essential",
                        label: "Household & Utilities",
                        monthly_amount: 25000,
                      },
                    ])
                  }
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Expense
                </button>
              </div>
              {expenses.map((exp, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-center bg-slate-950/80 p-3 rounded-xl border border-slate-800"
                >
                  <select
                    value={exp.category}
                    onChange={(e) => {
                      const next = [...expenses];
                      next[idx].category = e.target.value as any;
                      setExpenses(next);
                    }}
                    className="sm:col-span-4 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  >
                    <option value="essential">Essential Needs (Rent, Food, Meds)</option>
                    <option value="emi_debt">EMIs & Debt Repayments</option>
                    <option value="discretionary">Discretionary / Lifestyle</option>
                  </select>
                  <input
                    type="text"
                    value={exp.label}
                    onChange={(e) => {
                      const next = [...expenses];
                      next[idx].label = e.target.value;
                      setExpenses(next);
                    }}
                    placeholder="Expense Label"
                    className="sm:col-span-4 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  />
                  <input
                    type="number"
                    value={exp.monthly_amount}
                    onChange={(e) => {
                      const next = [...expenses];
                      next[idx].monthly_amount = Number(e.target.value);
                      setExpenses(next);
                    }}
                    placeholder="Monthly Amount (₹)"
                    className="sm:col-span-3 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-2 text-xs text-white"
                  />
                  <button
                    type="button"
                    onClick={() => setExpenses(expenses.filter((_, i) => i !== idx))}
                    className="sm:col-span-1 text-rose-400 hover:text-rose-300 flex justify-center"
                    aria-label="Remove expense"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-800">
        <button
          type="button"
          disabled={step === 1}
          onClick={() => setStep(Math.max(1, step - 1))}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold border border-slate-700 text-slate-300 disabled:opacity-40"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>

        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleNext}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors shadow-lg shadow-emerald-500/20"
        >
          {step < 4 ? (
            <>
              Next Step <ArrowRight className="w-4 h-4" />
            </>
          ) : isSubmitting ? (
            "Running Deterministic Audit..."
          ) : (
            <>
              Run Financial Security Audit <Check className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
