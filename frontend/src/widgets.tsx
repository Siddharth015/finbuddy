import type { ReactNode } from "react";
import { isCurrentMonth, monthLabel, shiftMonth } from "./format";
import { haptic } from "./telegram";

/** Shimmering placeholder block. */
export function Skeleton({
  height = 16,
  width = "100%",
  radius = 8,
  style,
}: {
  height?: number | string;
  width?: number | string;
  radius?: number;
  style?: React.CSSProperties;
}) {
  return (
    <span
      className="skeleton"
      style={{ height, width, borderRadius: radius, ...style }}
    />
  );
}

/** A few stacked skeleton rows that mimic a list/card while loading. */
export function SkeletonList({ rows = 4 }: { rows?: number }) {
  return (
    <div className="card">
      {Array.from({ length: rows }).map((_, i) => (
        <div className="txn" key={i}>
          <Skeleton width={40} height={40} radius={12} />
          <div className="meta" style={{ display: "grid", gap: 6 }}>
            <Skeleton width="55%" height={13} />
            <Skeleton width="35%" height={11} />
          </div>
          <Skeleton width={56} height={14} />
        </div>
      ))}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="state-block">
      <div className="state-emoji">⚠️</div>
      <p className="muted" style={{ margin: "0 0 14px" }}>
        {message}
      </p>
      {onRetry && (
        <button className="ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  emoji,
  title,
  hint,
  action,
}: {
  emoji: string;
  title: string;
  hint?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="state-block">
      <div className="state-emoji">{emoji}</div>
      <div className="state-title">{title}</div>
      {hint && <p className="muted state-hint">{hint}</p>}
      {action}
    </div>
  );
}

/** Prev / current / next month pager. Cannot advance past the current month. */
export function MonthPager({
  month,
  onChange,
}: {
  month: string;
  onChange: (month: string) => void;
}) {
  const atCurrent = isCurrentMonth(month);
  const go = (delta: number) => {
    haptic("light");
    onChange(shiftMonth(month, delta));
  };
  return (
    <div className="month-pager">
      <button className="month-nav" onClick={() => go(-1)} aria-label="Previous month">
        ‹
      </button>
      <span className="month-label">{monthLabel(month)}</span>
      <button
        className="month-nav"
        onClick={() => go(1)}
        disabled={atCurrent}
        aria-label="Next month"
      >
        ›
      </button>
    </div>
  );
}
