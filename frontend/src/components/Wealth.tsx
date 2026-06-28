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

type SheetState =
  | { kind: "account"; item?: Account }
  | { kind: "investment"; item?: Investment }
  | null;

export function Wealth({ space }: { space: Space }) {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync<[Account[], Investment[]]>(
    () => Promise.all([api.accounts(space.id), api.investments(space.id)]),
    [space.id],
  );
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [sheet, setSheet] = useState<SheetState>(null);

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
            <div
              className="txn tappable"
              key={a.id}
              onClick={() => {
                haptic("light");
                setSheet({ kind: "account", item: a });
              }}
            >
              <div className="icon">🏦</div>
              <div className="meta">
                <div className="t">{a.name}</div>
                <div className="s">{a.type.replace("_", " ")}</div>
              </div>
              <div className="amt">{money(a.balance, cur)}</div>
              <button
                className="delete-x"
                onClick={(e) => {
                  e.stopPropagation();
                  removeAccount(a);
                }}
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
            setSheet({ kind: "account" });
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
              <div
                className="txn tappable"
                key={i.id}
                onClick={() => {
                  haptic("light");
                  setSheet({ kind: "investment", item: i });
                }}
              >
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
                  onClick={(e) => {
                    e.stopPropagation();
                    removeInvestment(i);
                  }}
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
            setSheet({ kind: "investment" });
          }}
        >
          + Add investment
        </button>
      </div>

      {sheet?.kind === "account" && (
        <AccountSheet
          space={space}
          existing={sheet.item}
          onClose={() => setSheet(null)}
          onSaved={() => {
            setSheet(null);
            reload();
          }}
        />
      )}
      {sheet?.kind === "investment" && (
        <InvestmentSheet
          space={space}
          existing={sheet.item}
          onClose={() => setSheet(null)}
          onSaved={() => {
            setSheet(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

function AccountSheet({
  space,
  existing,
  onClose,
  onSaved,
}: {
  space: Space;
  existing?: Account;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(existing?.name ?? "");
  const [type, setType] = useState<string>(existing?.type ?? "bank");
  const [balance, setBalance] = useState(existing?.balance ?? "0");
  const [busy, setBusy] = useState(false);
  useBackButton(onClose);

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      if (existing) {
        await api.updateAccount(space.id, existing.id, {
          name: name.trim(),
          type,
          balance,
        });
      } else {
        await api.addAccount(space.id, {
          name: name.trim(),
          type,
          balance,
          currency: space.currency,
        });
      }
      haptic("success");
      onSaved();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h2>{existing ? "Edit account" : "Add account"}</h2>
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
          {busy ? "Saving…" : existing ? "Save changes" : "Save"}
        </button>
      </div>
    </div>
  );
}

function InvestmentSheet({
  space,
  existing,
  onClose,
  onSaved,
}: {
  space: Space;
  existing?: Investment;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(existing?.name ?? "");
  const [type, setType] = useState<string>(existing?.type ?? "equity");
  const [units, setUnits] = useState(existing?.units ?? "0");
  const [avg, setAvg] = useState(existing?.avg_buy_price ?? "0");
  const [current, setCurrent] = useState(existing?.current_price ?? "0");
  const [busy, setBusy] = useState(false);
  useBackButton(onClose);

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      if (existing) {
        await api.updateInvestment(space.id, existing.id, {
          name: name.trim(),
          units,
          avg_buy_price: avg,
          current_price: current,
        });
      } else {
        await api.addInvestment(space.id, {
          name: name.trim(),
          type,
          units,
          avg_buy_price: avg,
          current_price: current,
          currency: space.currency,
        });
      }
      haptic("success");
      onSaved();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h2>{existing ? "Edit investment" : "Add investment"}</h2>
        <label className="field">Name</label>
        <input
          autoFocus
          placeholder="Nifty 50 Index Fund"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <label className="field">Type</label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          disabled={!!existing}
        >
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
          {busy ? "Saving…" : existing ? "Save changes" : "Save"}
        </button>
      </div>
    </div>
  );
}
