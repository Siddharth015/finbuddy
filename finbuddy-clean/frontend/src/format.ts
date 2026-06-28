export const CATEGORY_ICONS: Record<string, string> = {
  food: "🍔",
  groceries: "🛒",
  transport: "🚕",
  shopping: "🛍️",
  entertainment: "🎬",
  bills: "💡",
  rent: "🏠",
  health: "💊",
  travel: "✈️",
  education: "📚",
  investment: "📈",
  income: "💰",
  other: "📦",
};

export function categoryIcon(category: string): string {
  return CATEGORY_ICONS[category] ?? CATEGORY_ICONS.other;
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  INR: "₹",
  USD: "$",
  EUR: "€",
  GBP: "£",
  JPY: "¥",
  AUD: "A$",
  CAD: "C$",
  SGD: "S$",
  AED: "AED ",
  CHF: "CHF ",
};

export function currencySymbol(currency: string): string {
  return CURRENCY_SYMBOLS[currency.toUpperCase()] ?? `${currency} `;
}

export function money(value: string | number, currency = ""): string {
  const num = typeof value === "string" ? Number(value) : value;
  const safe = Number.isFinite(num) ? num : 0;
  const formatted = Math.abs(safe).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  const sign = safe < 0 ? "-" : "";
  if (!currency) return `${sign}${formatted}`;
  return `${sign}${currencySymbol(currency)}${formatted}`;
}

/** Signed money, e.g. +₹1,200 / -₹450 — handy for net values and P&L. */
export function signedMoney(value: string | number, currency = ""): string {
  const num = typeof value === "string" ? Number(value) : value;
  const safe = Number.isFinite(num) ? num : 0;
  const sign = safe > 0 ? "+" : safe < 0 ? "-" : "";
  return `${sign}${money(Math.abs(safe), currency)}`;
}

export function percent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
  });
}

// --- Month helpers (YYYY-MM) -------------------------------------------------

export function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function monthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1, 1);
  const now = new Date();
  const opts: Intl.DateTimeFormatOptions =
    y === now.getFullYear()
      ? { month: "long" }
      : { month: "long", year: "numeric" };
  return d.toLocaleDateString(undefined, opts);
}

export function isCurrentMonth(month: string): boolean {
  return month === currentMonth();
}

// Deterministic color per category for the chart legend.
export function categoryColor(category: string): string {
  const palette = [
    "#6366f1", "#ec4899", "#f59e0b", "#10b981", "#3b82f6",
    "#ef4444", "#8b5cf6", "#14b8a6", "#f97316", "#84cc16",
    "#06b6d4", "#a855f7", "#64748b",
  ];
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = (hash * 31 + category.charCodeAt(i)) % palette.length;
  }
  return palette[hash];
}
