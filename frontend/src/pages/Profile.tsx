import { useEffect, useState } from "react";
import { api, clearToken } from "../lib/api";
import { useNavigate } from "react-router-dom";
import { User2, Mail, Clock, LogOut } from "lucide-react";

type Me = {
  id?: number | string;
  username?: string;
  userName?: string;
  email?: string;
  last_login?: string;
  lastLogin?: string;
};

const ENDPOINTS = ["/users/api/me/"];

function fmtDateTime(iso?: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export default function Profile() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const navigate = useNavigate();  // 👈 navigation hook

  async function load() {
    setLoading(true);
    setErr(null);
    for (const ep of ENDPOINTS) {
      try {
        const data = await api(ep);
        setMe(data);
        setLoading(false);
        return;
      } catch {
        // try next
      }
    }
    setErr("Could not load profile from the API.");
    setLoading(false);
  }

  function logout() {
    clearToken();        // clear access + refresh
    navigate("/login");  // redirect
  }

  useEffect(() => {
    load();
  }, []);

  const username = me?.username ?? me?.userName ?? "—";
  const email = me?.email ?? "—";
  const lastLogin = fmtDateTime(me?.last_login ?? me?.lastLogin);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Profile</h1>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            Refresh
          </button>
          <button
            onClick={logout}
            className="inline-flex items-center gap-1 rounded-lg border border-rose-300 bg-rose-50 px-3 py-1.5 text-sm text-rose-700 hover:bg-rose-100"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </div>

      {/* Error */}
      {err && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700">
          {err}
        </div>
      )}

      {/* Card */}
      <div className="rounded-2xl bg-white/70 p-6 ring-1 ring-gray-200">
        {/* Avatar + name */}
        <div className="flex items-center gap-4">
          <div className="grid h-14 w-14 place-items-center rounded-full bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200">
            <User2 className="h-7 w-7" />
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {loading ? <span className="inline-block h-5 w-40 rounded bg-gray-200" /> : username}
            </div>
            <div className="text-sm text-gray-500">
              {loading ? <span className="inline-block h-3 w-28 rounded bg-gray-200" /> : "Account owner"}
            </div>
          </div>
        </div>

        {/* Fields */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field icon={<User2 className="h-4 w-4" />} label="User name" value={loading ? "…" : username} />
          <Field icon={<Mail className="h-4 w-4" />} label="Email" value={loading ? "…" : email} />
          <Field icon={<Clock className="h-4 w-4" />} label="Last login" value={loading ? "…" : lastLogin} />
        </div>
      </div>
    </div>
  );
}

function Field({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-1 text-[15px] font-medium text-gray-900">{value}</div>
    </div>
  );
}
