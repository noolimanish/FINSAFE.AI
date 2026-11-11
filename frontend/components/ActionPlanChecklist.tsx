"use client";

import React from "react";
import { CheckCircle2, Circle, CalendarCheck } from "lucide-react";
import { Recommendation } from "@/lib/types";

interface ActionPlanChecklistProps {
  items: Recommendation[];
  onToggle: (id: number, nextState: boolean) => void;
}

export function ActionPlanChecklist({ items, onToggle }: ActionPlanChecklistProps) {
  const completedCount = items.filter((i) => i.is_completed).length;
  const progressPct = items.length > 0 ? Math.round((completedCount / items.length) * 100) : 0;

  return (
    <div className="rounded-2xl bg-ink-900/90 border border-slate-800/80 p-6 shadow-xl space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-400">
            <CalendarCheck className="w-4 h-4" />
            Prioritized Execution Roadmap
          </div>
          <h3 className="text-lg font-bold text-white mt-0.5 font-display">
            Your 30-Day Financial Security Action Plan
          </h3>
          <p className="text-xs text-slate-400">
            Ordered strictly by downside risk severity. Check off each milestone as you complete it.
          </p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2.5 flex items-center gap-3 shrink-0">
          <div className="text-right">
            <div className="text-xs text-slate-400">30-Day Progress</div>
            <div className="text-sm font-bold text-white">
              {completedCount} of {items.length} Completed ({progressPct}%)
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((item, idx) => {
          const id = item.id ?? idx + 1;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onToggle(id, !item.is_completed)}
              className={`text-left rounded-xl p-4 border transition-all flex items-start gap-3.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
                item.is_completed
                  ? "bg-emerald-950/20 border-emerald-500/30 opacity-80"
                  : "bg-slate-900/70 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {item.is_completed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-500" />
                )}
              </div>

              <div className="space-y-1.5 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-emerald-300">
                    {item.week_bucket}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Fixes Rule {item.rule_id}
                  </span>
                </div>
                <div
                  className={`font-semibold text-sm sm:text-base ${
                    item.is_completed ? "line-through text-slate-400" : "text-white"
                  }`}
                >
                  {item.title}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {item.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
