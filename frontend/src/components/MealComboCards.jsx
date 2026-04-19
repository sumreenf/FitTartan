import React from "react";

const LABELS = ["Light & balanced", "Hearty & filling", "Protein-forward"];

export default function MealComboCards({ combos, onPick, disabled, pickedIndex }) {
  if (!combos || combos.length === 0) return null;

  return (
    <div className="mt-3 grid gap-3 sm:grid-cols-1">
      {combos.map((combo, idx) => {
        const ranges = combo.approx_macros_ranges || {};
        const totals = combo.totals || {};
        const isPicked = pickedIndex === idx;
        return (
          <button
            key={`${combo.items?.join("|")}-${idx}`}
            type="button"
            disabled={disabled}
            onClick={() => onPick?.(combo, idx)}
            className={`w-full rounded-2xl border text-left transition focus:outline-none focus:ring-2 focus:ring-tartan/40 ${
              isPicked
                ? "border-tartan bg-tartan/5 shadow-md"
                : "border-slate-200 bg-white hover:border-tartan/40 hover:shadow-sm active:scale-[0.99]"
            } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
          >
            <div className="flex flex-col gap-2 p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-tartan/90">
                    Option {idx + 1}
                  </p>
                  <p className="text-sm font-semibold text-tartan-ink">{LABELS[idx] ?? "Meal combo"}</p>
                </div>
                <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">
                  Tap to log
                </span>
              </div>
              <ul className="list-inside list-disc space-y-0.5 text-sm text-slate-700">
                {(combo.items || []).map((name, i) => (
                  <li key={i}>
                    <span className="font-medium">{name}</span>
                    {combo.cafes?.[i] ? (
                      <span className="text-slate-500"> — {combo.cafes[i]}</span>
                    ) : null}
                    {combo.meal_periods?.[i] ? (
                      <span className="text-xs text-slate-400"> ({combo.meal_periods[i]})</span>
                    ) : null}
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap gap-x-3 gap-y-1 border-t border-slate-100 pt-2 text-xs text-slate-600">
                <span>{ranges.calories ?? `~${totals.calories} kcal`}</span>
                <span>{ranges.protein ?? `protein ~${totals.protein}g`}</span>
                <span>{ranges.carbs ?? `carbs ~${totals.carbs}g`}</span>
                <span>{ranges.fat ?? `fat ~${totals.fat}g`}</span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
