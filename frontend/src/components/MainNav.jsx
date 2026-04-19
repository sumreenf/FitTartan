import { NavLink } from "react-router-dom";

const pill = ({ isActive }) =>
  [
    "rounded-full px-3 py-1.5 text-sm font-medium transition",
    isActive
      ? "bg-gradient-to-b from-tartan to-tartan-dark text-white shadow-md shadow-tartan/30"
      : "text-slate-600 hover:bg-white/90 hover:text-tartan-ink",
  ].join(" ");

export default function MainNav() {
  return (
    <nav className="flex max-w-[18rem] flex-col items-end gap-2 sm:max-w-none">
      <div className="ft-nav-shell">
        <NavLink className={pill} to="/" end>
          Home
        </NavLink>
        <NavLink className={pill} to="/nutrition">
          Nutrition
        </NavLink>
        <NavLink className={pill} to="/training">
          Training
        </NavLink>
        <NavLink className={pill} to="/profile">
          Profile
        </NavLink>
        <NavLink className={pill} to="/chat">
          Chat
        </NavLink>
        <NavLink className={pill} to="/weekly">
          Weekly
        </NavLink>
      </div>
    </nav>
  );
}
