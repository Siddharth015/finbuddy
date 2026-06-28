// Lightweight, client-side mirror of the backend parser + categorizer.
// Used purely to give the user an instant preview while typing — the server
// remains the source of truth.

const SUFFIX_MULTIPLIERS: Record<string, number> = {
  k: 1_000,
  m: 1_000_000,
  l: 100_000, // lakh
  lakh: 100_000,
  cr: 10_000_000,
};

const INCOME_HINTS = [
  "salary",
  "income",
  "credited",
  "credit",
  "refund",
  "cashback",
  "bonus",
  "interest",
  "dividend",
  "received",
];

const CATEGORY_KEYWORDS: Record<string, string[]> = {
  food: [
    "zomato", "swiggy", "restaurant", "dinner", "lunch", "breakfast", "cafe",
    "coffee", "pizza", "burger", "food", "snack", "tea", "dominos", "mcd",
  ],
  groceries: [
    "grocery", "groceries", "bigbasket", "blinkit", "zepto", "dmart", "vegetables",
    "milk", "supermarket", "kirana",
  ],
  transport: [
    "uber", "ola", "auto", "taxi", "cab", "petrol", "fuel", "diesel", "metro",
    "bus", "train", "rapido", "parking", "toll",
  ],
  shopping: [
    "amazon", "flipkart", "myntra", "shopping", "clothes", "shoes", "ajio",
    "nykaa", "mall",
  ],
  entertainment: [
    "movie", "netflix", "spotify", "prime", "hotstar", "game", "concert",
    "bookmyshow", "youtube",
  ],
  bills: [
    "electricity", "water", "gas", "wifi", "internet", "broadband", "bill",
    "recharge", "mobile", "phone", "dth",
  ],
  rent: ["rent", "lease", "maintenance"],
  health: [
    "medicine", "pharmacy", "doctor", "hospital", "gym", "medical", "apollo",
    "clinic", "1mg",
  ],
  travel: ["flight", "hotel", "trip", "airbnb", "vacation", "makemytrip", "irctc"],
  education: ["course", "book", "tuition", "school", "college", "fees", "udemy"],
  investment: ["sip", "stock", "mutual", "invest", "shares", "fd", "gold"],
};

export interface ParsedPreview {
  amount: number;
  note: string;
  type: "expense" | "income";
  category: string;
}

export function categorize(note: string): string {
  const low = note.toLowerCase();
  for (const [category, words] of Object.entries(CATEGORY_KEYWORDS)) {
    if (words.some((w) => low.includes(w))) return category;
  }
  return "other";
}

/**
 * Returns a best-effort preview of what the server will record, or null if
 * the text does not yet contain a parseable amount.
 */
export function previewExpense(text: string): ParsedPreview | null {
  const raw = text.trim();
  if (!raw) return null;

  const match = raw.match(
    /([+\-])?\s*(\d+(?:[.,]\d+)?)\s*(k|m|l|lakh|cr)?/i,
  );
  if (!match) return null;

  const sign = match[1];
  let amount = Number(match[2].replace(",", "."));
  const suffix = match[3]?.toLowerCase();
  if (suffix && SUFFIX_MULTIPLIERS[suffix]) {
    amount *= SUFFIX_MULTIPLIERS[suffix];
  }
  if (!Number.isFinite(amount) || amount <= 0) return null;

  // Note = everything that isn't the amount token / separators.
  let note = (raw.slice(0, match.index) + raw.slice((match.index ?? 0) + match[0].length))
    .replace(/^[\s\-–—:|]+|[\s\-–—:|]+$/g, "")
    .trim();
  note = note.replace(/\s+/g, " ");

  const low = raw.toLowerCase();
  const isIncome =
    sign === "+" || INCOME_HINTS.some((w) => low.includes(w));

  const category = isIncome ? "income" : categorize(note || low);

  return {
    amount,
    note: note || category,
    type: isIncome ? "income" : "expense",
    category,
  };
}
