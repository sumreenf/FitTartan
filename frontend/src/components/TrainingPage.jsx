import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import CrowdMeter from "./CrowdMeter.jsx";
import MainNav from "./MainNav.jsx";
import {
  apiErrorMessage,
  deleteWorkout,
  getExerciseCatalog,
  getSummary,
  getWorkouts,
  logWorkout,
} from "../api.js";

const ZONE_COLORS = ["#991b1b", "#334155", "#0369a1", "#4338ca", "#6b21a8", "#0f766e", "#db2777"];

function lbsToKg(lbs) {
  return Number((Number(lbs) * 0.453592).toFixed(2));
}

function kgToLbs(kg) {
  return Math.round((Number(kg) / 0.453592) * 10) / 10;
}

export default function TrainingPage({ userId }) {
  const [summary, setSummary] = useState(null);
  const [workouts, setWorkouts] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [exerciseText, setExerciseText] = useState("");
  const [sets, setSets] = useState("");
  const [reps, setReps] = useState("");
  const [weightLbs, setWeightLbs] = useState("");
  const [loading, setLoading] = useState(false);
  const [workoutErr, setWorkoutErr] = useState("");
  const prevExerciseSig = useRef("");

  const loadData = useCallback(async () => {
    try {
      const [s, w] = await Promise.all([getSummary(userId), getWorkouts(userId, 80)]);
      setSummary(s);
      setWorkouts(w.workouts || []);
    } catch {
      setSummary(null);
      setWorkouts([]);
    }
  }, [userId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    getExerciseCatalog()
      .then((d) => setCatalog(d.exercises || []))
      .catch(() => setCatalog([]));
  }, []);

  const activeExerciseName = exerciseText.trim();
  const lastSame = useMemo(() => {
    if (!activeExerciseName) return null;
    const low = activeExerciseName.toLowerCase();
    return workouts.find((w) => (w.exercise || "").toLowerCase() === low) || null;
  }, [workouts, activeExerciseName]);

  useEffect(() => {
    if (!activeExerciseName) return;
    const sig = activeExerciseName.toLowerCase();
    if (lastSame) {
      setSets(String(lastSame.sets));
      setReps(String(lastSame.reps));
      setWeightLbs(
        lastSame.weight_kg != null && Number.isFinite(Number(lastSame.weight_kg))
          ? String(kgToLbs(lastSame.weight_kg))
          : ""
      );
      return;
    }
    if (prevExerciseSig.current !== sig) {
      prevExerciseSig.current = sig;
      setSets("");
      setReps("");
      setWeightLbs("");
    }
  }, [activeExerciseName, lastSame]);

  const weekly = summary?.weekly || {};
  const wz = summary?.workout_zones || {};
  const volPie = wz.volume_pie || [];

  const logSession = async () => {
    setWorkoutErr("");
    const ex = exerciseText.trim() || "Session";
    const sn = parseInt(String(sets).trim(), 10);
    const rn = parseInt(String(reps).trim(), 10);
    const snFinal = Number.isFinite(sn) && sn >= 1 && sn <= 50 ? sn : 1;
    const rnFinal = Number.isFinite(rn) && rn >= 1 && rn <= 200 ? rn : 1;
    const lbsTrim = String(weightLbs).trim();
    const lbs = lbsTrim === "" ? NaN : Number(weightLbs);
    const payload = {
      user_id: userId,
      exercise: ex,
      sets: snFinal,
      reps: rnFinal,
    };
    if (Number.isFinite(lbs) && lbs > 0) {
      payload.weight_kg = lbsToKg(lbs);
    }
    setLoading(true);
    try {
      await logWorkout(payload);
      await loadData();
    } catch (e) {
      setWorkoutErr(apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const removeWorkout = async (id) => {
    setWorkoutErr("");
    setLoading(true);
    try {
      await deleteWorkout(userId, id);
      await loadData();
    } catch (e) {
      setWorkoutErr(apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ft-page">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tartan/75">Move</p>
          <h1 className="ft-h1 mt-0.5">Training</h1>
          <p className="ft-muted mt-1">Log any activity — gym, cardio, or sport</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <MainNav />
          <button type="button" className="ft-btn-ghost text-xs" onClick={() => loadData()} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      <div className="ft-card">
        <h2 className="ft-h2 mb-2">This week — balance by zone</h2>
        <p className="mb-2 text-xs text-slate-500">
          Heuristic tags (strength + cardio). Last {wz.window_days ?? 7} days.
        </p>
        {wz.zones_not_trained_this_week?.length ? (
          <p className="mb-2 text-xs text-amber-900">
            <span className="font-semibold">Little or no volume yet:</span>{" "}
            {wz.zones_not_trained_this_week.map((z) => z.replace("_", " ")).join(", ")}
          </p>
        ) : (
          <p className="mb-2 text-xs text-emerald-800">Every zone has at least some logged work this week.</p>
        )}
        <div className="mb-2 flex flex-wrap gap-2 text-[11px]">
          {Object.entries(wz.zones_pct || {}).map(([z, p]) => (
            <span key={z} className="rounded-full border border-slate-200/70 bg-slate-50/90 px-2.5 py-0.5 text-[11px] capitalize text-slate-700 shadow-sm">
              {z}: {p}%
            </span>
          ))}
        </div>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie dataKey="value" data={volPie} cx="50%" cy="50%" innerRadius={44} outerRadius={72} paddingAngle={2}>
                {volPie.map((_, i) => (
                  <Cell key={i} fill={ZONE_COLORS[i % ZONE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend layout="horizontal" verticalAlign="bottom" height={28} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="ft-card">
        <h2 className="ft-h2 mb-2">Log a session</h2>
        <p className="text-xs text-slate-500">{weekly.auto_adjust_note || "Suggestions only — log what you actually did."}</p>
        <p className="mt-2 text-xs text-slate-600">
          <strong>All fields are optional.</strong> Leave blanks for defaults (1 set × 1 rep, no weight). For cardio, reps can
          mean minutes; add weight in lb only if you want load tracked.
        </p>
        <label className="mt-3 block text-xs font-medium text-slate-700">
          Exercise
          <input
            className="ft-input mt-1"
            list="ex-suggestions"
            value={exerciseText}
            onChange={(e) => setExerciseText(e.target.value)}
            placeholder="e.g. Swimming, Incline walk, Bench press…"
          />
          <datalist id="ex-suggestions">
            {catalog.map((e) => (
              <option key={e.name} value={e.name} />
            ))}
          </datalist>
        </label>
        {lastSame ? (
          <p className="mt-2 rounded-xl border border-slate-100/80 bg-slate-50/90 px-3 py-2 text-xs text-slate-700 shadow-inner">
            <span className="font-semibold text-tartan-ink">Last time:</span> {lastSame.sets}×{lastSame.reps}
            {lastSame.weight_kg != null && Number.isFinite(Number(lastSame.weight_kg)) ? (
              <>
                {" "}
                @ {kgToLbs(lastSame.weight_kg)} lb ({Number(lastSame.weight_kg).toFixed(1)} kg)
              </>
            ) : (
              <span className="text-slate-500"> (no weight logged)</span>
            )}{" "}
            on {lastSame.date}
          </p>
        ) : (
          <p className="mt-2 text-xs text-slate-500">No prior log under this exact name — enter honest numbers.</p>
        )}
        <div className="mt-3 grid grid-cols-3 gap-2">
          <label className="text-xs font-medium text-slate-700">
            Sets <span className="font-normal text-slate-400">(default 1)</span>
            <input
              type="number"
              min={1}
              max={50}
              className="ft-input mt-1 py-2"
              value={sets}
              onChange={(e) => setSets(e.target.value)}
              placeholder="1"
            />
          </label>
          <label className="text-xs font-medium text-slate-700">
            Reps (or min.) <span className="font-normal text-slate-400">(default 1)</span>
            <input
              type="number"
              min={1}
              max={200}
              className="ft-input mt-1 py-2"
              value={reps}
              onChange={(e) => setReps(e.target.value)}
              placeholder="1"
            />
          </label>
          <label className="text-xs font-medium text-slate-700">
            Weight (lb) <span className="font-normal text-slate-400">(optional)</span>
            <input
              type="number"
              min={1}
              className="ft-input mt-1 py-2"
              value={weightLbs}
              onChange={(e) => setWeightLbs(e.target.value)}
              placeholder="—"
            />
          </label>
        </div>
        {workoutErr ? <p className="mt-2 text-xs text-red-600">{workoutErr}</p> : null}
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" className="ft-btn-primary flex-1 py-3" onClick={logSession} disabled={loading}>
            Save session
          </button>
        </div>
      </div>

      <div className="ft-card">
        <h2 className="ft-h2 mb-3">Logged sessions</h2>
        <p className="mb-3 text-xs text-slate-500">Stored in kg; lb shown for convenience.</p>
        {workouts.length === 0 ? (
          <p className="text-sm text-slate-600">Nothing logged yet.</p>
        ) : (
          <ul className="max-h-96 space-y-2 overflow-y-auto text-sm">
            {workouts.map((w) => (
              <li
                key={w.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-100/90 bg-white/70 px-3 py-2 shadow-sm backdrop-blur-sm"
              >
                <div className="min-w-0 flex-1">
                  <span className="font-medium text-tartan-ink">{w.exercise}</span>
                  <span className="ml-2 text-xs text-slate-500">{w.date}</span>
                  <div className="text-xs text-slate-700">
                    {w.sets}×{w.reps}
                    {w.weight_kg != null && Number.isFinite(Number(w.weight_kg)) ? (
                      <>
                        {" "}
                        @ {kgToLbs(w.weight_kg)} lb ({Number(w.weight_kg).toFixed(1)} kg)
                      </>
                    ) : (
                      <span className="text-slate-500"> — no weight</span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  className="shrink-0 rounded-lg border border-red-200 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                  onClick={() => removeWorkout(w.id)}
                  disabled={loading}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <CrowdMeter />
    </div>
  );
}
