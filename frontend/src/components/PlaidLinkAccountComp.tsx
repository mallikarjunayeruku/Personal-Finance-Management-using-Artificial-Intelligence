import {useState} from "react";
import {api} from "../lib/api.ts";

async function loadPlaidScript() {
  if (window.Plaid) return;
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://cdn.plaid.com/link/v2/stable/link-initialize.js";
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load Plaid Link script"));
    document.head.appendChild(s);
  });
}

export default function AccountsHeaderButtons({
  afterLinked,
}: { afterLinked?: () => void }) {
  const [linking, setLinking] = useState(false);

  const onClickLinkAccounts = async () => {
    try {
      setLinking(true);
      // 1) call YOUR backend only
      const { link_token } = await api("/plaid/link-token/", { method: "POST" });

      // 2) load Plaid Link JS (no REST calls to Plaid from browser)
      await loadPlaidScript();
      if (!window.Plaid) throw new Error("Plaid Link unavailable");

      // 3) open Link with the token you got from YOUR backend
      const handler = window.Plaid.create({
        token: link_token,
          onSuccess: async (public_token: string, metadata: any) => {
              await api("/plaid/exchange-public-token/", {
                  method: "POST",
                  body: JSON.stringify({
                      public_token,
                      institution_name: metadata.institution?.name,
                  }),
              });

          // Optionally refresh accounts UI
          afterLinked?.();
        },
        onExit: (err: any) => {
          if (err) console.warn("Link exit error:", err);
        },
      });

      handler.open();
    } catch (e: any) {
      alert(e?.message || "Could not start linking");
    } finally {
      setLinking(false);
    }
  };

  return (
    <div className="flex gap-3">
      <button
        onClick={onClickLinkAccounts}
        disabled={linking}
        className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:brightness-110 disabled:opacity-60"
      >
        {linking ? "Starting…" : "🔗 Link Accounts"}
      </button>

      {/* your existing Add Account button here */}
    </div>
  );
}