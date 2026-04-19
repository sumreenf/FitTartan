import React, { useState } from "react";
import CookAtHomeCards from "./CookAtHomeCards.jsx";
import MealComboCards from "./MealComboCards.jsx";

export default function MealOptionsPanel({
  combos,
  cookOptions,
  onPickCmu,
  onPickCook,
  cmuPickedIndex,
  cookPickedIndex,
  disabledCmu,
  disabledCook,
}) {
  const hasCmu = combos && combos.length > 0;
  const hasCook = cookOptions && cookOptions.length > 0;
  const [tab, setTab] = useState(hasCmu ? "cmu" : "cook");

  if (!hasCmu && !hasCook) return null;

  return (
    <div className="mt-3 w-full max-w-lg">
      <div className="flex rounded-xl bg-slate-100 p-1 text-xs font-medium">
        <button
          type="button"
          disabled={!hasCmu}
          onClick={() => setTab("cmu")}
          className={`flex-1 rounded-lg py-2 transition ${
            tab === "cmu" && hasCmu
              ? "bg-white text-tartan shadow-sm"
              : "text-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
          }`}
        >
          Eat at CMU
        </button>
        <button
          type="button"
          disabled={!hasCook}
          onClick={() => setTab("cook")}
          className={`flex-1 rounded-lg py-2 transition ${
            tab === "cook" && hasCook
              ? "bg-white text-emerald-800 shadow-sm"
              : "text-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
          }`}
        >
          Cook on your own (budget)
        </button>
      </div>
      {tab === "cmu" && hasCmu ? (
        <MealComboCards
          combos={combos}
          onPick={onPickCmu}
          pickedIndex={cmuPickedIndex}
          disabled={disabledCmu}
        />
      ) : null}
      {tab === "cook" && hasCook ? (
        <CookAtHomeCards
          options={cookOptions}
          onPick={onPickCook}
          pickedIndex={cookPickedIndex}
          disabled={disabledCook}
        />
      ) : null}
    </div>
  );
}
