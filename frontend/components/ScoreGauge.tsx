"use client";

import React from "react";
import { motion } from "framer-motion";
import { ShieldAlert, ShieldCheck, ShieldHalf, Sparkles } from "lucide-react";

interface ScoreGaugeProps {
  score: number;
  band: string;
  alias: string;
  llmUsed: boolean;
  criticalCount: number;
  warningCount: number;
}

export function ScoreGauge({
  score,
  band,
  alias,
  llmUsed,
  criticalCount,
  warningCount,
}: ScoreGaugeProps) {
  const radius = 76;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const strokeDashoffset = circumference - (clamped / 100) * circumference;

  const isSafe = clamped >= 75;
  const isWarning = clamped >= 50 && clamped < 75;

  const strokeColor = isSafe
    ? "#10B981"
    : isWarning
    ? "#F59E0B"
    : "#F43F5E";

  const badgeStyles = isSafe
    ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
    : isWarning
    ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
    : "bg-rose-500/15 text-rose-300 border-rose-500/30";

  return (
    <div className="rounded-2xl bg-ink-900/90 border border-slate-800/80 p-6 shadow-xl backdrop-blur-md flex flex-col md:flex-row items-center justify-between gap-6">
      <div className="flex flex-col sm:flex-row items-center gap-6">
        <div
          className="relative w-44 h-44 flex items-center justify-center shrink-0"
          role="meter"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Financial Security Score: ${clamped} out of 100`}
        >
          <svg className="w-full h-full -rotate-90" viewBox="0 0 180 180">
            <circle
              cx="90"
              cy="90"
              r={radius}
              stroke="rgba(148, 163, 184, 0.14)"
              strokeWidth="14"
              fill="transparent"
            />
            <motion.circle
              cx="90"
              cy="90"
              r={radius}
              stroke={strokeColor}
              strokeWidth="14"
              strokeLinecap="round"
              fill="transparent"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-bold tracking-tight text-white font-display">
              {clamped}
            </span>
            <span className="text-xs uppercase tracking-widest text-slate-400 mt-0.5">
              / 100 Score
            </span>
          </div>
        </div>

        <div className="space-y-2.5 text-center sm:text-left">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${badgeStyles}`}
            >
              {isSafe ? (
                <ShieldCheck className="w-3.5 h-3.5" />
              ) : isWarning ? (
                <ShieldHalf className="w-3.5 h-3.5" />
              ) : (
                <ShieldAlert className="w-3.5 h-3.5" />
              )}
              {band} Posture
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800/90 text-slate-300 border border-slate-700">
              <Sparkles className="w-3 h-3 text-emerald-400" />
              {llmUsed ? "AI Narrative Active" : "Deterministic Narrative Engine"}
            </span>
          </div>

          <h2 className="text-2xl font-bold text-white font-display">
            Financial Security Audit for {alias}
          </h2>
          <p className="text-sm text-slate-300 max-w-xl leading-relaxed">
            {criticalCount > 0
              ? `Your snapshot flagged ${criticalCount} critical exposure(s) and ${warningCount} warning(s). Address your standalone health cover and liquid buffer first before adding new locked investments.`
              : warningCount > 0
              ? `You have zero critical survival gaps, with ${warningCount} optimization warning(s) to strengthen long-term compounding and disability protection.`
              : `All 5 core financial security pillars meet recommended Indian stress-test benchmarks.`}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 w-full md:w-auto shrink-0 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6">
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-rose-400">{criticalCount}</div>
          <div className="text-xs text-rose-200/80">Critical</div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-amber-400">{warningCount}</div>
          <div className="text-xs text-amber-200/80">Warnings</div>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-emerald-400">
            {5 - criticalCount - warningCount}
          </div>
          <div className="text-xs text-emerald-200/80">Healthy</div>
        </div>
      </div>
    </div>
  );
}
