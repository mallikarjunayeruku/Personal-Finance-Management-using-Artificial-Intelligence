// src/layouts/AppLayout.tsx
import { useEffect, useRef, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Bell, LogOut, User2 } from "lucide-react";
import Sidebar from "../components/Sidebar";
import { clearToken } from "../lib/api";

export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const btnRef = useRef<HTMLButtonElement | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!menuOpen) return;
      const t = e.target as Node;
      if (menuRef.current?.contains(t) || btnRef.current?.contains(t)) return;
      setMenuOpen(false);
    }
    function onEsc(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, [menuOpen]);

  const goProfile = () => {
    setMenuOpen(false);
    navigate("/profile");
  };

  const doLogout = () => {
    setMenuOpen(false);
    clearToken();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto grid grid-cols-[auto_1fr]">
        <Sidebar />
        <main className="relative">
          {/* Header (shared) */}
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white/80 px-6 py-3 backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="text-2xl font-extrabold italic">
                <span className="text-indigo-600">Fin</span>Track
              </div>
              <div className="text-lg text-gray-700">
                Hello, <span className="font-semibold">Test</span>
              </div>
            </div>

            <div className="relative flex items-center gap-3">
              <button
                className="grid h-10 w-10 place-items-center rounded-xl border border-gray-200 bg-white text-gray-600 hover:text-gray-900"
                aria-label="Notifications"
              >
                <Bell className="h-5 w-5" />
              </button>

              {/* Avatar trigger */}
              <button
                ref={btnRef}
                onClick={() => setMenuOpen((s) => !s)}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="rounded-full ring-2 ring-white focus:outline-none focus:ring-4 focus:ring-indigo-200"
                title="Account menu"
              >
                <img
                  alt="avatar"
                  className="h-10 w-10 rounded-full"
                  src="https://w0.peakpx.com/wallpaper/373/788/HD-wallpaper-zootopia-nick-cute-disney-fox-movie-zootropolis.jpg"
                />
              </button>

              {/* Popover menu */}
              {menuOpen && (
                <div
                  ref={menuRef}
                  role="menu"
                  aria-label="Account menu"
                  className="absolute right-0 top-12 z-50 w-48 overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-gray-200"
                >
                  <button
                    role="menuitem"
                    onClick={goProfile}
                    className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    <User2 className="h-4 w-4 text-gray-500" />
                    Profile
                  </button>
                  <div className="my-1 h-px bg-gray-100" />
                  <button
                    role="menuitem"
                    onClick={doLogout}
                    className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-rose-700 hover:bg-rose-50"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Page body */}
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
