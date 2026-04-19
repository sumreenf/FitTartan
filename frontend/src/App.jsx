import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import ChatInterface from "./components/ChatInterface.jsx";
import Home from "./components/Home.jsx";
import NutritionPage from "./components/NutritionPage.jsx";
import Onboarding from "./components/Onboarding.jsx";
import Profile from "./components/Profile.jsx";
import TrainingPage from "./components/TrainingPage.jsx";
import WeeklySummary from "./components/WeeklySummary.jsx";

function AppRoutes() {
  const location = useLocation();
  const [userId, setUserId] = useState(() => localStorage.getItem("fittartan_user_id"));

  useEffect(() => {
    setUserId(localStorage.getItem("fittartan_user_id"));
  }, [location.pathname]);

  const uid = userId ? Number(userId) : null;

  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-slate-900 antialiased">
      <div className="ft-ambient" aria-hidden />
      <div className="ft-ambient-dots" aria-hidden />
      <Routes>
        <Route path="/onboard" element={<Onboarding />} />
        <Route path="/" element={uid ? <Home userId={uid} /> : <Navigate to="/onboard" replace />} />
        <Route path="/nutrition" element={uid ? <NutritionPage userId={uid} /> : <Navigate to="/onboard" replace />} />
        <Route path="/training" element={uid ? <TrainingPage userId={uid} /> : <Navigate to="/onboard" replace />} />
        <Route path="/profile" element={uid ? <Profile userId={uid} /> : <Navigate to="/onboard" replace />} />
        <Route path="/chat" element={uid ? <ChatInterface userId={uid} /> : <Navigate to="/onboard" replace />} />
        <Route path="/weekly" element={uid ? <WeeklySummary userId={uid} /> : <Navigate to="/onboard" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return <AppRoutes />;
}
