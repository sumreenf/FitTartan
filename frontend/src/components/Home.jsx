import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FormattedAssistantReply from "./FormattedAssistantReply.jsx";
import MainNav from "./MainNav.jsx";
import { apiErrorMessage, chatAgent, getDailyMotivation, getUser } from "../api.js";

const tiles = [
  { to: "/nutrition", title: "Nutrition", emoji: "🥗", blurb: "Targets, macros, calories left, food nudges.", tint: "from-emerald-400/25" },
  { to: "/training", title: "Training", emoji: "🏋️", blurb: "Log any activity, weekly balance, crowd timing.", tint: "from-sky-400/20" },
  { to: "/chat", title: "Chat", emoji: "💬", blurb: "Meals, workouts, quiet gym windows.", tint: "from-violet-400/20" },
  { to: "/weekly", title: "Weekly", emoji: "📈", blurb: "Streaks, trends, and charts.", tint: "from-amber-400/25" },
];

export default function Home({ userId }) {
  const [motivation, setMotivation] = useState(null);
  const [incomplete, setIncomplete] = useState(false);
  const [quick, setQuick] = useState("");
  const [quickReply, setQuickReply] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [m, u] = await Promise.all([getDailyMotivation(userId), getUser(userId)]);
        if (!cancelled) {
          setMotivation(m?.message || "");
          setIncomplete(!u?.age || u?.height_cm == null || !u?.sex);
        }
      } catch {
        if (!cancelled) {
          setMotivation("");
          setIncomplete(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const askQuick = async () => {
    if (!quick.trim()) return;
    setLoading(true);
    setQuickReply("");
    try {
      const res = await chatAgent(userId, quick);
      setQuickReply(res.reply);
    } catch (e) {
      setQuickReply(apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ft-page animate-fade-up pb-40">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tartan/80">FitTartan</p>
          <h1 className="ft-h1 mt-1">One place for training and nutrition</h1>
          <p className="ft-muted mt-2 max-w-md">Tuned for a healthy life on campus.</p>
        </div>
        <MainNav />
      </header>

      {motivation ? (
        <section className="animate-fade-up-delay relative overflow-hidden rounded-3xl border border-amber-200/45 bg-gradient-to-br from-amber-50/95 via-white/95 to-rose-50/50 p-6 shadow-soft ring-1 ring-white/90 backdrop-blur-md">
          <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-tartan/10 blur-3xl" />
          <div className="pointer-events-none absolute bottom-0 left-1/3 h-32 w-48 rounded-full bg-amber-200/30 blur-3xl" />
          <p className="relative text-[11px] font-semibold uppercase tracking-wide text-tartan">Daily spark</p>
          <p className="relative mt-2 font-display text-xl font-semibold leading-snug text-tartan-ink sm:text-2xl">
            {motivation}
          </p>
        </section>
      ) : null}

      {incomplete ? (
        <div className="rounded-2xl border border-amber-300/50 bg-gradient-to-r from-amber-50 to-orange-50/90 px-4 py-3 text-sm text-amber-950 shadow-soft ring-1 ring-amber-100/70">
          Add <strong>age</strong>, <strong>height</strong>, and <strong>sex</strong> in{" "}
          <Link className="ft-link" to="/profile">
            Profile
          </Link>{" "}
          so targets match you better.
        </div>
      ) : null}

      <section className="animate-fade-up-delay">
        <div className="mb-4 flex items-end justify-between gap-2">
          <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-slate-500">Jump in</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {tiles.map((t) => (
            <Link key={t.to} to={t.to} className="group ft-tile">
              <div className={`ft-tile-glow bg-gradient-to-br ${t.tint} to-transparent`} />
              <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${t.tint} to-transparent opacity-60`} />
              <div className="relative flex items-start gap-3">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/90 text-2xl shadow-inner ring-1 ring-slate-200/50">
                  {t.emoji}
                </span>
                <div className="min-w-0">
                  <h3 className="font-display text-lg font-semibold text-tartan-ink transition group-hover:text-tartan">
                    {t.title}
                  </h3>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">{t.blurb}</p>
                  <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-tartan opacity-0 transition group-hover:opacity-100">
                    Open →
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {quickReply ? (
        <div className="ft-card animate-fade-up">
          <FormattedAssistantReply content={quickReply} />
        </div>
      ) : null}

      <div className="fixed bottom-0 left-0 right-0 z-20 border-t border-slate-200/60 bg-white/85 p-3 shadow-[0_-12px_40px_-12px_rgba(15,23,42,0.1)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl gap-2">
          <input
            className="ft-input flex-1"
            placeholder="Quick ask FitTartan…"
            value={quick}
            onChange={(e) => setQuick(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") askQuick();
            }}
          />
          <button type="button" className="ft-btn-primary shrink-0 px-5" onClick={askQuick} disabled={loading}>
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}
