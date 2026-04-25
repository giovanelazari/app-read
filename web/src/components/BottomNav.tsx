import { NavLink } from "react-router-dom";

const items = [
  { to: "/", label: "Hoje", icon: "☀" },
  { to: "/review", label: "Revisão", icon: "↻" },
  { to: "/library", label: "Biblioteca", icon: "📚" },
  { to: "/tags", label: "Tags", icon: "#" },
];

export default function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 inset-x-0 bg-ink-800/95 backdrop-blur border-t border-ink-700"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="max-w-2xl mx-auto grid grid-cols-4">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex flex-col items-center py-3 text-xs gap-0.5 ${
                isActive ? "text-amber-400" : "text-ink-400"
              }`
            }
          >
            <span className="text-lg leading-none">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
