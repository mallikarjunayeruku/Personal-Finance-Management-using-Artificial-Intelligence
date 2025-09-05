import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, setToken } from "../lib/api";

/**
 * Split screen login (Credit-Karma style)
 * - Left: form
 * - Right: promo/QR panel (hidden on small screens)
 * Tailwind required.
 */
export default function Login() {
  const nav = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const userRef = useRef<HTMLInputElement>(null);

  useEffect(() => userRef.current?.focus(), []);

  const canSubmit = useMemo(
    () => form.username.trim() && form.password && !loading,
    [form, loading]
  );

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!canSubmit) {
      setMsg("Enter email/username and password");
      return;
    }
    setLoading(true);
    setMsg(null);
    try {
      const data = await api("/token/", {
        method: "POST",
        body: JSON.stringify({
          username: form.username.trim(),
          password: form.password,
        }),
      }); // -> { access, refresh }
      setToken(data.access, data.refresh);
      nav("/dashboard");
    } catch (err: any) {
      setMsg(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white text-slate-900">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 md:grid-cols-2">
        {/* LEFT – FORM */}
        <section className="flex items-center px-6 py-10 sm:px-12 md:px-16">
          <div className="w-full max-w-[560px]">
            {/* Brand */}
            <div className="mb-10">
              <div className="text-3xl font-extrabold tracking-tight">
                <span>Log in to </span>
                <span className="text-slate-900">FinTrack</span>
              </div>
            </div>

            <form onSubmit={submit} className="space-y-5" noValidate>
              {/* Email / Username */}
              <div>
                <label
                  htmlFor="username"
                  className="mb-2 block text-[15px] font-semibold"
                >
                  Email
                </label>
                <div className="relative">
                  <input
                    id="username"
                    ref={userRef}
                    type="text"
                    autoComplete="username"
                    placeholder="you@example.com"
                    value={form.username}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, username: e.target.value }))
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-3 text-[15px] outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-emerald-200"
                  />
                  {/* Optional icon placeholder at right */}
                  <span className="pointer-events-none absolute inset-y-0 right-0 grid w-10 place-items-center text-slate-300">
                    ✉️
                  </span>
                </div>
              </div>

              {/* Password */}
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label
                    htmlFor="password"
                    className="text-[15px] font-semibold"
                  >
                    Password
                  </label>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    type={showPass ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    value={form.password}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, password: e.target.value }))
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-3 pr-14 text-[15px] outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-emerald-200"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass((s) => !s)}
                    className="absolute inset-y-0 right-0 grid w-14 place-items-center text-slate-600 hover:text-slate-900"
                  >
                    {showPass ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {/* Error */}
              {msg && (
                <div
                  role="alert"
                  className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
                >
                  {msg}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={!canSubmit}
                className="inline-flex w-full items-center justify-center rounded-lg bg-emerald-600 px-4 py-3 text-[16px] font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-60"
              >
                {loading ? "Logging in…" : "Log in"}
              </button>

              {/* Help */}
              <p className="text-sm text-slate-700">
                Can’t log in to your account?{" "}
                <a href="#" className="underline">
                  Try another way
                </a>
              </p>

              {/* Create account link (green) */}
              <p className="pt-4 text-center text-[16px] font-semibold text-emerald-700">
                <Link to="/register" className="hover:underline">
                  Create an account
                </Link>
              </p>
            </form>
          </div>
        </section>

        {/* RIGHT – PROMO / QR (hidden on small screens) */}
        <aside className="relative hidden items-center justify-center bg-[#FAD9E4] p-8 md:flex">
          <div className="absolute left-[-80px] top-1/4 hidden h-80 w-80 rounded-full bg-[#1E73E8] md:block" />
          <div className="relative z-10 flex max-w-md flex-col items-center text-center">
            {/* Phone mockup with QR */}
            <div className="mb-8 w-[280px] rounded-3xl border-[10px] border-slate-900/80 bg-white p-4 shadow-xl">
              <div className="aspect-[9/16] w-full rounded-2xl bg-white p-6 ring-1 ring-slate-200">
                <div className="grid h-full place-items-center rounded-xl border border-slate-200 p-4">
                  {/* Replace src with your real QR image if you have one */}
                  <img
                    src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https://example.com/app"
                    alt="Scan to get the app"
                    className="h-[180px] w-[180px]"
                  />
                </div>
              </div>
            </div>

            <h2 className="mb-2 text-3xl font-extrabold tracking-tight text-slate-900">
              Create your own karma.
            </h2>
            <p className="max-w-sm text-[15px] text-slate-700">
              Download our app to see what’s new.
            </p>
          </div>

          {/* Decorative star glyphs */}
          <div className="pointer-events-none absolute right-10 top-10 h-10 w-10 rotate-12 border-2 border-slate-900" />
          <div className="pointer-events-none absolute bottom-16 right-24 h-10 w-10 -rotate-12 border-2 border-slate-900" />
        </aside>
      </div>
    </main>
  );
}
