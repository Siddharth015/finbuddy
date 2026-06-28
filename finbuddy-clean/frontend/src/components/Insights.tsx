import { useEffect, useState } from "react";
import { api } from "../api";
import { currentMonth, money } from "../format";
import { useAsync } from "../hooks";
import { haptic } from "../telegram";
import { ErrorState, MonthPager, SkeletonList } from "../widgets";
import { BarTrend, DonutChart } from "./charts";
import type { MonthlyReport, Space } from "../types";

export function Insights({ space }: { space: Space }) {
  const [month, setMonth] = useState(currentMonth());
  const { data: insight, loading, error, reload } = useAsync(
    () => api.insights(space.id, month),
    [space.id, month],
  );

  const [report, setReport] = useState<MonthlyReport | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportErr, setReportErr] = useState<string | null>(null);

  // A report belongs to a specific month/space — drop it when either changes.
  useEffect(() => {
    setReport(null);
    setReportErr(null);
  }, [space.id, month]);

  const generateReport = () => {
    haptic("light");
    setLoadingReport(true);
    setReportErr(null);
    api
      .report(space.id, month)
      .then(setReport)
      .catch((e) =>
        setReportErr(e instanceof Error ? e.message : "Couldn't generate"),
      )
      .finally(() => setLoadingReport(false));
  };

  return (
    <div>
      <MonthPager month={month} onChange={setMonth} />

      {loading && <SkeletonList rows={5} />}
      {!loading && error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && insight && (
        <>
          <div className="section-title">Spending by category</div>
          <div className="card">
            {insight.categories.length === 0 ? (
              <p className="muted" style={{ margin: 0 }}>
                No spending recorded this month.
              </p>
            ) : (
              <DonutChart
                slices={insight.categories}
                currency={insight.currency}
              />
            )}
          </div>

          <div className="section-title">Daily trend</div>
          <div className="card">
            <BarTrend points={insight.daily_trend} />
            <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
              Total spent: {money(insight.total_spent, insight.currency)}
            </div>
          </div>

          {insight.anomalies.length > 0 && (
            <>
              <div className="section-title">Heads up</div>
              {insight.anomalies.map((a, i) => (
                <div className="anomaly" key={i}>
                  ⚠️ {a}
                </div>
              ))}
            </>
          )}

          <div className="section-title">AI monthly report</div>
          <div className="card">
            {!report && (
              <button
                className="primary"
                onClick={generateReport}
                disabled={loadingReport}
              >
                {loadingReport ? "Thinking…" : "✨ Generate report"}
              </button>
            )}
            {reportErr && (
              <p style={{ color: "var(--red)", fontSize: 13, marginBottom: 0 }}>
                {reportErr}
              </p>
            )}
            {report && (
              <>
                <p style={{ marginTop: 0 }}>{report.summary}</p>
                {report.advice.map((a, i) => (
                  <div className="advice-item" key={i}>
                    <span>💡</span>
                    <span>{a}</span>
                  </div>
                ))}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
