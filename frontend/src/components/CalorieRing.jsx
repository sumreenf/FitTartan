import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const COLORS = ["#A6192E", "#e2e8f0"];

export default function CalorieRing({ eaten, target }) {
  const t = Math.max(target || 1, 1);
  const e = Math.min(Math.max(eaten || 0, 0), t * 2);
  const remaining = Math.max(t - e, 0);
  const data = [
    { name: "eaten", value: e },
    { name: "remaining", value: remaining },
  ];

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="h-44 w-full">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={52}
              outerRadius={72}
              startAngle={90}
              endAngle={-270}
              dataKey="value"
              stroke="none"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="text-center text-sm text-slate-600">
        <div className="text-lg font-semibold text-tartan-ink">
          ~{Math.round(e)} / ~{Math.round(t)} kcal
        </div>
        <div className="text-xs">Ranges avoid false precision</div>
      </div>
    </div>
  );
}
