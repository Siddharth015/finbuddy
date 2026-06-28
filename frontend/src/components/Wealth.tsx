import { useEffect, useState } from "react";
import { api } from "../api";
import { money, percent, signedMoney } from "../format";
import { useAsync } from "../hooks";
import { haptic } from "../telegram";
import { useBackButton } from "../telegramButtons";
import { useToast } from "../toast";
import { EmptyState, ErrorState, SkeletonList } from "../widgets";
import type { Account, Investment, Space } from "../types";

const ACCOUNT_TYPES = ["bank", "cash", "credit_card", "wallet"];
const INVESTMENT_TYPES = [
  "equity",
  "mutual_fund",
  "fixed_deposit",
  "bond",
  "crypto",
  "gold",
  "other",
];

export function Wealth({ space }: { space: Space }) {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync<[Account[], Investment[]]>(
    () => Promise.all([api.accounts(space.id), api.investments(space.id)]),
    [space.id],
  );
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [adding, setAdding] = useState<"account" | "investment" | null>(null);

  useEffect(() => {
    if (data) {
      setAccounts(data[0]);
      setInvestments(data[1]);
    }
  }, [data]);

  const cur = space.currency;
  const accountsTotal = accounts.reduce((s, a) => s + Number(a.balance), 0);
  const invValue = investments.reduce((s, i) => s + Number(i.current_value), 0);
  const invInvested = investments.reduce((s, i) => s + Number(i.invested), 0);
  const pnl = invValue - invInvested;
  const pnlPct = invInvested > 0 ? (pnl / invInvested) * 100 : 0;

  const removeAccount = (a: Account) => {
    haptic("warning");
    const idx = accounts.findIndex((x) => x.id === a.id);
    setAccounts((p) => p.filter((x) => x.id !== a.id));
    toast.showUndo("Account removed", {
      onCommit: () => {
        api.deleteAccount(space.id, a.id).catch(() => reload());
      },
      onUndo: () =>
        setAccounts((p) => {
          const c = [...p];
          c.splice(Math.min(idx, c.length), 0, a);
          return c;
        }),
    });
  };

  const removeInvestment = (i: Investment) => {
    haptic("warning");
    const idx = investments.findIndex((x) => x.id === i.id);
    setInvestments((p) => p.filter((x) => x.id !== i.id));
    toast.showUndo("Holding removed", {
      onCommit: () => {
        api.deleteInvestment(space.id, i.id).catch(() => reload());
      },
      onUndo: () =>
        setInvestments((p) => {
          const c = [...p];
          c.splice(Math.min(idx, c.length), 0, i);
          return c;
        }),
    });
  };

  if (loading) return <SkeletonList rows={5} />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div>
      <div className="section-row">
        <div className="section-title" style={{ margin: 0 }}>
          Accounts
        </div>
        {accounts.length > 0 && (
          <div className="day-total">{money(accountsTotal, cur)}</div>
        )}
      </div>
      <div className="card">
        {accounts.length === 0 ? (
          <EmptyState
            emoji="🏦"
            title="No accounts yet"
            hint="Track balances across your bank, cash and cards."
          />
        ) : (
          accounts.map((a) => (
            <div className="txn" key={a.id}>
              <div className="icon">🏦</div>
              <div className="meta">
                <div className="t">{a.name}</div>
                <div className="s">{a.type.replace("_", " ")}</div>
              </div>
              <div className="amt">{money(a.balance, cur)}</div>
              <button
                className="delete-x"
                onClick={() => removeAccount(a)}
                aria-label="Remove account"
              >
                ✕
              </button>
            </div>
          ))
        )}
        <button
          className="ghost"
          style={{ marginTop: 10 }}
          onClick={() => {
            haptic("light");
            setAdding("account");
          }}
        >
          + Add account
        </button>
      </div>

      <div className="section-title">Investments</div>
      <div className="card">
        {investments.length > 0 && (
          <div className="stat-grid" style={{ marginBottom: 12 }}>
            <div className="stat">
              <div className="k">Value</div>
              <div className="v">{money(invValue, cur)}</div>
            </div>
            <div className="stat">
              <div className="k">P&amp;L</div>
              <div
                className="v"
                style={{ color: pnl >= 0 ? "var(--green)" : "var(--red)" }}
              >
                {signedMoney(pnl, cur)}
                <span style={{ fontSize: 12, opacity: 0.8 }}>
                  {" "}
                  ({percent(pnlPct)})
                </span>
              </div>
            </div>
          </div>
        )}
        {investments.length === 0 ? (
          <EmptyState
            emoji="📈"
            title="No holdings yet"
            hint="Add stocks, funds, gold or crypto to track net worth."
          />
        ) : (
          investments.map((i) => {
            const gain = Number(i.current_value) - Number(i.invested);
            return (
              <div className="txn" key={i.id}>
                <div className="icon">📈</div>
                <div className="meta">
                  <div className="t">{i.name}</div>
                  <div className="s">
                    {i.units} units · {i.type.replace("_", " ")}
                  </div>
                </div>
                <div className="amt" style={{ textAlign: "right" }}>
                  <div>{money(i.current_value, cur)}</div>
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: gain >= 0 ? "var(--green)" : "var(--red)",
                    }}
                  >
                    {signedMoney(gain, cur)}
                  </div>
                </div>
                <button
                  className="delete-x"
                  onClick={() => removeInvestment(i)}
                  aria-label="Remove holding"
                >
                  ✕
                </button>
              </div>
            );
          })
        )}
        <button
          className="ghost"
          style={{ marginTop: 10 }}
          onClick={() => {
            haptic("light");
            setAdding("investment");
          }}
        >
          + Add investment
        </button>
      </div>

      {adding === "account" && (
        <AddAccountSheet
          space={space}
          onClose={() => setAdding(null)}
          onAdded={() => {
            setAdding(null);
            reload();
          }}
        />
      )}
      {adding === "investment" && (
        <AddInvestmentSheet
          space={space}
          onClose={() => setAdding(null)}
          onAdded={() => {
            setAdding(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

function AddAccountSheet({
  space,
  onClose,
  onAdded,
}: {
  space: Space;
  onClose: () => void;
  onAdded: () => void;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("bank");
  const [balance, setBalance] = useState("0");
  const [busy, setBusy] = useState(false);
  useBackButton(onClose);

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await api.addAccount(space.id, {
        name: name.trim(),
        type,
        balance,
        currency: space.currency,
      });
      haptic("success");
      onAdded();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h2>Add account</h2>
        <label className="field">Name</label>
        <input
          autoFocus
          placeholder="HDFC Savings"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div className="row">
          <div>
            <label className="field">Type</label>
            <select value={type} onChange={(e) => setType(e.target.value)}>
              {ACCOUNT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="field">Balance</label>
            <input
              type="number"
              inputMode="decimal"
              value={balance}
              onChange={(e) => setBalance(e.target.value)}
            />
          </div>
        </div>
        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}

function AddInvestmentSheet({
  space,
  onClose,
  onAdded,
}: {
  space: Space;
  onClose: () => void;
  onAdded: () => void;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("equity");
  const [units, setUnits] = useState("0");
  const [avg, setAvg] = useState("0");
  const [current, setCurrent] = useState("0");
  const [busy, setBusy] = useState(false);
  useBackButton(onClose);

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await api.addInvestment(space.id, {
        name: name.trim(),
        type,
        units,
        avg_buy_price: avg,
        current_price: current,
        currency: space.currency,
      });
      haptic("success");
      onAdded();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h2>Add investment</h2>
        <label className="field">Name</label>
        <input
          autoFocus
          placeholder="Nifty 50 Index Fund"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <label className="field">Type</label>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {INVESTMENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.replace("_", " ")}
            </option>
          ))}
        </select>
        <div className="row">
          <div>
            <label className="field">Units</label>
            <input
              type="number"
              inputMode="decimal"
              value={units}
              onChange={(e) => setUnits(e.target.value)}
            />
          </div>
          <div>
            <label className="field">Avg price</label>
            <input
              type="number"
              inputMode="decimal"
              value={avg}
              onChange={(e) => setAvg(e.target.value)}
            />
          </div>
          <div>
            <label className="field">Now</label>
            <input
              type="number"
              inputMode="decimal"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
            />
          </div>
        </div>
        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}
