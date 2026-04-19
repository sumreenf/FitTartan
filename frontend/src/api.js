import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

/** Turn FastAPI `detail` (string, object, or validation list) into a single line for UI. */
export function formatApiDetail(detail) {
  if (detail == null) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (typeof e === "object" && e?.msg ? `${(e.loc || []).join(".")}: ${e.msg}` : String(e)))
      .join("; ");
  }
  return String(detail);
}

/** User-facing text when /agent or other API calls fail (common: API not running on :8000). */
export function apiErrorMessage(err) {
  const msg = err?.message || "";
  const code = err?.code;
  const fetchFailed =
    msg === "Failed to fetch" ||
    msg.includes("Load failed") ||
    msg.includes("NetworkError when attempting to fetch");
  const noResponse = axios.isAxiosError(err) && !err.response;
  if (noResponse || fetchFailed || code === "ERR_NETWORK" || msg === "Network Error") {
    return (
      "Cannot reach the FitTartan API (port 8000). Start the backend, then reload. " +
      "From fittartan/frontend run: npm run dev:all — or in another terminal: " +
      "cd fittartan/backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
    );
  }
  if (axios.isAxiosError(err) && err.response?.data?.detail) {
    const d = err.response.data.detail;
    return typeof d === "string" ? d : JSON.stringify(d);
  }
  return msg || "Request failed";
}

export async function onboardUser(payload) {
  const { data } = await api.post("/users/onboard", payload);
  return data;
}

export async function getUser(userId) {
  const { data } = await api.get(`/users/${userId}`);
  return data;
}

export async function updateUser(userId, payload) {
  const { data } = await api.patch(`/users/${userId}`, payload);
  return data;
}

export async function logWorkout(payload) {
  const { data } = await api.post("/logs/workout", payload);
  return data;
}

export async function getWorkouts(userId, limit = 50) {
  const { data } = await api.get("/logs/workouts/" + userId, { params: { limit } });
  return data;
}

export async function getExerciseCatalog() {
  const { data } = await api.get("/logs/exercises");
  return data;
}

export async function deleteWorkout(userId, workoutId) {
  const { data } = await api.delete(`/logs/workout/${workoutId}`, { params: { user_id: userId } });
  return data;
}

export async function logFood(payload) {
  const { data } = await api.post("/logs/food", payload);
  return data;
}

export async function logWeight(payload) {
  const { data } = await api.post("/logs/weight", payload);
  return data;
}

export async function postCheckin(payload) {
  const { data } = await api.post("/checkin", payload);
  return data;
}

export async function getCrowd(gym) {
  const { data } = await api.get(`/crowd/${encodeURIComponent(gym)}`);
  return data;
}

export async function chatAgent(userId, message) {
  const { data } = await api.post("/agent/chat", { user_id: userId, message, stream: false });
  return data;
}

export async function getSummary(userId) {
  const { data } = await api.get(`/summary/${userId}`);
  return data;
}

export async function getDailyMotivation(userId) {
  const { data } = await api.get("/motivation/daily", { params: { user_id: userId } });
  return data;
}

export async function getMenuToday() {
  const { data } = await api.get("/menu/today");
  return data;
}

export async function getMealSuggestions(userId) {
  const { data } = await api.get(`/meals/suggestions/${userId}`);
  return data;
}
