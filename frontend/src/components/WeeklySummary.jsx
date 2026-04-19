import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import MainNav from "./MainNav.jsx";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getSummary } from "../api.js";

function StreakCard({ label, value, hint }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/70 bg-gradient-to-b from-white/95 to-slate-50/70 px-4 py-3 text-center shadow-soft ring-1 ring-white/70 backdrop-blur-sm">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-tartan/50 via-amber-400/40 to-emerald-500/40" />
      <p className="relative text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="relative mt-1 font-display text-3xl font-bold tabular-nums text-tartan-ink">{value}</p>
      {hint ? <p className="relative mt-1 text-[11px] leading-snug text-slate-500">{hint}</p> : null}
    </div>
  );
}

export default function WeeklySummary({ userId }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await getSummary(userId);
        if (!cancelled) setData(s);
      } catch {
        setData(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const weekly = data?.weekly || {};
  const targets = data?.targets || {};
  const wp = data?.weekly_progress || {};
  const insights = data?.insights || {};
  const weightSeries = data?.weight_series || [];

  const trend = useMemo(() => wp.daily_nutrition_trend || [], [wp.daily_nutrition_trend]);
  const tgtCal = Number(wp.target_calories || 0);

  const chartData = useMemo(
    () =>
      trend.map((d) => ({
        ...d,
        label: d.weekday,
        barCal: d.logged ? d.calories : 0,
        ghost: !d.logged,
      })),
    [trend]
  );

  const weightData = weightSeries.map((r) => ({
    day: r.date?.slice(5) || r.date,
    kg: r.kg,
  }));

  const logStreak = wp.logging_streak_days ?? 0;
  const hitStreak = wp.on_track_streak_days ?? 0;
  const trainStreak = wp.training_log_streak_days ?? 0;

  const avgCal = wp.avg_daily_calories;
  const calDeltaPct =
    tgtCal > 0 && avgCal != null ? Math.round(((avgCal - tgtCal) / tgtCal) * 1000) / 10 : null;

  return (
    <div className="ft-page">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tartan/75">Rhythm</p>
          <h1 className="ft-h1 mt-0.5">Weekly summary</h1>
          <p className="ft-muted mt-1">
            Last {wp.window_days ?? 7} days — trends & streaks (today&apos;s detail lives on{" "}
            <Link className="ft-link" to="/nutrition">
              Nutrition
            </Link>
            )
          </p>
        </div>
        <MainNav />
      </header>

      <div className="ft-card">
        <h2 className="ft-h2">Nutrition — week at a glance</h2>
        <p className="mt-1 text-xs text-slate-600">
          Bars are calories per day. <span className="text-emerald-700">Green</span> = within ±150 kcal of target and
          ~85%+ protein goal; <span className="text-amber-700">Amber</span> = logged but wider gap; gray = no food
          logged.
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <StreakCard
            label="On-track streak"
            value={hitStreak}
            hint="Consecutive days ending today: logged + calories ±150 + protein goal."
          />
          <StreakCard
            label="Logging streak"
            value={logStreak}
            hint="Consecutive days ending today with any food log."
          />
          <StreakCard
            label="Training streak"
            value={trainStreak}
            hint="Consecutive days ending today with a logged workout."
          />
        </div>

        {hitStreak === 0 && logStreak > 0 ? (
          <p className="mt-3 text-xs text-slate-600">
            You&apos;re logging steadily — tighten calories and protein to the targets above to grow your on-track
            streak.
          </p>
        ) : null}

        <div className="mt-4 h-56 w-full">
          {chartData.length === 0 ? (
            <p className="text-sm text-slate-600">Log meals to see your week-over-week calorie trend.</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={44} />
                {tgtCal > 0 ? <ReferenceLine y={tgtCal} stroke="#64748b" strokeDasharray="4 4" label={{ value: "Target", fill: "#64748b", fontSize: 10 }} /> : null}
                <Tooltip
                  formatter={(value, _name, item) => {
                    const p = item?.payload;
                    if (!p?.logged) return ["No food logged", "Calories"];
                    return [`${p.calories} kcal`, "Logged"];
                  }}
                  labelFormatter={(_, items) => {
                    const p = items?.[0]?.payload;
                    return p?.date ? String(p.date) : "";
                  }}
                />
                <Bar dataKey="barCal" radius={[6, 6, 0, 0]} maxBarSize={40}>
                  {chartData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.ghost ? "#e2e8f0" : entry.on_track ? "#059669" : "#d97706"}
                      fillOpacity={entry.ghost ? 1 : 0.9}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="mt-2 flex flex-wrap gap-2">
          {trend.map((d) => (
            <span
              key={d.date}
              title={d.date}
              className={`inline-flex h-8 min-w-[2.25rem] items-center justify-center rounded-lg text-[11px] font-medium ${
                !d.logged ? "bg-slate-200 text-slate-500" : d.on_track ? "bg-emerald-100 text-emerald-900" : "bg-amber-100 text-amber-950"
              }`}
            >
              {d.weekday?.slice(0, 1) ?? "—"}
            </span>
          ))}
        </div>

        <p className="mt-4 text-sm text-slate-700">
          Logged-day average:{" "}
          <span className="font-semibold text-tartan-ink">{avgCal != null ? `${avgCal} kcal` : "—"}</span>
          {tgtCal > 0 ? (
            <>
              {" "}
              vs <span className="font-semibold">{tgtCal} kcal</span> daily target
              {calDeltaPct != null ? (
                <span className="text-slate-600">
                  {" "}
                  ({calDeltaPct > 0 ? "+" : ""}
                  {calDeltaPct}%)
                </span>
              ) : null}
            </>
          ) : null}
          {targets.protein != null && wp.avg_daily_protein != null ? (
            <span className="block pt-1 text-xs text-slate-600">
              Protein avg: <strong>{wp.avg_daily_protein} g</strong> vs <strong>{wp.target_protein} g</strong> target
            </span>
          ) : null}
        </p>
        <p className="mt-2 text-xs text-slate-500">
          Averages use only days you logged food in the window ({wp.days_with_food_logs ?? 0} day
          {(wp.days_with_food_logs ?? 0) === 1 ? "" : "s"} with logs).
        </p>

        <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
          <div className="rounded-xl border border-slate-100/80 bg-slate-50/80 px-3 py-2 shadow-inner">
            <dt className="text-xs text-slate-500">Workout consistency (score)</dt>
            <dd className="font-semibold text-tartan-ink">
              {weekly.workout_consistency_score != null
                ? `${(weekly.workout_consistency_score * 100).toFixed(0)}%`
                : "—"}
            </dd>
          </div>
          <div className="rounded-xl border border-slate-100/80 bg-slate-50/80 px-3 py-2 shadow-inner">
            <dt className="text-xs text-slate-500">Macro adherence (week)</dt>
            <dd className="font-semibold text-tartan-ink">
              {weekly.macro_adherence_pct != null ? `${weekly.macro_adherence_pct}%` : "—"}
            </dd>
          </div>
          <div className="rounded-xl border border-slate-100/80 bg-slate-50/80 px-3 py-2 shadow-inner">
            <dt className="text-xs text-slate-500">Training days (window)</dt>
            <dd className="font-semibold text-tartan-ink">{wp.training_days ?? 0}</dd>
          </div>
          <div className="rounded-xl border border-slate-100/80 bg-slate-50/80 px-3 py-2 shadow-inner">
            <dt className="text-xs text-slate-500">Weight change (window)</dt>
            <dd className="font-semibold text-tartan-ink">
              {wp.weight_change_kg_in_window != null
                ? `${wp.weight_change_kg_in_window > 0 ? "+" : ""}${wp.weight_change_kg_in_window} kg`
                : "—"}
            </dd>
          </div>
        </dl>
      </div>

      <div className="ft-card">
        <h2 className="ft-h2 mb-2">Weight (last ~14 days)</h2>
        {weightData.length === 0 ? (
          <p className="text-sm text-slate-600">Log weight to see a trend line.</p>
        ) : (
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weightData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis domain={["dataMin - 0.5", "dataMax + 0.5"]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="kg" stroke="#A6192E" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-3xl border border-emerald-200/60 bg-gradient-to-br from-emerald-50/95 to-teal-50/35 p-4 shadow-soft ring-1 ring-emerald-100/50">
          <h2 className="font-display text-sm font-semibold text-emerald-900">What went well</h2>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-emerald-950">
            {(insights.done_well || []).length === 0 ? (
              <li className="list-none text-slate-600">Keep logging — we will highlight wins as patterns emerge.</li>
            ) : (
              insights.done_well.map((t, i) => <li key={i}>{t}</li>)
            )}
          </ul>
        </div>
        <div className="rounded-3xl border border-amber-200/60 bg-gradient-to-br from-amber-50/95 to-orange-50/35 p-4 shadow-soft ring-1 ring-amber-100/50">
          <h2 className="font-display text-sm font-semibold text-amber-950">What to improve</h2>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-amber-950">
            {(insights.needs_improvement || []).length === 0 ? (
              <li className="list-none text-slate-600">No major gaps flagged — stay consistent with logging.</li>
            ) : (
              insights.needs_improvement.map((t, i) => <li key={i}>{t}</li>)
            )}
          </ul>
        </div>
      </div>

      {weekly.auto_adjust_note ? (
        <div className="rounded-3xl border border-tartan/25 bg-gradient-to-br from-tartan/10 via-white/85 to-rose-50/40 p-4 shadow-soft ring-1 ring-tartan/10">
          <h2 className="font-display text-sm font-semibold text-tartan-ink">Adjustment note</h2>
          <p className="mt-2 text-sm text-slate-800">{weekly.auto_adjust_note}</p>
          <p className="mt-2 text-xs text-slate-600">
            Progressive overload events logged: {weekly.progressive_overload_events ?? 0}
          </p>
        </div>
      ) : null}
    </div>
  );
}
