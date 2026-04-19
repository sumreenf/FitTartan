import { useEffect, useState } from "react";
import MainNav from "./MainNav.jsx";
import { apiErrorMessage, formatApiDetail, getUser, updateUser } from "../api.js";

function kgToLbs(kg) {
  if (kg == null || !Number.isFinite(Number(kg))) return "";
  return Math.round((Number(kg) / 0.453592) * 10) / 10;
}

export default function Profile({ userId }) {
  const [name, setName] = useState("");
  const [weightLbs, setWeightLbs] = useState("");
  const [goal, setGoal] = useState("maintain");
  const [activity, setActivity] = useState("moderate");
  const [diet, setDiet] = useState("");
  const [age, setAge] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [sex, setSex] = useState("other");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setErr("");
    setOk("");
    setLoading(true);
    (async () => {
      try {
        const u = await getUser(userId);
        if (cancelled) return;
        setName(u.name || "");
        setWeightLbs(String(kgToLbs(u.weight_kg)));
        setGoal(u.goal || "maintain");
        setActivity(u.activity_level || "moderate");
        setDiet(u.dietary_restrictions || "");
        setAge(u.age != null ? String(u.age) : "");
        setHeightCm(u.height_cm != null ? String(u.height_cm) : "");
        setSex(u.sex || "other");
      } catch (e) {
        if (!cancelled) setErr(formatApiDetail(e?.response?.data?.detail) || apiErrorMessage(e) || "Could not load profile");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const save = async () => {
    setErr("");
    setOk("");
    if (!name.trim()) {
      setErr("Name is required.");
      return;
    }
    const lbs = Number(weightLbs);
    if (!Number.isFinite(lbs) || lbs <= 40 || lbs >= 600) {
      setErr("Enter a current weight between 41 and 599 lbs.");
      return;
    }
    const ageN = age === "" ? null : Number(age);
    if (ageN != null && (!Number.isFinite(ageN) || ageN < 14 || ageN > 95)) {
      setErr("Age must be between 14 and 95, or leave blank.");
      return;
    }
    const hcm = heightCm === "" ? null : Number(heightCm);
    if (hcm != null && (!Number.isFinite(hcm) || hcm < 120 || hcm > 230)) {
      setErr("Height must be 120–230 cm, or leave blank.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        weight_lbs: lbs,
        goal,
        activity_level: activity,
        dietary_restrictions: diet.trim() ? diet.trim() : null,
        sex,
      };
      if (ageN != null) payload.age = ageN;
      if (hcm != null) payload.height_cm = hcm;
      await updateUser(userId, payload);
      setOk("Profile saved. Nutrition and Training pages use these settings.");
    } catch (e) {
      const d = e?.response?.data?.detail;
      setErr(formatApiDetail(d) || apiErrorMessage(e) || "Could not save profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="ft-page-narrow">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tartan/75">You</p>
          <h1 className="ft-h1 mt-0.5">Profile</h1>
          <p className="ft-muted mt-1">
            Weight, age, height, sex, goal, and activity drive BMR / TDEE and macro targets.
          </p>
        </div>
        <MainNav />
      </header>

      {loading ? (
        <p className="text-sm text-slate-600">Loading…</p>
      ) : (
        <div className="ft-card p-6">
          <div className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Name
              <input
                className="ft-input mt-1"
                value={name}
                onChange={(e) => setName(e.target.value)}
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
                className="ft-input mt-1"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="e.g. 22"
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
                placeholder="e.g. 170"
              />
            </label>
            <div>
              <div className="text-sm font-medium text-slate-700">Sex (for BMR)</div>
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
                placeholder="Leave blank if none"
              />
            </label>
          </div>
          {err && <p className="mt-3 text-sm text-red-600">{err}</p>}
          {ok && <p className="mt-3 text-sm text-emerald-800">{ok}</p>}
          <button type="button" className="ft-btn-primary mt-6 w-full py-3.5" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      )}
    </div>
  );
}
