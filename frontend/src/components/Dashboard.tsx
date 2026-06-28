import { useState } from "react";
import { api } from "../api";
import { categoryIcon, currentMonth, formatDate, money } from "../format";
import { useAsync } from "../hooks";
import { ErrorState, MonthPager, Skeleton, SkeletonList } from "../widgets";
import { Settlement } from "./Settlement";
import type { Space, SpaceSummary, Transaction } from "../types";

export function Dashboard({
  space,
  meId,
  onSeeAll,
  onAdd,
}: {
  space: Space;
  meId: number;
  onSeeAll: () => void;
  onAdd: () => void;
}) {
  const [month, setMonth] = useState(currentMonth());

  const { data, loading, error, reload } = useAsync<
    [SpaceSummary, Transaction[]]
  >(
    () =>
      Promise.all([api.summary(space.id, month), api.transactions(space.id, 5)]),
    [space.id, month],
  );

  const isShared = space.members.length > 1;
  const cur = space.currency;

  return (
    <div>
      <MonthPager month={month} onChange={setMonth} />

      {loading && (
        <>
          <div className="balance-hero">
            <Skeleton
              width="45%"
              height={13}
              style={{ background: "rgba(255,255,255,0.25)" }}
            />
            <Skeleton
              width="60%"
              height={34}
              style={{
                margin: "10px 0 16px",
                background: "rgba(255,255,255,0.25)",
              }}
            />
            <div className="hero-row">
              <Skeleton
                height={48}
                radius={12}
                style={{ background: "rgba(255,255,255,0.2)" }}
              />
              <Skeleton
                height={48}
                radius={12}
                style={{ background: "rgba(255,255,255,0.2)" }}
              />
            </div>
          </div>
          <SkeletonList rows={4} />
        </>
      )}

      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && data && (
        <DashboardContent
          summary={data[0]}
          recent={data[1]}
          space={space}
          meId={meId}
          isShared={isShared}
          cur={cur}
          onSeeAll={onSeeAll}
          onAdd={onAdd}
        />
      )}
    </div>
  );
}

function DashboardContent({
  summary,
  recent,
  space,
  meId,
  isShared,
  cur,
  onSeeAll,
  onAdd,
}: {
  summary: SpaceSummary;
  recent: Transaction[];
  space: Space;
  meId: number;
  isShared: boolean;
  cur: string;
  onSeeAll: () => void;
  onAdd: () => void;
}) {
  const net = Number(summary.net);

  return (
    <>
      <div className="balance-hero">
        <div className="label">Net balance</div>
        <div className={`value ${net < 0 ? "neg" : ""}`}>{money(net, cur)}</div>
        <div className="hero-row">
          <div className="hero-pill">
            <div className="k">↑ Income</div>
            <div className="v">{money(summary.total_income, cur)}</div>
          </div>
          <div className="hero-pill">
            <div className="k">↓ Spent</div>
            <div className="v">{money(summary.total_spent, cur)}</div>
          </div>
        </div>
      </div>

      {isShared && <Settlement space={space} meId={meId} />}

      <div className="stat-grid">
        <div className="stat">
          <div className="k">🏦 Accounts</div>
          <div className="v">{money(summary.accounts_balance, cur)}</div>
        </div>
        <div className="stat">
          <div className="k">📈 Investments</div>
          <div className="v">{money(summary.investments_value, cur)}</div>
        </div>
      </div>

      <div className="section-row">
        <div className="section-title" style={{ margin: 0 }}>
          Recent activity
        </div>
        {recent.length > 0 && (
          <button className="link-btn" onClick={onSeeAll}>
            See all
          </button>
        )}
      </div>

      <div className="card">
        {recent.length === 0 ? (
          <div className="state-block compact">
            <div className="state-emoji">🪙</div>
            <div className="state-title">No activity yet</div>
            <p className="muted state-hint">
              Tap + to add one, or message the bot like <code>1000-zomato</code>.
            </p>
            <button
              className="primary"
              onClick={onAdd}
              style={{ maxWidth: 220 }}
            >
              Add your first expense
            </button>
          </div>
        ) : (
          recent.map((t) => (
            <div className="txn" key={t.id}>
              <div className="icon">{categoryIcon(t.category)}</div>
              <div className="meta">
                <div className="t">
                  {t.note || t.category}
                  {t.scope === "shared" && (
                    <span className="badge">shared</span>
                  )}
                </div>
                <div className="s">
                  {t.category} · {formatDate(t.occurred_at)}
                </div>
              </div>
              <div className={`amt ${t.type}`}>
                {t.type === "income" ? "+" : "−"}
                {money(t.amount, cur)}
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}
