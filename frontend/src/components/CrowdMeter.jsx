import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getCrowd } from "../api.js";
import { CROWD_GYM_OPTIONS, DEFAULT_CROWD_GYM, isCrowdGymLocation } from "../gymLocations.js";

function locationPillClass(active) {
  return [
    "rounded-full px-3 py-1.5 text-xs font-medium transition sm:text-sm",
    active
      ? "bg-gradient-to-b from-tartan to-tartan-dark text-white shadow-md shadow-tartan/30"
      : "border border-slate-200/80 bg-white/80 text-slate-600 hover:border-tartan/30 hover:text-tartan-ink",
  ].join(" ");
}

/**
 * @param {{ initialGym?: string }} [props] — optional initial location (must be a known crowd location)
 */
export default function CrowdMeter({ initialGym } = {}) {
  const [gym, setGym] = useState(() =>
    initialGym && isCrowdGymLocation(initialGym) ? initialGym : DEFAULT_CROWD_GYM,
  );
  const [rows, setRows] = useState([]);
  const [n, setN] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await getCrowd(gym);
        if (cancelled) return;
        const hours = Array.from({ length: 24 }, (_, h) => ({ hour: h, score: 0 }));
        (d.quiet_windows || []).forEach((w) => {
          const h = w.hour_start ?? 0;
          if (h >= 0 && h < 24) hours[h].score = 1;
        });
        setRows(hours);
        setN(d.based_on_checkins ?? 0);
      } catch {
        setRows([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [gym]);

  return (
    <div className="ft-card">
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <h3 className="ft-h2">Gym crowd</h3>
        <span className="shrink-0 text-xs text-slate-500 sm:text-right">based on {n} check-ins</span>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        {CROWD_GYM_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className={locationPillClass(gym === opt.value)}
            onClick={() => setGym(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <div className="h-48 w-full">
        <ResponsiveContainer>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
            <YAxis hide />
            <Tooltip />
            <Bar dataKey="score" fill="#A6192E" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        Highlights quieter hour windows from check-in history for {gym}; cold start uses gentle heuristics.
      </p>
    </div>
  );
}
