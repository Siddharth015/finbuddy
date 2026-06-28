import { categoryColor, money } from "../format";
import type { CategorySlice, TrendPoint } from "../types";

export function DonutChart({
  slices,
  currency,
}: {
  slices: CategorySlice[];
  currency: string;
}) {
  const size = 160;
  const stroke = 26;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const total = slices.reduce((s, c) => s + Number(c.amount), 0);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <svg width={size} height={size} style={{ flexShrink: 0 }}>
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          {total === 0 && (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth={stroke}
            />
          )}
          {slices.map((slice) => {
            const fraction = total > 0 ? Number(slice.amount) / total : 0;
            const dash = fraction * circumference;
            const seg = (
              <circle
                key={slice.category}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={categoryColor(slice.category)}
                strokeWidth={stroke}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
              />
            );
            offset += dash;
            return seg;
          })}
        </g>
        <text
          x="50%"
          y="46%"
          textAnchor="middle"
          fill="var(--tg-hint)"
          fontSize="11"
        >
          Spent
        </text>
        <text
          x="50%"
          y="60%"
          textAnchor="middle"
          fill="var(--tg-text)"
          fontSize="15"
          fontWeight="700"
        >
          {money(total, currency)}
        </text>
      </svg>
      <div className="legend">
        {slices.slice(0, 6).map((s) => (
          <div className="legend-item" key={s.category}>
            <span
              className="dot"
              style={{ background: categoryColor(s.category) }}
            />
            <span className="name">{s.category}</span>
            <span className="pct">{s.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function BarTrend({ points }: { points: TrendPoint[] }) {
  if (points.length === 0) {
    return <p className="muted">No spending yet this month.</p>;
  }
  const max = Math.max(...points.map((p) => Number(p.amount)), 1);
  return (
    <div className="bars">
      {points.map((p) => (
        <div
          key={p.period}
          className="bar"
          style={{ height: `${(Number(p.amount) / max) * 100}%` }}
          title={`${p.period}: ${p.amount}`}
        />
      ))}
    </div>
  );
}
