"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { Finding } from "@/lib/types";
import { formatCompactINR } from "@/lib/api";

interface FindingsListProps {
  findings: Finding[];
}

export function FindingsList({ findings }: FindingsListProps) {
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({
    R1: true,
    R2: true,
  });

  const toggle = (id: string) => {
    setExpandedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="rounded-2xl bg-ink-900/90 border border-slate-800/80 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white font-display">
            5-Pillar Vulnerability Findings
          </h3>
          <p className="text-xs text-slate-400">
            Every rupee figure is computed deterministically; expand any card for plain-English guidance.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {findings.map((f) => {
          const isOpen = !!expandedIds[f.rule_id];
          const isCrit = f.severity === "critical";
          const isWarn = f.severity === "warning";

          const borderClass = isCrit
            ? "border-rose-500/35 bg-rose-950/15"
            : isWarn
            ? "border-amber-500/35 bg-amber-950/15"
            : "border-emerald-500/30 bg-emerald-950/10";

          const badgeClass = isCrit
            ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
            : isWarn
            ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
            : "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";

          return (
            <div
              key={f.rule_id}
              className={`rounded-xl border transition-colors ${borderClass}`}
            >
              <button
                type="button"
                onClick={() => toggle(f.rule_id)}
                aria-expanded={isOpen}
                className="w-full p-4 text-left flex flex-col sm:flex-row sm:items-center justify-between gap-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded-xl"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 shrink-0">
                    {isCrit ? (
                      <AlertOctagon className="w-5 h-5 text-rose-400" />
                    ) : isWarn ? (
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono uppercase text-slate-400">
                        {f.rule_id}
                      </span>
                      <span className="font-semibold text-white text-sm sm:text-base">
                        {f.title}
                      </span>
                      <span
                        className={`text-[11px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full border ${badgeClass}`}
                      >
                        {f.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                      {f.deterministic_message}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800/70">
                  <div className="text-left sm:text-right">
                    <div className="text-[11px] text-slate-400">Current vs Target</div>
                    <div className="text-xs font-semibold text-slate-200">
                      {f.current_value_label}{" "}
                      <span className="text-slate-500">→</span> {f.target_value_label}
                    </div>
                    {f.gap_inr > 0 && (
                      <div className="text-[11px] font-medium text-rose-300">
                        Gap: {formatCompactINR(f.gap_inr)}
                      </div>
                    )}
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </div>
              </button>

              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 pt-1 border-t border-slate-800/60">
                      <div className="rounded-lg bg-slate-900/90 p-3.5 border border-slate-800 flex items-start gap-2.5">
                        <Sparkles className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <div className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                          <span className="font-semibold text-emerald-300">
                            Why this matters:{" "}
                          </span>
                          {f.plain_explanation}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}
