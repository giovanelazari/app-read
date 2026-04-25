import { Link, Outlet, useLocation } from "react-router-dom";
import BottomNav from "./components/BottomNav";
import InstallPrompt from "./components/InstallPrompt";

export default function App() {
  const location = useLocation();
  return (
    <div className="min-h-full flex flex-col">
      <header className="sticky top-0 z-20 bg-ink-900/80 backdrop-blur border-b border-ink-800">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="font-serif text-lg font-semibold">
            Kindle Highlights
          </Link>
          <Link
            to="/settings"
            className={`text-sm ${
              location.pathname === "/settings" ? "text-amber-400" : "text-ink-400"
            } hover:text-amber-300`}
          >
            Configurações
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-4 pb-24">
        <InstallPrompt />
        <Outlet />
      </main>

      <BottomNav />
    </div>
  );
}
