/** Backend `training_split` values + display labels. */
export const TRAINING_SPLIT_OPTIONS = [
  { value: "none", label: "No set split", hint: "Log by feel or schedule." },
  { value: "full_body", label: "Full body", hint: "Most major patterns each session." },
  { value: "push_pull_legs", label: "Push / Pull / Legs", hint: "3-day rotation; repeat through the week." },
  { value: "upper_lower", label: "Upper / Lower", hint: "Alternate upper- and lower-body days." },
  { value: "bro_split", label: "Bro split", hint: "One main muscle focus per day." },
  { value: "arnold", label: "Arnold split", hint: "Chest-back, shoulders-arms, legs rotation." },
  { value: "phul", label: "PHUL", hint: "Power + hypertrophy upper/lower blend." },
];

export function labelForSplit(value) {
  return TRAINING_SPLIT_OPTIONS.find((o) => o.value === value)?.label || value || "Not set";
}
