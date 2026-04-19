import React from "react";

export default function GymWindowCards({ gym, windows, basedOnCheckins }) {
  if (!windows || windows.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs text-slate-500">
        {gym ? `${gym} · ` : ""}
        based on {basedOnCheckins ?? 0} check-ins
      </p>
      <div className="grid gap-2 sm:grid-cols-1">
        {windows.map((w, i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm shadow-sm"
          >
            <p className="font-semibold text-tartan-ink">
              Window {i + 1}: {w.hour_start ?? "—"}:00 – {w.hour_end ?? "—"}:00
            </p>
            <p className="text-xs text-slate-600">
              {w.relative_busyness ?? "Usually quieter vs other hours"}
              {w.estimated_checkins_this_hour != null
                ? ` · ~${w.estimated_checkins_this_hour} check-ins this hour in history`
                : ""}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
