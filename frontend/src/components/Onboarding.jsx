import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiErrorMessage, formatApiDetail, onboardUser } from "../api.js";

export default function Onboarding() {
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [weightLbs, setWeightLbs] = useState(170);
  const [age, setAge] = useState(22);
  const [heightCm, setHeightCm] = useState(170);
  const [sex, setSex] = useState("other");
  const [goal, setGoal] = useState("maintain");
  const [activity, setActivity] = useState("moderate");
  const [diet, setDiet] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setErr("");
    if (!name.trim()) {
      setErr("Please enter your name to continue.");
      return;
    }
    const lbs = Number(weightLbs);
    if (!Number.isFinite(lbs) || lbs <= 40 || lbs >= 600) {
      setErr("Enter a current weight between 41 and 599 lbs.");
      return;
    }
    const ageN = Number(age);
    if (!Number.isFinite(ageN) || ageN < 14 || ageN > 95) {
      setErr("Enter a realistic age (14–95).");
      return;
    }
    const hcm = Number(heightCm);
    if (!Number.isFinite(hcm) || hcm < 120 || hcm > 230) {
      setErr("Enter height in cm between 120 and 230 (about 3′11″–7′7″).");
      return;
    }
    if (!sex) {
      setErr("Select sex at birth for BMR (used only for calorie estimates).");
      return;
    }
    setLoading(true);
    try {
      const res = await onboardUser({
        name: name.trim(),
        weight_lbs: lbs,
        age: ageN,
        height_cm: hcm,
        sex,
        goal,
        activity_level: activity,
        dietary_restrictions: diet || null,
      });
      localStorage.setItem("fittartan_user_id", String(res.user_id));
      nav("/");
    } catch (e) {
      const d = e?.response?.data?.detail;
      setErr(formatApiDetail(d) || apiErrorMessage(e) || "Could not save profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ft-page-narrow gap-8">
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/60 bg-gradient-to-br from-white/95 via-white/90 to-rose-50/40 p-6 shadow-soft ring-1 ring-white/80 backdrop-blur-md">
        <div className="pointer-events-none absolute -right-12 top-0 h-44 w-44 rounded-full bg-tartan/10 blur-3xl" />
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tartan/80">Welcome</p>
        <h1 className="ft-h1 relative mt-1">FitTartan</h1>
        <p className="ft-muted relative mt-2">CMU fitness + nutrition — quick setup, then you&apos;re in.</p>
      </div>

      <div className="ft-card p-6">
        <div className="space-y-4">
          <label className="block text-sm font-medium text-slate-700">
            Name
            <input
              className="ft-input mt-1"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alex"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Current weight (lbs)
            <input
              type="number"
              className="ft-input mt-1"
              value={weightLbs}
              onChange={(e) => setWeightLbs(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Age (years)
            <input
              type="number"
              min={14}
              max={95}
              className="ft-input mt-1"
              value={age}
              onChange={(e) => setAge(e.target.value)}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Height (cm)
            <input
              type="number"
              step="0.5"
              className="ft-input mt-1"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
            />
            <span className="mt-1 block text-xs text-slate-500">Example: 5′10″ ≈ 178 cm</span>
          </label>
          <div>
            <div className="text-sm font-medium text-slate-700">Sex (for BMR estimate)</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {[
                ["male", "Male"],
                ["female", "Female"],
                ["other", "Other / prefer not"],
              ].map(([v, label]) => (
                <button
                  key={v}
                  type="button"
                  className={`rounded-full px-3 py-1 text-sm ${
                    sex === v ? "bg-tartan text-white" : "bg-slate-100 text-slate-700"
                  }`}
                  onClick={() => setSex(v)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-slate-700">Goal</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {["cut", "bulk", "maintain"].map((g) => (
                <button
                  key={g}
                  type="button"
                  className={`rounded-full px-3 py-1 text-sm ${
                    goal === g ? "bg-tartan text-white" : "bg-slate-100 text-slate-700"
                  }`}
                  onClick={() => setGoal(g)}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-slate-700">Activity level</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {["sedentary", "light", "moderate", "active", "very_active"].map((a) => (
                <button
                  key={a}
                  type="button"
                  className={`rounded-full px-3 py-1 text-xs ${
                    activity === a ? "bg-tartan text-white" : "bg-slate-100 text-slate-700"
                  }`}
                  onClick={() => setActivity(a)}
                >
                  {a.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>
          <label className="block text-sm font-medium text-slate-700">
            Dietary restrictions
            <input
              className="ft-input mt-1"
              value={diet}
              onChange={(e) => setDiet(e.target.value)}
              placeholder="vegetarian, halal, allergies…"
            />
          </label>
        </div>
        {err && <p className="mt-3 text-sm text-red-600">{err}</p>}
        <button type="button" className="ft-btn-primary mt-6 w-full py-3.5" onClick={submit} disabled={loading}>
          {loading ? "Saving…" : "Continue"}
        </button>
        {!name.trim() && (
          <p className="mt-2 text-center text-xs text-slate-500">Add your name above, then tap Continue.</p>
        )}
      </div>
    </div>
  );
}
