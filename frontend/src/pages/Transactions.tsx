// src/pages/Transactions.tsx
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { Plus, Search, Loader2, ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight } from "lucide-react";

/* -------------------- Types -------------------- */
type ApiAccount = {
  id: number | string;
  accountName?: string;
  accountType?: string;
  accountNumber?: string;
  isoCurrencyCode?: string;
};

type ApiTransaction = {
  id: number | string;
  amount?: number;
  category?: string;
  name?: string;
  merchantName?: string;
  currencyCode?: string;
  checkNumber?: string;
  note?: string;
  createdDate?: string;
  transactionDate?: string;
  location?: string;
  isIncome?: boolean;
  repeat?: string;
  account: number | string;
  isCashAccount?: boolean;
  canDelete?: boolean;
  category_display?: string;
};

type TxForm = {
  name: string;
  merchantName: string;
  amount: number;
  isIncome: boolean;
  category: string;
  currencyCode: string;
  transactionDate: string;
  account: number | string;
  note: string;
};

type ApiCategory = { id: number | string; name: string; slug: string };

/* -------------------- Helpers -------------------- */
function fmtMoney(n?: number, code?: string) {
  if (n == null || isNaN(n)) return "—";
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: code || "USD", maximumFractionDigits: 2 }).format(n);
  } catch {
    return n.toFixed(2);
  }
}
function normalizeType(t?: string) {
  if (!t) return "current";
  const s = t.trim().toLowerCase();
  if (s === "checking") return "current";
  if (["credit", "creditcard", "credit_card"].includes(s)) return "credit card";
  return s;
}
function isoLocal(date?: string | Date) {
  const d = date ? new Date(date) : new Date();
  const pad = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/* -------------------- Page -------------------- */
export default function Transactions() {
  const [accounts, setAccounts] = useState<ApiAccount[]>([]);
  const [rows, setRows] = useState<ApiTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  // NEW: pagination state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [count, setCount] = useState(0);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [prevUrl, setPrevUrl] = useState<string | null>(null);

  // filters (client-side)
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [accountFilter, setAccountFilter] = useState<string>("all");

  // modal state
  const [openAdd, setOpenAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<TxForm>({
    name: "",
    merchantName: "",
    amount: 0,
    isIncome: false,
    category: "",
    currencyCode: "USD",
    transactionDate: isoLocal(),
    account: "" as any,
    note: "",
  });

  const [categories, setCategories] = useState<ApiCategory[]>([]);
  useEffect(() => {
    api("/categories/?ordering=name&page_size=500")
      .then((r) => setCategories(r?.results ?? r ?? []))
      .catch(() => setCategories([]));
  }, []);

  // NEW: core loader with pagination
  async function load(goToPage = page, size = pageSize) {
    setLoading(true);
    setErr(null);
    try {
      // accounts (once per load, small)
      const accRes = await api("/accounts/?page_size=500");
      const accs: ApiAccount[] = accRes?.results ?? accRes ?? [];
      setAccounts(accs);
      if (!form.account && accs[0]?.id != null) setForm((f) => ({ ...f, account: accs[0].id }));

      const params = new URLSearchParams({
        ordering: "-transactionDate",
        page: String(goToPage),
        page_size: String(size),
      });
      const txRes = await api(`/transactions/?${params.toString()}`);

      // txRes is paginated: { count, next, previous, results: [...] }
      const txs: ApiTransaction[] = txRes?.results ?? [];
      console.log(txs.length)
      setRows(txs);
      setCount(txRes?.count || 0);
      setNextUrl(txRes?.next || null);
      setPrevUrl(txRes?.previous || null);
      setPage(goToPage);
      setPageSize(size);
    } catch (e: any) {
      setErr(e?.message || "Failed to fetch transactions");
    } finally {
      setLoading(false);
    }
  }

  // initial load
  useEffect(() => { load(1, pageSize); /* eslint-disable-next-line */ }, []);

  // when pageSize changes, reset to page 1
  useEffect(() => {
    load(1, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageSize]);

  const accountsById = useMemo(() => {
    const map = new Map<number | string, ApiAccount>();
    accounts.forEach((a) => map.set(a.id, a));
    return map;
  }, [accounts]);

  const typeOptions = useMemo(() => {
    const set = new Set<string>();
    accounts.forEach((a) => set.add(normalizeType(a.accountType)));
    return ["all", ...Array.from(set)];
  }, [accounts]);

  const accountOptions = useMemo(() => ["all", ...accounts.map((a) => a.id)], [accounts]);

  const filtered = useMemo(() => {
    // client-side filter is applied to the current page
    const text = q.trim().toLowerCase();
    return rows.filter((t) => {
      const acc = accountsById.get(t.account);
      const accType = normalizeType(acc?.accountType);
      const byText =
        !text ||
        [t.name, t.merchantName, t.category, t.note, acc?.accountNumber, acc?.accountName]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(text));
      const byType = typeFilter === "all" || accType === typeFilter;
      const byAccount = accountFilter === "all" || String(t.account) === accountFilter;
      return byText && byType && byAccount;
    });
  }, [rows, q, typeFilter, accountFilter, accountsById]);

  // NEW: pagination helpers
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  const startIdx = count === 0 ? 0 : (page - 1) * pageSize + 1;
  const endIdx = Math.min(count, (page - 1) * pageSize + rows.length);

  function goFirst() { if (page > 1) load(1, pageSize); }
  function goPrev() { if (prevUrl && page > 1) load(page - 1, pageSize); }
  function goNext() { if (nextUrl && page < totalPages) load(page + 1, pageSize); }
  function goLast() { if (page < totalPages) load(totalPages, pageSize); }

  async function createTx() {
    setSaving(true);
    try {
      let tcategory = getCategoryByNameOrLast(categories as any, form.category);
      const payload = {
        ...form,
        amount: isNaN(form.amount) ? 0 : form.amount,
        transactionDate: new Date(form.transactionDate).toISOString(),
        category: tcategory?.id,
      };
      await api("/transactions/", { method: "POST", body: JSON.stringify(payload) });
      setOpenAdd(false);
      setForm((f) => ({ ...f, name: "", merchantName: "", amount: 0, category: "", note: "" }));
      // reload current page (helps keep context)
      await load(page, pageSize);
    } catch (e: any) {
      alert(e?.message || "Failed to create transaction");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">Transactions</h1>
        <button
          onClick={() => setOpenAdd(true)}
          className="inline-flex items-center gap-2 self-start rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:brightness-110"
        >
          <Plus className="h-4 w-4" />
          Add Transaction
        </button>
      </div>

      {/* Filters Row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative w-full sm:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search name, merchant, category, notes…"
            className="w-full rounded-lg border border-gray-300 bg-white pl-9 pr-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200"
          />
        </div>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200"
        >
          {typeOptions.map((t) => (
            <option key={t} value={t}>
              {t === "all" ? "All types" : t.replace(/\b\w/g, (m) => m.toUpperCase())}
            </option>
          ))}
        </select>

        <select
          value={accountFilter}
          onChange={(e) => setAccountFilter(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200"
        >
          {accountOptions.map((id) => {
            if (id === "all") return <option key="all" value="all">All accounts</option>;
            const a = accountsById.get(id);
            const label = (a?.accountName || a?.accountType || "Account") + (a?.accountNumber ? ` • ${a.accountNumber}` : "");
            return <option key={String(id)} value={String(id)}>{label}</option>;
          })}
        </select>

        {/* NEW: page size */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-sm text-gray-600">Rows:</span>
          <select
            value={pageSize}
            onChange={(e) => setPageSize(parseInt(e.target.value || "50", 10))}
            className="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-sm"
          >
            {[25, 50, 100, 250, 500].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-2xl bg-white ring-1 ring-gray-200">
        <div className="min-w-full overflow-x-auto">
          <table className="min-w-full whitespace-nowrap text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <Th>Date</Th>
                <Th>Description</Th>
                <Th>Merchant</Th>
                <Th>Account</Th>
                <Th>Category</Th>
                <Th className="text-right">Amount</Th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-gray-500">
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading…
                    </span>
                  </td>
                </tr>
              )}

              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-gray-500">No transactions found.</td>
                </tr>
              )}

              {!loading &&
                filtered.map((t) => {
                  const acc = accountsById.get(t.account);
                  const code = t.currencyCode || acc?.isoCurrencyCode || "USD";
                  const signClass = (t.isIncome ? "text-emerald-600" : "text-rose-600") + " font-semibold";
                  return (
                    <tr key={t.id} className="border-t border-gray-100 hover:bg-gray-50/60">
                      <Td>{t.transactionDate ? new Date(t.transactionDate).toLocaleString() : "—"}</Td>
                      <Td>{t.name || "—"}</Td>
                      <Td className="text-gray-700">{t.merchantName || "—"}</Td>
                      <Td className="text-gray-700">
                        {(acc?.accountName || acc?.accountType || "Account") + (acc?.accountNumber ? ` • ${acc.accountNumber}` : "")}
                      </Td>
                      <Td className="text-gray-700">{t.category_display || "—"}</Td>
                      <Td className={`text-right ${signClass}`}>{fmtMoney(t.amount, code)}</Td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>

        {/* NEW: footer with range + pager */}
        <div className="flex flex-col items-center justify-between gap-3 border-t px-4 py-3 sm:flex-row">
          <div className="text-sm text-gray-600">
            {count === 0 ? "No results" : `Showing ${startIdx}–${endIdx} of ${count}`}
          </div>

          <div className="flex items-center gap-1">
            <PagerBtn onClick={goFirst} disabled={page <= 1} title="First"><ChevronsLeft className="h-4 w-4" /></PagerBtn>
            <PagerBtn onClick={goPrev} disabled={!prevUrl}><ChevronLeft className="h-4 w-4" /></PagerBtn>

            <span className="px-2 text-sm text-gray-700">
              Page <strong>{page}</strong> / {totalPages}
            </span>

            <PagerBtn onClick={goNext} disabled={!nextUrl}><ChevronRight className="h-4 w-4" /></PagerBtn>
            <PagerBtn onClick={goLast} disabled={page >= totalPages} title="Last"><ChevronsRight className="h-4 w-4" /></PagerBtn>
          </div>
        </div>
      </div>

      {/* Add Transaction Modal (unchanged except save→reload keeps current page) */}
      {openAdd && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-gray-200">
            <div className="flex items-center justify-between border-b px-5 py-4">
              <h3 className="text-lg font-semibold">Add Transaction</h3>
              <button onClick={() => setOpenAdd(false)} className="rounded p-1 text-gray-500 hover:bg-gray-100">✕</button>
            </div>

            <div className="max-h-[75vh] overflow-y-auto px-5 py-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Text label="Description" value={form.name} onChange={(v) => setForm((f) => ({ ...f, name: v }))} />
                <Text label="Merchant" value={form.merchantName} onChange={(v) => setForm((f) => ({ ...f, merchantName: v }))} />
                <Number label="Amount" value={form.amount} onChange={(v) => setForm((f) => ({ ...f, amount: v }))} />
                <Select label="Type" value={form.isIncome ? "income" : "expense"} options={["expense", "income"]} onChange={(v) => setForm((f) => ({ ...f, isIncome: v === "income" }))} />
                <CategoryField
                  value={form.category}
                  categories={categories}
                  onChange={(v) => setForm(f => ({ ...f, category: v }))}
                />
                <Text label="Currency" value={form.currencyCode} onChange={(v) => setForm((f) => ({ ...f, currencyCode: v }))} />
                <DateTime label="Transaction Date" value={form.transactionDate} onChange={(v) => setForm((f) => ({ ...f, transactionDate: v }))} />
                <Select
                  label="Account"
                  value={String(form.account)}
                  options={accounts.map((a) => ({
                    value: String(a.id),
                    label: (a.accountName || a.accountType || "Account") + (a.accountNumber ? ` • ${a.accountNumber}` : ""),
                  }))}
                  onChange={(v) => setForm((f) => ({ ...f, account: v }))}
                />
                <Area label="Note" value={form.note} onChange={(v) => setForm((f) => ({ ...f, note: v }))} className="md:col-span-2" />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 border-t px-5 py-4">
              <button onClick={() => setOpenAdd(false)} className="rounded-lg px-4 py-2 text-gray-700 hover:bg-gray-100">Cancel</button>
              <button onClick={createTx} disabled={saving} className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:brightness-110 disabled:opacity-60">
                {saving ? "Saving…" : "Add Transaction"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* -------------------- Small UI bits -------------------- */
function Th({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide ${className}`}>{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-4 py-3 align-top ${className}`}>{children}</td>;
}
function PagerBtn({ children, onClick, disabled, title }: { children: React.ReactNode; onClick: () => void; disabled?: boolean; title?: string; }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}
function Text({ label, value, onChange, className = "" }: { label: string; value: string; onChange: (v: string) => void; className?: string }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
    </label>
  );
}
function Area({ label, value, onChange, className = "" }: { label: string; value: string; onChange: (v: string) => void; className?: string }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <textarea rows={3} value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
    </label>
  );
}
function Number({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input type="number" value={isFinite(value) ? value : 0} onChange={(e) => onChange(parseFloat(e.target.value || "0"))} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
    </label>
  );
}
function DateTime({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input type="datetime-local" value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
    </label>
  );
}
function Select({ label, value, options, onChange }: { label: string; value: string; options: (string | { value: string; label: string })[]; onChange: (v: string) => void; }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200">
        {options.map((o) =>
          typeof o === "string" ? (
            <option key={o} value={o}>{o}</option>
          ) : (
            <option key={o.value} value={o.value}>{o.label}</option>
          )
        )}
      </select>
    </label>
  );
}
function CategoryField({ value, categories, onChange }: { value: string; categories: ApiCategory[]; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return categories;
    return categories.filter(c => c.name.toLowerCase().includes(s));
  }, [q, categories]);

  return (
    <div className="relative">
      <label className="block">
        <span className="mb-1 block text-sm font-medium text-gray-700">Category</span>
        <div className="flex gap-2">
          <input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Pick or type…" className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
          <button type="button" onClick={() => setOpen(v => !v)} className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm hover:bg-gray-50">
            Browse
          </button>
        </div>
      </label>

      {open && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-gray-200">
          <div className="border-b p-2">
            <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search categories…" className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-gray-400 focus:ring-2 focus:ring-indigo-200" />
          </div>
          <div className="max-h-64 overflow-auto p-1">
            {filtered.length === 0 && <div className="p-3 text-sm text-gray-500">No matches</div>}
            {filtered.map((c) => (
              <button key={c.name} type="button" onClick={() => { onChange(c.name); setOpen(false); setQ(""); }} className={`block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-gray-50 ${c.name === value ? "bg-indigo-50 text-indigo-700" : "text-gray-800"}`}>
                {c.name}
              </button>
            ))}
          </div>
          <div className="flex items-center justify-end gap-2 border-t p-2">
            <button onClick={() => setOpen(false)} className="rounded-lg px-3 py-1.5 text-sm hover:bg-gray-100">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
function getCategoryByNameOrLast(categories: { id: number | string; name: string }[], name: string) {
  if (!categories || categories.length === 0) return null;
  const found = categories.find(c => c.name.toLowerCase() === name.toLowerCase());
  return found || categories[categories.length - 1];
}
