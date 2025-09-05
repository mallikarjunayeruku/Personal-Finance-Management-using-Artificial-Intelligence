// src/pages/Accounts.tsx
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import {
  PiggyBank, Wallet, CreditCard, Banknote, Landmark, Plus,
} from "lucide-react";

/* ---------- Types ---------- */
type ApiAccount = {
  id: string | number;
  accountName: string;
  accountType?: string;
  officialAccountName?: string;
  isoCurrencyCode?: string;
  accountNumber?: string;        // masked number like ****4321
  currentBalance?: number;
  availableBalance?: number;     // <-- add back (used only for credit cards)
  limit?: number;
};

type AccountForm = {
  accountName: string;
  officialAccountName: string;
  accountType: string;
  subAccountType?: string;
  accountNumber?: string;
  accountId?: string;
  isoCurrencyCode: string;
  currentBalance: number;
  limit: number;
  loans: number;
  depts: number;
  isInternalAccount: boolean;
  icon: number;
};

/* ---------- Icons & colors per type ---------- */
const TYPE_META: Record<string, { label: string; icon: any; tone: string }> = {
  savings:       { label: "Savings",     icon: PiggyBank,  tone: "text-emerald-600 bg-emerald-50 ring-emerald-200" },
  current:       { label: "Current",     icon: Wallet,     tone: "text-indigo-600 bg-indigo-50 ring-indigo-200" },
  "credit card": { label: "Credit Card", icon: CreditCard, tone: "text-orange-600 bg-orange-50 ring-orange-200" },
  loan:          { label: "Loan",        icon: Banknote,   tone: "text-rose-600 bg-rose-50 ring-rose-200" },
  investments:   { label: "Investments", icon: Landmark,   tone: "text-teal-700 bg-teal-50 ring-teal-200" },
};

function normalizeType(t?: string) {
  if (!t) return "current";
  const s = t.trim().toLowerCase();
  if (s === "checking") return "current";
  if (["credit", "creditcard", "credit_card"].includes(s)) return "credit card";
  return s;
}

function fmtMoney(amount?: number, code?: string) {
  if (amount == null || isNaN(amount)) return "—";
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: code || "USD",
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return amount.toFixed(2);
  }
}

/* ---------- Page ---------- */
export default function Accounts() {
  const [items, setItems] = useState<ApiAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  // add account modal state
  const [openAdd, setOpenAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<AccountForm>({
    accountName: "Primary Checking",
    officialAccountName: "Chase Total Checking",
    accountType: "checking",
    subAccountType: "DEMAND_DEPOSIT",
    accountNumber: "****4321",
    accountId: "ext_abc_123",
    isoCurrencyCode: "USD",
    currentBalance: 1800.0,
    limit: 0,
    loans: 0,
    depts: 0,
    isInternalAccount: true,
    icon: 1,
  });

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const res = await api("/accounts/");
      const rows: ApiAccount[] = res?.results ?? res ?? [];
      setItems(rows);
    } catch (e: any) {
      setErr(e?.message || "Failed to fetch accounts");
    } finally {
      setLoading(false);
    }
  }

  async function createAccount() {
    setSaving(true);
    try {
      await api("/accounts/", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setOpenAdd(false);
      await load();
    } catch (e: any) {
      alert(e?.message || "Failed to create account");
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      {/* header with Add button */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Accounts</h1>
        <button
          onClick={() => setOpenAdd(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:brightness-110"
        >
          <Plus className="h-4 w-4" />
          Add account
        </button>
      </div>

      {/* error */}
      {err && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700">
          {err}
        </div>
      )}

      {/* grid */}
      {!loading && items.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((a) => {
            const key = normalizeType(a.accountType);
            const meta = TYPE_META[key] ?? TYPE_META["current"];
            const Icon = meta.icon;
            return (
              <div key={a.id} className="rounded-2xl bg-white p-5 ring-1 ring-gray-200">
                {/* header with icon, name, and masked account */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`grid h-12 w-12 place-items-center rounded-xl ring-1 ${meta.tone}`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div>
                      <div className="text-[15px] font-semibold text-gray-900">
                        {a.accountName || a.officialAccountName || "Account"}
                      </div>
                      <div className="mt-1 inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                        {meta.label}
                      </div>
                    </div>
                  </div>
                    <div className="mt-6">
                  <div className="text-[15px] font-semibold text-black ">Account Number</div>
                  <div className="text-2xl font-semibold">
                    {a.accountNumber && (
                    <div className="text-sm font-mono text-gray-500">{a.accountNumber}</div>
                  )}
                  </div>
                </div>

                </div>

                {/* balance */}
                  <div className="mt-6">
  <div className="text-sm text-gray-500">
    {isCreditCard(key) ? "Outstanding Balance" : "Current Balance"}
  </div>
  <div className="text-2xl font-semibold">
    {fmtMoney(a.currentBalance, a.isoCurrencyCode)}
  </div>

  {isCreditCard(key) && (
    <>
      {availableForCard(a) != null && (
        <div className="mt-1 text-sm text-gray-500">
          Available:{" "}
          <span className="font-medium text-gray-700">
            {fmtMoney(availableForCard(a)!, a.isoCurrencyCode)}
          </span>
        </div>
      )}
      {typeof a.limit === "number" && (
        <div className="text-sm text-gray-500">
          Limit:{" "}
          <span className="font-medium text-gray-700">
            {fmtMoney(a.limit, a.isoCurrencyCode)}
          </span>
        </div>
      )}
    </>
  )}
</div>

              </div>
            );
          })}
        </div>
      )}

      {/* Add account modal */}
      <AddAccountDialog
        open={openAdd}
        saving={saving}
        form={form}
        onChange={(k, v) => setForm((f) => ({ ...f, [k]: v }))}
        onClose={() => setOpenAdd(false)}
        onSubmit={createAccount}
      />
    </div>
  );
}

/* ---------- Modal + inputs ---------- */
function AddAccountDialog({
  open, saving, form, onChange, onClose, onSubmit,
}: {
  open: boolean;
  saving: boolean;
  form: AccountForm;
  onChange: (key: keyof AccountForm, value: any) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-gray-200">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="text-lg font-semibold">Add account</h3>
          <button onClick={onClose} className="rounded p-1 text-gray-500 hover:bg-gray-100">✕</button>
        </div>

        <div className="max-h-[75vh] overflow-y-auto px-5 py-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Text label="Account Name" value={form.accountName} onChange={(v) => onChange("accountName", v)} />
            <Select
              label="Account Type"
              value={form.accountType}
              onChange={(v) => onChange("accountType", v)}
              options={["checking", "savings", "credit card", "loan", "investments", "current"]}
            />
            <Text label="Account Number (masked)" value={form.accountNumber || ""} onChange={(v) => onChange("accountNumber", v)} />
            <Text label="Currency" value={form.isoCurrencyCode} onChange={(v) => onChange("isoCurrencyCode", v)} />
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

function Text({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200"
      />
    </label>
  );
}
function Number({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input
        type="number"
        value={isFinite(value) ? value : 0}
        onChange={(e) => onChange(parseFloat(e.target.value || "0"))}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200"
      />
    </label>
  );
}
function isCreditCard(typeKey: string) {
  return typeKey === "credit card";
}

function availableForCard(a: ApiAccount) {
  if (typeof a.availableBalance === "number") return a.availableBalance;
  if (typeof a.limit === "number" && typeof a.currentBalance === "number") {
    // available = limit - outstanding
    return Math.max(0, a.limit - a.currentBalance);
  }
  return undefined;
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}
