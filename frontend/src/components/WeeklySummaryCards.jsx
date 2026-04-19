import React from "react";

function Row({ label, target, achieved }) {
  const t = target != null && !Number.isNaN(Number(target)) ? Number(target) : null;
  const a = achieved != null && !Number.isNaN(Number(achieved)) ? Number(achieved) : null;
  return (
    <tr className="border-b border-slate-100 text-xs last:border-0">
      <td className="py-1.5 pr-2 font-medium text-slate-700">{label}</td>
      <td className="py-1.5 text-right text-slate-600">{t != null ? t.toFixed(0) : "—"}</td>
      <td className="py-1.5 text-right text-tartan-ink">{a != null ? a.toFixed(0) : "—"}</td>
    </tr>
  );
}

export default function WeeklySummaryCards({ snapshot }) {
  if (!snapshot || snapshot.error) return null;

  const weekly = snapshot.weekly || {};
  const daily = snapshot.daily || {};
  const wp = snapshot.weekly_progress || {};
  const ins = snapshot.insights || {};
  const done = ins.done_well || [];
  const improve = ins.needs_improvement || [];

  const dt = daily.targets || {};
  const da = daily.achieved || {};

  return (
    <div className="mt-3 space-y-3">
      {weekly.auto_adjust_note ? (
        <div className="rounded-xl border border-tartan/20 bg-tartan/5 px-3 py-2 text-xs text-slate-800">
          {weekly.auto_adjust_note}
        </div>
      ) : null}

      <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-tartan/90">Today — target vs logged</p>
        <table className="mt-2 w-full border-collapse">
          <thead>
            <tr className="text-[10px] uppercase text-slate-500">
              <th className="pb-1 text-left font-medium">Macro</th>
              <th className="pb-1 text-right font-medium">Target</th>
              <th className="pb-1 text-right font-medium">Logged</th>
            </tr>
          </thead>
          <tbody>
            <Row label="Calories" target={dt.calories} achieved={da.calories} />
            <Row label="Protein (g)" target={dt.protein} achieved={da.protein} />
            <Row label="Carbs (g)" target={dt.carbs} achieved={da.carbs} />
            <Row label="Fat (g)" target={dt.fat} achieved={da.fat} />
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-tartan/90">This week (7 days)</p>
        <ul className="mt-2 space-y-1">
          <li>
            Avg calories: <strong>{wp.avg_daily_calories ?? "—"}</strong> vs target ~{wp.target_calories ?? "—"} / day
          </li>
          <li>
            Avg protein: <strong>{wp.avg_daily_protein ?? "—"}</strong> g vs ~{wp.target_protein ?? "—"} g / day
          </li>
          <li>
            Training days logged: <strong>{wp.training_days ?? 0}</strong> · days near calorie target:{" "}
            <strong>{wp.days_near_calorie_target ?? 0}</strong>
          </li>
        </ul>
      </div>

      {(done.length > 0 || improve.length > 0) && (
        <div className="grid gap-2 sm:grid-cols-2">
          {done.length > 0 ? (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 px-3 py-2">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-800">Going well</p>
              <ul className="mt-1 list-inside list-disc space-y-0.5 text-[11px] text-emerald-900">
                {done.slice(0, 4).map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {improve.length > 0 ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-3 py-2">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-900">Room to improve</p>
              <ul className="mt-1 list-inside list-disc space-y-0.5 text-[11px] text-amber-950">
                {improve.slice(0, 4).map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
