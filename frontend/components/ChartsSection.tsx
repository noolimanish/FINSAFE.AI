"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { DashboardMetrics } from "@/lib/types";
import { formatCompactINR, formatINR } from "@/lib/api";

interface ChartsSectionProps {
  metrics: DashboardMetrics;
}

export function ChartsSection({ metrics }: ChartsSectionProps) {
  const medicalData = [
    {
      name: "Employer Cover",
      amountLakhs: Number((metrics.employer_medical_cover / 100000).toFixed(1)),
      fill: "#64748B",
    },
    {
      name: "Personal Cover",
      amountLakhs: Number((metrics.personal_medical_cover / 100000).toFixed(1)),
      fill:
        metrics.personal_medical_cover <= 0
          ? "#F43F5E"
          : metrics.personal_medical_cover < 1000000
          ? "#F59E0B"
          : "#10B981",
    },
    {
      name: "3× Income Target",
      amountLakhs: Number((metrics.recommended_medical_cover / 100000).toFixed(1)),
      fill: "#3B82F6",
    },
  ];

  const portfolioSlices = [
    {
      name: "Liquid Cash / FD",
      value: metrics.liquid_assets,
      color: "#10B981",
    },
    {
      name: "Equity & Mutual Funds",
      value: metrics.market_growth_value,
      color: "#3B82F6",
    },
    {
      name: "EPF / PPF / NPS",
      value: metrics.retirement_locked_value,
      color: "#6366F1",
    },
    {
      name: "Locked LIC / Endowment",
      value: metrics.locked_endowment_value,
      color: "#F59E0B",
    },
  ].filter((s) => s.value > 0);

  const runwayMonths = metrics.emergency_runway_months;
  const runwayPct = Math.min(100, (runwayMonths / 12) * 100);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 1. Coverage vs Need Bar Chart */}
      <div className="rounded-2xl bg-ink-900/90 border border-slate-800/80 p-5 shadow-xl flex flex-col justify-between">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
            Medical Protection
          </span>
          <h3 className="text-base font-bold text-white mt-0.5 font-display">
            Coverage vs. 3× Income Need (₹ Lakhs)
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Employer health insurance disappears when you switch jobs.
          </p>
        </div>

        <div className="h-56 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={medicalData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <XAxis
                dataKey="name"
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `₹${v}L`}
              />
              <Tooltip
                formatter={(val: number) => [`₹${val} Lakhs`, "Cover"]}
                contentStyle={{
                  backgroundColor: "#0B132B",
                  borderColor: "#1E293B",
                  borderRadius: "10px",
                  color: "#F8FAFC",
                }}
              />
              <Bar dataKey="amountLakhs" radius={[8, 8, 0, 0]}>
                {medicalData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-800/80 flex justify-between text-xs">
          <span className="text-slate-400">Personal Portable Cover:</span>
          <span
            className={`font-semibold ${
              metrics.personal_medical_cover <= 0 ? "text-rose-400" : "text-emerald-400"
            }`}
          >
            {formatCompactINR(metrics.personal_medical_cover)}
          </span>
        </div>
      </div>

      {/* 2. Emergency Fund Runway */}
      <div className="rounded-2xl bg-ink-900/90 border border-slate-800/80 p-5 shadow-xl flex flex-col justify-between">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">
            Survival Cushion
          </span>
          <h3 className="text-base font-bold text-white mt-0.5 font-display">
            Emergency Fund Runway
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Based on {formatINR(metrics.monthly_essential_burn)}/mo mandatory burn (Needs + EMIs).
          </p>
        </div>

        <div className="my-6 space-y-4">
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-bold text-white font-display">
                {runwayMonths.toFixed(1)}
              </span>
              <span className="text-sm text-slate-400 ml-1.5">months covered</span>
            </div>
            <span className="text-xs text-slate-300 font-medium">
              {formatCompactINR(metrics.liquid_assets)} liquid
            </span>
          </div>

          <div className="relative h-5 w-full rounded-full bg-slate-800 overflow-hidden border border-slate-700">
            <div
              className={`h-full transition-all duration-700 rounded-full ${
                runwayMonths < 3
                  ? "bg-rose-500"
                  : runwayMonths < 6
                  ? "bg-amber-500"
                  : "bg-emerald-500"
              }`}
              style={{ width: `${runwayPct}%` }}
            />
            {/* 3m, 6m markers */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-rose-300/70"
              style={{ left: "25%" }}
              title="3 Months Critical Floor"
            />
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-emerald-300/80"
              style={{ left: "50%" }}
              title="6 Months Recommended Target"
            />
          </div>

          <div className="grid grid-cols-3 text-[11px] text-slate-400 pt-1">
            <div>
              <span className="text-rose-400 font-semibold">3m Floor:</span>{" "}
              {formatCompactINR(metrics.monthly_essential_burn * 3)}
            </div>
            <div className="text-center">
              <span className="text-emerald-400 font-semibold">6m Target:</span>{" "}
              {formatCompactINR(metrics.monthly_essential_burn * 6)}
            </div>
            <div className="text-right">
              <span className="text-blue-400 font-semibold">12m Fortress:</span>{" "}
              {formatCompactINR(metrics.monthly_essential_burn * 12)}
            </div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-800/80 flex justify-between text-xs">
          <span className="text-slate-400">6-Month Buffer Shortfall:</span>
          <span
            className={`font-semibold ${
              metrics.emergency_shortfall_inr > 0 ? "text-amber-300" : "text-emerald-400"
            }`}
          >
            {metrics.emergency_shortfall_inr > 0
              ? formatINR(metrics.emergency_shortfall_inr)
              : "Fully Funded"}
          </span>
        </div>
      </div>

      {/* 3. Liquidity vs Locked Donut Chart */}
      <div className="rounded-2xl bg-ink-900/90 border border-slate-800/80 p-5 shadow-xl flex flex-col justify-between">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-400">
            Asset Flexibility
          </span>
          <h3 className="text-base font-bold text-white mt-0.5 font-display">
            Liquidity vs. Locked Endowment Share
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Flags portfolios with &gt;40% trapped in low-yield LIC/endowment plans.
          </p>
        </div>

        <div className="h-52 mt-2 flex items-center">
          <ResponsiveContainer width="55%" height="100%">
            <PieChart>
              <Pie
                data={portfolioSlices}
                dataKey="value"
                nameKey="name"
                innerRadius={42}
                outerRadius={68}
                paddingAngle={3}
              >
                {portfolioSlices.map((s, idx) => (
                  <Cell key={idx} fill={s.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(val: number) => formatINR(val)}
                contentStyle={{
                  backgroundColor: "#0B132B",
                  borderColor: "#1E293B",
                  borderRadius: "10px",
                  color: "#F8FAFC",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="w-[45%] space-y-2 pl-2">
            {portfolioSlices.map((s) => (
              <div key={s.name} className="flex items-start gap-2 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-full mt-1 shrink-0"
                  style={{ backgroundColor: s.color }}
                />
                <div>
                  <div className="text-slate-300 font-medium leading-tight">{s.name}</div>
                  <div className="text-slate-400 text-[11px]">
                    {formatCompactINR(s.value)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-800/80 flex justify-between text-xs">
          <span className="text-slate-400">Locked LIC / Endowment Share:</span>
          <span
            className={`font-semibold ${
              metrics.locked_endowment_share_pct > 40
                ? "text-amber-400"
                : "text-emerald-400"
            }`}
          >
            {metrics.locked_endowment_share_pct.toFixed(1)}% (Limit: 40%)
          </span>
        </div>
      </div>
    </div>
  );
}
