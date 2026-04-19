/** Labels must match `gym_location` strings used in backend check-ins and `/crowd/{gym}`. */
export const CROWD_GYM_OPTIONS = [
  { value: "CUC Gym", label: "CUC Gym" },
  { value: "Tepper Gym", label: "Tepper Gym" },
  { value: "Swimming pool", label: "Swimming pool" },
];

export const DEFAULT_CROWD_GYM = "CUC Gym";

export function isCrowdGymLocation(value) {
  return CROWD_GYM_OPTIONS.some((o) => o.value === value);
}
