import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Home, Grid2X2, Clock, Wallet, Calendar, Lightbulb, User2, Bell, TrendingDown, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from "recharts";
import {api} from "../lib/api.ts";
import Sidebar from "./Sidebar.tsx";

/**
 * FinTrackDashboard (data-driven)
 * - Reads JWT from localStorage("lp_token")
 * - Fetches from a Django/DRF backend (defaults to `/api`)
 * - Props allow overriding data or supplying your own fetcher
 */
export default function FinTrackDashboard({
  userName = "jon_snow",
  apiBase = "/api",
  token = typeof window !== "undefined" ? localStorage.getItem("lp_token") : "",
  // Optional: allow passing pre-fetched data
  initial,
}: {
  userName?: string;
  apiBase?: string;
  token?: string | null;
  initial?: Partial<DashboardData>;
}) {
  const [data, setData] = useState<DashboardData | null>(initial as DashboardData || null);
  const [loading, setLoading] = useState(!initial);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<"month" | "year">("month");
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [accForm, setAccForm] = useState({
    accountName: "Primary Checking",
    officialAccountName: "Chase Total Checking",
    accountType: "checking",
    subAccountType: "DEMAND_DEPOSIT",
    accountNumber: "****4321",
    accountId: "ext_abc_123",
    isoCurrencyCode: "USD",
    availableBalance: 1725.0,
    currentBalance: 1800.0,
    limit: 0,
    loans: 0,
    depts: 0,
    isInternalAccount: true,
    icon: 1,
  });
  type Page = "home" | "accounts" | "transactions" | "budget" | "insights" | "profile";
  const [page, setPage] = useState<Page>("home");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const accRes = await api("/accounts/");
      const accounts: any[] = accRes.results || accRes || [];

      const txRes = await api("/transactions/?ordering=-transactionDate&page_size=500");
      const transactions: any[] = txRes.results || txRes || [];

      setData(computeDashboard(accounts, transactions));

      // if there are NO accounts, open the dialog
            if (accounts.length === 0) setShowAdd(true);

    } catch (e: any) {
      setError(e?.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initial) return;
    refresh();
  }, [initial, refresh]);

  async function createAccount() {
    setSaving(true);
    try {
      const res = await api("/accounts/", {
        method: "POST",
        body: JSON.stringify(accForm),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.detail || "Failed to create account");
      setShowAdd(false);
      await refresh(); // reload dashboard with the new account
    } catch (err: any) {
      alert(err?.message || "Error creating account");
    } finally {
      setSaving(false);
    }
  }

  if (error) {
    return (
      <div className="grid min-h-screen place-items-center bg-gray-50 p-6 text-gray-900">
        <div className="max-w-lg rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <div className="mb-2 text-lg font-semibold">Couldn’t load your data</div>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto grid gap-0">
        <main>
          {/* Body */}
          <div className="space-y-6 p-6">
            {/* Stats */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Stat
                title="Total Balance"
                value={fmtC(data?.kpis.totalBalance)}
                delta={deltaStr(data?.kpis.totalBalanceDelta)}
                positive={(data?.kpis.totalBalanceDelta ?? 0) >= 0}
                icon={<Wallet className="h-5 w-5" />}
                loading={loading}
              />
              <Stat
                title="Monthly Income"
                value={fmtC(data?.kpis.monthlyIncome)}
                delta={deltaStr(data?.kpis.monthlyIncomeDelta)}
                positive={(data?.kpis.monthlyIncomeDelta ?? 0) >= 0}
                icon={<Clock className="h-5 w-5" />}
                loading={loading}
              />
              <Stat
                title="Monthly Expenses"
                value={fmtC(data?.kpis.monthlyExpenses)}
                delta={deltaStr(data?.kpis.monthlyExpensesDelta)}
                positive={(data?.kpis.monthlyExpensesDelta ?? 0) <= 0}
                icon={<Grid2X2 className="h-5 w-5" />}
                loading={loading}
              />
              <Stat
                title="Savings"
                value={fmtC(data?.kpis.savings)}
                delta={deltaStr(data?.kpis.savingsDelta)}
                positive={(data?.kpis.savingsDelta ?? 0) >= 0}
                icon={<Home className="h-5 w-5" />}
                loading={loading}
              />
            </div>

            {/* Charts Row */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Income vs Expenses */}
              <Card className="p-5 lg:col-span-2">
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-lg font-semibold">Income vs Expenses</div>
                  <div className="flex items-center gap-2 rounded-full border border-gray-200 p-1 text-sm">
                    <button onClick={() => setPeriod("month")} className={`rounded-full px-3 py-1 ${period === "month" ? "font-medium text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>Month</button>
                    <button onClick={() => setPeriod("year")} className={`rounded-full px-3 py-1 ${period === "year" ? "font-medium text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>Year</button>
                  </div>
                </div>
                <div className="h-64 w-full">
                  <ResponsiveContainer>
                    <BarChart data={data?.charts?.[period] || []} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e5e7eb" }} />
                      <Bar dataKey="income" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="expenses" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              {/* Financial Health */}
              <Card className="p-5">
                <div className="mb-2 flex items-center justify-between">
                  <div className="text-lg font-semibold">Financial Health</div>
                  <button className="text-gray-400">i</button>
                </div>
                <Gauge value={data?.health.score ?? 0} />
                <div className="mt-4 space-y-3">
                  <Row label="Savings Rate" value={`${data?.health.savingsRate ?? 0}%`}>
                    <Progress value={data?.health.savingsRate ?? 0} tone="emerald" />
                  </Row>
                  <Row label="Debt Ratio" value={`${data?.health.debtRatio ?? 0}%`}>
                    <Progress value={data?.health.debtRatio ?? 0} tone="rose" />
                  </Row>
                </div>
              </Card>
            </div>
          </div>
          <AddAccountDialog
          open={showAdd}
          saving={saving}
          form={accForm}
          onClose={() => setShowAdd(false)}
          onChange={(k, v) => setAccForm((f) => ({ ...f, [k]: v }))}
          onSubmit={createAccount}
        />
        </main>
      </div>
    </div>
  );
}

// ---- Types ----
type KPI = { totalBalance: number; totalBalanceDelta: number; monthlyIncome: number; monthlyIncomeDelta: number; monthlyExpenses: number; monthlyExpensesDelta: number; savings: number; savingsDelta: number };
type Health = { score: number; savingsRate: number; debtRatio: number };
type Charts = { month: { name: string; income: number; expenses: number }[]; year: { name: string; income: number; expenses: number }[] };
export type DashboardData = { kpis: KPI; health: Health; charts: Charts };

// ---- Components ----
type AccountForm = {
  accountName: string;
  officialAccountName: string;
  accountType: string;
  subAccountType?: string;
  accountNumber?: string;
  accountId?: string;
  isoCurrencyCode: string;
  availableBalance: number;
  currentBalance: number;
  limit: number;
  loans: number;
  depts: number;
  isInternalAccount: boolean;
  icon: number;
};

function AddAccountDialog({
  open,
  saving,
  form,
  onClose,
  onChange,
  onSubmit,
}: {
  open: boolean;
  saving: boolean;
  form: AccountForm;
  onClose: () => void;
  onChange: (key: keyof AccountForm, value: any) => void;
  onSubmit: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <div className="w-full max-w-2xl rounded-2xl bg-white shadow-xl ring-1 ring-gray-200">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="text-lg font-semibold">Add your first account</h3>
          <button onClick={onClose} className="rounded p-1 text-gray-500 hover:bg-gray-100">✕</button>
        </div>

        <div className="max-h-[75vh] overflow-y-auto px-5 py-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Text label="Account Name" value={form.accountName} onChange={(v)=>onChange("accountName", v)} />
            <Text label="Official Name" value={form.officialAccountName} onChange={(v)=>onChange("officialAccountName", v)} />
            <Select
              label="Account Type"
              value={form.accountType}
              onChange={(v)=>onChange("accountType", v)}
              options={["checking","savings","loan","credit","mortgage"]}
            />
            <Text label="Sub Type" value={form.subAccountType || ""} onChange={(v)=>onChange("subAccountType", v)} />
            <Text label="Account Number (masked)" value={form.accountNumber || ""} onChange={(v)=>onChange("accountNumber", v)} />
            <Text label="External ID" value={form.accountId || ""} onChange={(v)=>onChange("accountId", v)} />
            <Text label="Currency" value={form.isoCurrencyCode} onChange={(v)=>onChange("isoCurrencyCode", v)} />
            <Number label="Available Balance" value={form.availableBalance} onChange={(v)=>onChange("availableBalance", v)} />
            <Number label="Current Balance" value={form.currentBalance} onChange={(v)=>onChange("currentBalance", v)} />
            <Number label="Limit" value={form.limit} onChange={(v)=>onChange("limit", v)} />
            <Number label="Loans" value={form.loans} onChange={(v)=>onChange("loans", v)} />
            <Number label="Debts" value={form.depts} onChange={(v)=>onChange("depts", v)} />
            <Select
              label="Internal Account?"
              value={form.isInternalAccount ? "true" : "false"}
              onChange={(v)=>onChange("isInternalAccount", v === "true")}
              options={["true","false"]}
            />
            <Number label="Icon (index)" value={form.icon} onChange={(v)=>onChange("icon", v)} />
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 border-t px-5 py-4">
          <button onClick={onClose} className="rounded-lg px-4 py-2 text-gray-700 hover:bg-gray-100">Cancel</button>
          <button
            onClick={onSubmit}
            disabled={saving}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:brightness-110 disabled:opacity-60"
          >
            {saving ? "Saving…" : "Create account"}
          </button>
        </div>
      </div>
    </div>
  );
}

// tiny input helpers
function Text({label, value, onChange}:{label:string; value:string; onChange:(v:string)=>void}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input value={value} onChange={(e)=>onChange(e.target.value)}
             className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
    </label>
  );
}
function Number({label, value, onChange}:{label:string; value:number; onChange:(v:number)=>void}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input type="number" value={value} onChange={(e)=>onChange(parseFloat(e.target.value || "0"))}
             className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
    </label>
  );
}
function Select({label, value, onChange, options}:{label:string; value:string; onChange:(v:string)=>void; options:string[]}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <select value={value} onChange={(e)=>onChange(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200">
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

const Card = ({ className = "", children }: { className?: string; children: React.ReactNode }) => (
  <div className={`rounded-2xl bg-white/70 backdrop-blur shadow-sm ring-1 ring-gray-200 ${className}`}>{children}</div>
);

const Row = ({ label, value, children }: { label: string; value: string; children: React.ReactNode }) => (
  <div>
    <div className="flex items-center justify-between text-sm"><span className="text-gray-600">{label}</span><span className="font-medium">{value}</span></div>
    {children}
  </div>
);

const Stat = ({ title, value, delta, icon, positive, loading }: { title: string; value?: string; delta?: string; icon: React.ReactNode; positive: boolean; loading?: boolean }) => (
  <Card className="p-5">
    <div className="flex items-start justify-between">
      <div>
        <div className="text-sm text-gray-500">{title}</div>
        <div className="mt-1 text-2xl font-semibold text-gray-900">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.span key="skeleton" className="inline-block h-6 w-40 rounded bg-gray-200" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            ) : (
              <motion.span key={value} initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -8, opacity: 0 }} transition={{ duration: 0.25 }}>{value}</motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-gray-100 text-gray-600">{icon}</div>
    </div>
    <div className="mt-3 flex items-center gap-2 text-sm">
      {positive ? <TrendingUp className="h-4 w-4 text-emerald-500" /> : <TrendingDown className="h-4 w-4 text-rose-500" />}
      <span className={positive ? "text-emerald-600" : "text-rose-600"}>{delta}</span>
      <span className="text-gray-500">from last month</span>
    </div>
  </Card>
);

const Progress = ({ value, className = "", tone = "emerald" }: { value: number; className?: string; tone?: "emerald" | "rose" | "indigo" }) => (
  <div className={`h-2 w-full overflow-hidden rounded-full bg-gray-200 ${className}`}>
    <motion.div
      className={`${tone === "emerald" ? "bg-emerald-500" : tone === "rose" ? "bg-rose-500" : "bg-indigo-500"} h-full rounded-full`}
      initial={{ width: 0 }}
      animate={{ width: `${value}%` }}
      transition={{ duration: 0.7 }}
    />
  </div>
);


// SVG semi-gauge 0-100
const Gauge = ({ value = 0 }: { value: number }) => {
  const clamped = Math.max(0, Math.min(100, value));
  const angle = (clamped / 100) * 180; // degrees
  return (
    <div className="relative mx-auto w-full max-w-[420px]">
      <svg viewBox="0 0 200 120" className="w-full">
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
        </defs>
        <path d="M10,110 A90,90 0 0,1 190,110" stroke="#fee2e2" strokeWidth="16" fill="none" />
        <path d="M20,110 A80,80 0 0,1 180,110" stroke="url(#gaugeGradient)" strokeWidth="16" fill="none" />
        {Array.from({ length: 11 }).map((_, i) => {
          const a = (i / 10) * Math.PI; // 0..pi
          const x1 = 100 + Math.cos(Math.PI - a) * 72;
          const y1 = 110 - Math.sin(a) * 72;
          const x2 = 100 + Math.cos(Math.PI - a) * 78;
          const y2 = 110 - Math.sin(a) * 78;
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#fff" strokeOpacity="0.7" strokeWidth="2" />;
        })}
        <g transform={`rotate(${-90 + angle} 100 110)`}>
          <rect x="98" y="32" width="4" height="80" rx="2" fill="#111827" />
          <circle cx="100" cy="110" r="6" fill="#111827" />
        </g>
        <text x="25" y="118" className="fill-gray-400" fontSize="10">Poor</text>
        <text x="160" y="118" className="fill-gray-400" fontSize="10">Good</text>
        <text x="70" y="70" className="fill-gray-900" fontSize="18" fontWeight="600">Financial Health</text>
        <text x="88" y="90" className="fill-emerald-600" fontSize="20" fontWeight="700">{value}</text>
        <text x="135" y="90" className="fill-emerald-600" fontSize="12">Excellent</text>
      </svg>
    </div>
  );
};

// ---- Helpers ----
function fmtC(n?: number) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(n);
}
function deltaStr(p?: number) {
  if (p == null || isNaN(p)) return "0%";
  const s = (p >= 0 ? "+" : "") + p.toFixed(1) + "%";
  return s;
}

function computeDashboard(accounts: any[], transactions: any[]): DashboardData {
  const totalBalance = accounts.reduce((s, a) => s + (parseFloat(a.currentBalance ?? 0) || 0), 0);

  // Split by month (last 6 months) for a light demo
  const byMonth = new Map<string, { income: number; expenses: number }>();
  const now = new Date();
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = d.toLocaleString("en-US", { month: "short", year: "numeric" });
    byMonth.set(key, { income: 0, expenses: 0 });
  }

  transactions.forEach((t) => {
    const dt = t.transactionDate ? new Date(t.transactionDate) : null;
    if (!dt) return;
    const key = dt.toLocaleString("en-US", { month: "short", year: "numeric" });
    if (!byMonth.has(key)) return;
    const bucket = byMonth.get(key)!;
    const amt = parseFloat(t.amount ?? 0) || 0;
    if (t.isIncome) bucket.income += amt; else bucket.expenses += Math.abs(amt);
  });

  const monthArr = Array.from(byMonth.entries()).map(([name, v]) => ({ name, income: v.income, expenses: v.expenses }));
  const monthlyIncome = monthArr.at(-1)?.income ?? 0;
  const monthlyExpenses = monthArr.at(-1)?.expenses ?? 0;
  const prevIncome = monthArr.at(-2)?.income ?? 0;
  const prevExpenses = monthArr.at(-2)?.expenses ?? 0;

  const kpis: KPI = {
    totalBalance,
    totalBalanceDelta: 0, // assume flat for demo
    monthlyIncome,
    monthlyIncomeDelta: pctDelta(prevIncome, monthlyIncome),
    monthlyExpenses,
    monthlyExpensesDelta: pctDelta(prevExpenses, monthlyExpenses),
    savings: Math.max(0, totalBalance - monthlyExpenses),
    savingsDelta: 0,
  };

  const health: Health = {
    score: clamp(100 - Math.min(100, (monthlyExpenses / (monthlyIncome || 1)) * 100) + 20, 0, 100),
    savingsRate: clamp((monthlyIncome ? (1 - monthlyExpenses / monthlyIncome) * 100 : 0), 0, 100),
    debtRatio: clamp((monthlyExpenses / (totalBalance || 1)) * 100, 0, 100),
  };

  // Simple year chart from grouping by year
  const byYear = new Map<string, { income: number; expenses: number }>();
  transactions.forEach((t) => {
    const dt = t.transactionDate ? new Date(t.transactionDate) : null;
    if (!dt) return;
    const key = String(dt.getFullYear());
    const obj = byYear.get(key) || { income: 0, expenses: 0 };
    const amt = parseFloat(t.amount ?? 0) || 0;
    if (t.isIncome) obj.income += amt; else obj.expenses += Math.abs(amt);
    byYear.set(key, obj);
  });
  const yearArr = Array.from(byYear.entries()).sort(([a],[b]) => (a > b ? 1 : -1)).map(([name, v]) => ({ name, income: v.income, expenses: v.expenses }));

  return { kpis, health, charts: { month: monthArr, year: yearArr } };
}

function pctDelta(prev: number, curr: number) {
  if (!prev && !curr) return 0;
  if (!prev) return 100;
  return ((curr - prev) / Math.abs(prev)) * 100;
}
function clamp(n: number, min: number, max: number) { return Math.max(min, Math.min(max, n)); }
