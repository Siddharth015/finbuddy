import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { categoryIcon, formatDate, money } from "../format";
import { useAsync } from "../hooks";
import { haptic } from "../telegram";
import { useToast } from "../toast";
import { EmptyState, ErrorState, SkeletonList } from "../widgets";
import type { Space, Transaction } from "../types";

type Filter = "all" | "expense" | "income" | "shared";

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "expense", label: "Expenses" },
  { id: "income", label: "Income" },
  { id: "shared", label: "Shared" },
];

export function History({ space }: { space: Space }) {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(
    () => api.transactions(space.id, 200),
    [space.id],
  );
  const [items, setItems] = useState<Transaction[]>([]);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    if (data) setItems(data);
  }, [data]);

  const remove = (t: Transaction) => {
    haptic("warning");
    const idx = items.findIndex((x) => x.id === t.id);
    setItems((prev) => prev.filter((x) => x.id !== t.id));
    toast.showUndo("Transaction deleted", {
      onCommit: () => {
        api.deleteTransaction(space.id, t.id).catch(() => reload());
      },
      onUndo: () =>
        setItems((prev) => {
          const copy = [...prev];
          copy.splice(Math.min(idx, copy.length), 0, t);
          return copy;
        }),
    });
  };

  const visible = useMemo(() => {
    if (filter === "all") return items;
    if (filter === "shared") return items.filter((t) => t.scope === "shared");
    return items.filter((t) => t.type === filter);
  }, [items, filter]);

  if (loading) return <SkeletonList rows={6} />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  if (items.length === 0) {
    return (
      <EmptyState
        emoji="🧾"
        title="No transactions yet"
        hint="Add one with the + button or message the bot."
      />
    );
  }

  const groups = groupByDay(visible);

  return (
    <div>
      <div className="filter-row">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            className={`chip ${filter === f.id ? "active" : ""}`}
            onClick={() => {
              haptic("select");
              setFilter(f.id);
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState emoji="🔍" title="Nothing here" hint="No matching transactions." />
      ) : (
        Object.entries(groups).map(([day, dayItems]) => (
          <div key={day}>
            <div className="section-row">
              <div className="section-title" style={{ margin: 0 }}>
                {day}
              </div>
              <div className="day-total">{dayTotal(dayItems, space.currency)}</div>
            </div>
            <div className="card">
              {dayItems.map((t) => (
                <div className="txn" key={t.id}>
                  <div className="icon">{categoryIcon(t.category)}</div>
                  <div className="meta">
                    <div className="t">
                      {t.note || t.category}
                      {t.scope === "shared" && (
                        <span className="badge">shared</span>
                      )}
                    </div>
                    <div className="s">{t.category}</div>
                  </div>
                  <div className={`amt ${t.type}`}>
                    {t.type === "income" ? "+" : "−"}
                    {money(t.amount, space.currency)}
                  </div>
                  <button
                    className="delete-x"
                    onClick={() => remove(t)}
                    aria-label="Delete transaction"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function dayTotal(items: Transaction[], currency: string): string {
  const net = items.reduce(
    (s, t) => s + (t.type === "income" ? Number(t.amount) : -Number(t.amount)),
    0,
  );
  return money(net, currency);
}

function groupByDay(txns: Transaction[]): Record<string, Transaction[]> {
  const out: Record<string, Transaction[]> = {};
  for (const t of txns) {
    const key = formatDate(t.occurred_at);
    (out[key] ??= []).push(t);
  }
  return out;
}
