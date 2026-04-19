import { useEffect, useRef, useState } from "react";
import MainNav from "./MainNav.jsx";
import { apiErrorMessage, chatAgent, logFood } from "../api.js";
import FormattedAssistantReply from "./FormattedAssistantReply.jsx";
import GymWindowCards from "./GymWindowCards.jsx";
import MealOptionsPanel from "./MealOptionsPanel.jsx";
import WeeklySummaryCards from "./WeeklySummaryCards.jsx";

/** Map /agent/chat JSON (snake_case) to message state for card UIs. */
function assistantMessageFromAgentReply(res) {
  const msg = { role: "assistant", content: res.reply || "" };
  const mc = res.meal_combos;
  const co = res.cook_options;
  if ((mc && mc.length) || (co && co.length)) {
    msg.mealCombos = mc || [];
    msg.cookOptions = co || [];
    msg.mealLoggedIdx = null;
    msg.cookLoggedIdx = null;
  }
  if (res.gym_windows && res.gym_windows.length) {
    msg.gymWindows = res.gym_windows;
    msg.gymMeta = {
      gym: res.gym_meta?.gym,
      basedOn: res.gym_meta?.basedOn,
    };
  }
  if (res.weekly_snapshot) {
    msg.weeklyPayload = res.weekly_snapshot;
  }
  return msg;
}

export default function ChatInterface({ userId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handlePickMeal = async (messageIndex, combo, comboIdx) => {
    const t = combo.totals;
    if (!t) return;
    setLoading(true);
    try {
      await logFood({
        user_id: userId,
        item_name: (combo.items || []).join(" + "),
        calories: t.calories,
        protein: t.protein,
        carbs: t.carbs,
        fat: t.fat,
      });
      setMessages((m) => {
        const copy = [...m];
        copy[messageIndex] = { ...copy[messageIndex], mealLoggedIdx: comboIdx };
        return [
          ...copy,
          {
            role: "assistant",
            content: "Logged CMU combo for today (estimates). Adjust if your portions differ.",
          },
        ];
      });
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: apiErrorMessage(e) }]);
    } finally {
      setLoading(false);
    }
  };

  const handlePickCook = async (messageIndex, opt, cookIdx) => {
    const t = opt.totals;
    if (!t) return;
    setLoading(true);
    try {
      await logFood({
        user_id: userId,
        item_name: `Cook: ${opt.title}`,
        calories: t.calories,
        protein: t.protein,
        carbs: t.carbs,
        fat: t.fat,
      });
      setMessages((m) => {
        const copy = [...m];
        copy[messageIndex] = { ...copy[messageIndex], cookLoggedIdx: cookIdx };
        return [
          ...copy,
          {
            role: "assistant",
            content:
              "Logged this cook-at-home plan using budget macro estimates. Update if your portions or ingredients differ.",
          },
        ];
      });
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: apiErrorMessage(e) }]);
    } finally {
      setLoading(false);
    }
  };

  const send = async (text) => {
    const t = text ?? input;
    if (!t.trim()) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: t }]);
    setLoading(true);
    try {
      const res = await chatAgent(userId, t);
      setMessages((m) => [...m, assistantMessageFromAgentReply(res)]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: apiErrorMessage(e) }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ft-page-chat">
      <header className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-slate-200/60 pb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tartan/75">Assistant</p>
          <span className="font-display text-lg font-semibold text-tartan-ink">FitTartan Chat</span>
        </div>
        <MainNav />
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {[
          ["Log workout", () => send("Log bench press 4x5 at 80 kg")],
          ["What should I eat?", () => send("What should I eat at CMU today?")],
          ["Gym timing?", () => send("When should I go to the gym today?")],
          ["Weekly summary", () => send("Give me my weekly summary")],
        ].map(([label, fn]) => (
          <button key={label} type="button" className="rounded-full border border-slate-200/80 bg-slate-50/90 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition hover:border-tartan/30 hover:bg-white" onClick={() => fn()}>
            {label}
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pb-32">
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "ml-auto max-w-[90%] text-right"
                : "mr-auto flex w-full max-w-[95%] flex-col gap-3 text-left"
            }
          >
            <div
              className={`inline-block max-w-full rounded-2xl text-left ${
                m.role === "user"
                  ? "bg-gradient-to-br from-tartan to-tartan-dark px-4 py-3 text-sm text-white shadow-md shadow-tartan/25"
                  : "border border-slate-200/70 bg-white/90 px-4 py-4 text-slate-800 shadow-soft ring-1 ring-white/80 backdrop-blur-sm"
              }`}
            >
              {m.role === "assistant" ? (
                <FormattedAssistantReply content={m.content} />
              ) : (
                <span className="text-sm">{m.content}</span>
              )}
            </div>
            {m.role === "assistant" && (m.mealCombos?.length || m.cookOptions?.length) ? (
              <MealOptionsPanel
                combos={m.mealCombos || []}
                cookOptions={m.cookOptions || []}
                cmuPickedIndex={m.mealLoggedIdx}
                cookPickedIndex={m.cookLoggedIdx}
                disabledCmu={loading || m.mealLoggedIdx != null}
                disabledCook={loading || m.cookLoggedIdx != null}
                onPickCmu={(combo, idx) => handlePickMeal(i, combo, idx)}
                onPickCook={(opt, idx) => handlePickCook(i, opt, idx)}
              />
            ) : null}
            {m.role === "assistant" && m.gymWindows?.length ? (
              <GymWindowCards
                gym={m.gymMeta?.gym}
                windows={m.gymWindows}
                basedOnCheckins={m.gymMeta?.basedOn}
              />
            ) : null}
            {m.role === "assistant" && m.weeklyPayload ? (
              <WeeklySummaryCards snapshot={m.weeklyPayload} />
            ) : null}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-20 border-t border-slate-200/60 bg-white/85 p-3 shadow-[0_-12px_40px_-12px_rgba(15,23,42,0.1)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-2xl gap-2">
          <input
            className="ft-input flex-1"
            placeholder="Ask FitTartan…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") send();
            }}
          />
          <button type="button" className="ft-btn-primary shrink-0 px-6" onClick={() => send()} disabled={loading}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
