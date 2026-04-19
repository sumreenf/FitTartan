import React from "react";

export default function CookAtHomeCards({ options, onPick, disabled, pickedIndex }) {
  if (!options || options.length === 0) return null;

  return (
    <div className="mt-1 grid gap-3">
      {options.map((opt, idx) => {
        const ranges = opt.approx_macros_ranges || {};
        const totals = opt.totals || {};
        const isPicked = pickedIndex === idx;
        const totalUsd = opt.total_est_cost_usd ?? null;
        return (
          <button
            key={`${opt.title}-${idx}`}
            type="button"
            disabled={disabled}
            onClick={() => onPick?.(opt, idx)}
            className={`w-full rounded-2xl border text-left transition focus:outline-none focus:ring-2 focus:ring-emerald-600/30 ${
              isPicked
                ? "border-emerald-600 bg-emerald-50/80 shadow-md"
                : "border-slate-200 bg-white hover:border-emerald-500/40 hover:shadow-sm active:scale-[0.99]"
            } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
          >
            <div className="flex flex-col gap-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-emerald-800">
                    Budget cook {idx + 1}
                  </p>
                  <p className="text-sm font-semibold text-tartan-ink">{opt.title}</p>
                  {opt.subtitle ? <p className="text-xs text-slate-600">{opt.subtitle}</p> : null}
                </div>
                <div className="flex flex-col items-end gap-1">
                  {totalUsd != null ? (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-900">
                      ~${totalUsd.toFixed(2)} est.
                    </span>
                  ) : null}
                  <span className="text-[10px] text-slate-500">Tap to log meal</span>
                </div>
              </div>
              <ul className="space-y-1.5 text-sm text-slate-700">
                {(opt.ingredients || []).map((ing, i) => (
                  <li
                    key={i}
                    className="flex flex-wrap justify-between gap-x-2 gap-y-0.5 border-b border-slate-100 pb-1 last:border-0"
                  >
                    <span>
                      <span className="font-medium">{ing.item}</span>
                      {ing.qty ? <span className="text-slate-500"> — {ing.qty}</span> : null}
                    </span>
                    {ing.est_cost_usd != null ? (
                      <span className="shrink-0 text-xs text-slate-600">~${Number(ing.est_cost_usd).toFixed(2)}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
              {opt.budget_note ? <p className="text-[11px] text-slate-500">{opt.budget_note}</p> : null}
              <div className="flex flex-wrap gap-x-3 gap-y-1 border-t border-slate-100 pt-2 text-xs text-slate-600">
                <span>{ranges.calories ?? `~${totals.calories} kcal`}</span>
                <span>{ranges.protein}</span>
                <span>{ranges.carbs}</span>
                <span>{ranges.fat}</span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
