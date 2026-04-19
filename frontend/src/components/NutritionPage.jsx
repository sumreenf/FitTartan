import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import CalorieRing from "./CalorieRing.jsx";
import MainNav from "./MainNav.jsx";
import { getSummary } from "../api.js";

const MACRO_COLORS = ["#991b1b", "#166534", "#a16207", "#64748b"];

export default function NutritionPage({ userId }) {
  const [summary, setSummary] = useState(null);

  const load = useCallback(async () => {
    try {
      const s = await getSummary(userId);
      setSummary(s);
    } catch {
      setSummary(null);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const targets = summary?.targets || {};
  const daily = summary?.daily || {};
  const insights = summary?.insights || {};
  const eaten = summary?.today_consumed?.calories ?? 0;
  const dt = daily.targets || {};
  const da = daily.achieved || {};
  const rem = daily.remaining || {};
  const macroPie = summary?.macro_day_pie?.slices || [];
  const hints = summary?.nutrition_hints || {};
  const incomplete = summary?.profile_incomplete;
  const wz = summary?.workout_zones || {};

  return (
    <div className="ft-page">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tartan/75">Today</p>
          <h1 className="ft-h1 mt-0.5">Nutrition</h1>
          <p className="ft-muted mt-1">Targets, logging, and gentle guidance — not medical advice</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <MainNav />
          <button type="button" className="ft-btn-ghost text-xs" onClick={() => load()}>
            Refresh
          </button>
        </div>
      </header>

      {incomplete ? (
        <div className="rounded-2xl border border-amber-300/50 bg-gradient-to-r from-amber-50 to-orange-50/90 px-4 py-3 text-sm text-amber-950 shadow-soft ring-1 ring-amber-100/70">
          Add <strong>age</strong>, <strong>height</strong>, and <strong>sex</strong> in{" "}
          <Link className="ft-link" to="/profile">
            Profile
          </Link>{" "}
          for better BMR / TDEE estimates.
        </div>
      ) : null}

      {targets.bmr_estimate_kcal != null ? (
        <div className="ft-card">
          <h2 className="ft-h2">Energy outlook</h2>
          <p className="mt-1 text-xs text-slate-500">Mifflin–St Jeor × activity factor. Estimates only.</p>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            <div className="rounded-lg bg-slate-50 px-3 py-2">
              <dt className="text-xs text-slate-500">BMR</dt>
              <dd className="font-semibold text-slate-900">{Math.round(targets.bmr_estimate_kcal)} kcal</dd>
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2">
              <dt className="text-xs text-slate-500">Est. TDEE</dt>
              <dd className="font-semibold text-slate-900">{Math.round(targets.tdee_estimate_kcal)} kcal</dd>
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2">
              <dt className="text-xs text-slate-500">Day target</dt>
              <dd className="font-semibold text-tartan">{Math.round(targets.calories || 0)} kcal</dd>
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2">
              <dt className="text-xs text-slate-500">Logged today</dt>
              <dd className="font-semibold text-slate-900">{Math.round(da.calories || 0)} kcal</dd>
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2">
              <dt className="text-xs text-slate-500">Calories left</dt>
              <dd className="font-semibold text-emerald-800">{Math.round(rem.calories || 0)} kcal</dd>
            </div>
            <div className="rounded-lg bg-slate-50 px-3 py-2">
              <dt className="text-xs text-slate-500">Est. training kcal (7d)</dt>
              <dd className="font-semibold text-slate-900">{wz.est_workout_kcal_week ?? 0} kcal</dd>
            </div>
          </dl>
        </div>
      ) : null}

      <div className="ft-card">
        <h2 className="ft-h2 mb-2">Today — target vs logged</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="pb-2 font-medium">Macro</th>
                <th className="pb-2 font-medium">Target</th>
                <th className="pb-2 font-medium">Logged</th>
                <th className="pb-2 font-medium">Left</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Calories", dt.calories, da.calories, rem.calories],
                ["Protein (g)", dt.protein, da.protein, rem.protein],
                ["Carbs (g)", dt.carbs, da.carbs, rem.carbs],
                ["Fat (g)", dt.fat, da.fat, rem.fat],
              ].map(([label, t, a, r]) => (
                <tr key={label} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 font-medium text-slate-800">{label}</td>
                  <td className="py-2 text-slate-600">{t != null ? Number(t).toFixed(0) : "—"}</td>
                  <td className="py-2 font-medium text-tartan-ink">{a != null ? Number(a).toFixed(0) : "—"}</td>
                  <td className="py-2 text-slate-600">{r != null ? Math.max(0, Number(r)).toFixed(0) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(insights.done_well?.length > 0 || insights.needs_improvement?.length > 0) && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {insights.done_well?.length > 0 ? (
              <div>
                <p className="text-[10px] font-semibold uppercase text-emerald-800">Going well</p>
                <ul className="mt-1 list-inside list-disc text-xs text-emerald-950">
                  {insights.done_well.slice(0, 4).map((t, i) => (
                    <li key={i}>{t}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {insights.needs_improvement?.length > 0 ? (
              <div>
                <p className="text-[10px] font-semibold uppercase text-amber-900">Room to improve</p>
                <ul className="mt-1 list-inside list-disc text-xs text-amber-950">
                  {insights.needs_improvement.slice(0, 4).map((t, i) => (
                    <li key={i}>{t}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="ft-card">
          <h2 className="ft-h2 mb-2">Calories</h2>
          <CalorieRing eaten={eaten} target={targets.calories || 2400} />
          <p className="mt-2 text-xs text-slate-500">{targets.adjustment_reason || targets.macros_as_ranges?.calories}</p>
        </div>
        <div className="ft-card">
          <h2 className="ft-h2 mb-2">Today — calories from macros</h2>
          <p className="mb-2 text-xs text-slate-500">Protein & carbs ×4 kcal/g, fat ×9.</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie dataKey="value" data={macroPie} cx="50%" cy="50%" innerRadius={48} outerRadius={72} paddingAngle={2}>
                  {macroPie.map((_, i) => (
                    <Cell key={i} fill={MACRO_COLORS[i % MACRO_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [`${v} kcal`, ""]} />
                <Legend layout="horizontal" verticalAlign="bottom" height={28} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {(hints.eat_more?.length > 0 || hints.ease_off?.length > 0) && (
        <div className="grid gap-3 sm:grid-cols-2">
          {hints.eat_more?.length > 0 ? (
            <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-4 text-sm text-emerald-950">
              <p className="text-xs font-semibold uppercase text-emerald-900">Favor today</p>
              <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
                {hints.eat_more.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {hints.ease_off?.length > 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800">
              <p className="text-xs font-semibold uppercase text-slate-600">Ease off</p>
              <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
                {hints.ease_off.map((t, i) => (
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
