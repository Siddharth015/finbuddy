import { api } from "../api";
import { money } from "../format";
import { useAsync } from "../hooks";
import { Skeleton } from "../widgets";
import type { Space } from "../types";

/**
 * "Who owes whom" for shared spaces — the headline feature for couples and
 * roommates. Only shared-scope expenses are settled.
 */
export function Settlement({ space, meId }: { space: Space; meId: number }) {
  const { data, loading, error } = useAsync(
    () => api.settlement(space.id),
    [space.id],
  );

  if (loading) {
    return (
      <div className="card">
        <Skeleton width="40%" height={14} style={{ marginBottom: 12 }} />
        <Skeleton width="70%" height={12} />
      </div>
    );
  }

  // Settlement is a nice-to-have card: if it errors, stay quiet rather than
  // shouting on the home screen.
  if (error || !data) return null;

  const myBalance = Number(data.balances[meId] ?? 0);
  const cur = data.currency;
  const settled = Math.abs(myBalance) < 0.01;

  return (
    <div className="card settle-card">
      <div className="settle-head">
        <span className="settle-title">🤝 Settle up</span>
        <span
          className={`settle-net ${
            settled ? "" : myBalance > 0 ? "pos" : "neg"
          }`}
        >
          {settled
            ? "All settled"
            : myBalance > 0
              ? `You're owed ${money(myBalance, cur)}`
              : `You owe ${money(Math.abs(myBalance), cur)}`}
        </span>
      </div>

      {data.transfers.length === 0 ? (
        <p className="muted" style={{ margin: "10px 0 0" }}>
          {settled
            ? "Everyone is square — no payments needed. 🎉"
            : "No shared expenses to settle yet."}
        </p>
      ) : (
        <div className="settle-list">
          {data.transfers.map((t, i) => {
            const involvesMe =
              t.from_user.id === meId || t.to_user.id === meId;
            let label: string;
            let tone = "";
            if (t.from_user.id === meId) {
              label = `You pay ${t.to_user.first_name}`;
              tone = "neg";
            } else if (t.to_user.id === meId) {
              label = `${t.from_user.first_name} pays you`;
              tone = "pos";
            } else {
              label = `${t.from_user.first_name} → ${t.to_user.first_name}`;
            }
            return (
              <div className={`settle-row ${involvesMe ? "mine" : ""}`} key={i}>
                <span className="settle-row-label">{label}</span>
                <span className={`settle-row-amt ${tone}`}>
                  {money(t.amount, cur)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
