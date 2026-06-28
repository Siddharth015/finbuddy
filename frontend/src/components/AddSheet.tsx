import { useMemo, useState } from "react";
import { api } from "../api";
import { categoryIcon, money } from "../format";
import { previewExpense } from "../parse";
import { haptic } from "../telegram";
import { hasMainButton, useBackButton, useMainButton } from "../telegramButtons";
import type { Space } from "../types";

const QUICK_CATEGORIES = [
  "food",
  "groceries",
  "transport",
  "shopping",
  "bills",
  "rent",
  "health",
  "entertainment",
];

export function AddSheet({
  space,
  onClose,
  onAdded,
}: {
  space: Space;
  onClose: () => void;
  onAdded: () => void;
}) {
  const [raw, setRaw] = useState("");
  const [type, setType] = useState<"expense" | "income">("expense");
  const [scope, setScope] = useState<"personal" | "shared">("personal");
  const [category, setCategory] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isShared = space.members.length > 1;
  const memberCount = space.members.length || 1;

  const preview = useMemo(() => previewExpense(raw), [raw]);
  const effectiveCategory =
    category || (type === "income" ? "income" : preview?.category ?? "");
  const canSubmit = !!preview && !submitting;

  const submit = async () => {
    setError(null);
    const text = raw.trim();
    if (!preview) {
      setError("Type something like 1000-zomato");
      return;
    }
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        raw_text: text,
        type,
        scope: type === "expense" ? scope : "personal",
      };
      if (category) payload.category = category;
      await api.addTransaction(space.id, payload);
      haptic("success");
      onAdded();
      onClose();
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  useBackButton(onClose);
  useMainButton({
    text: submitting
      ? "Adding…"
      : type === "income"
        ? "Add income"
        : "Add expense",
    onClick: submit,
    enabled: canSubmit,
    progress: submitting,
  });

  const showShared = type === "expense" && isShared && scope === "shared";
  const perHead = preview ? preview.amount / memberCount : 0;

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-grabber" />
        <h2>Add transaction</h2>

        <div className="segmented">
          <button
            className={type === "expense" ? "active" : ""}
            onClick={() => {
              haptic("select");
              setType("expense");
            }}
          >
            💸 Expense
          </button>
          <button
            className={type === "income" ? "active" : ""}
            onClick={() => {
              haptic("select");
              setType("income");
            }}
          >
            💰 Income
          </button>
        </div>

        <label className="field">Amount &amp; note</label>
        <input
          autoFocus
          className="big-input"
          placeholder="e.g. 1000-zomato, 1.2k uber, +50000 salary"
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && canSubmit && submit()}
        />

        {/* Live preview of what the bot will record. */}
        <div className={`parse-preview ${preview ? "ready" : "pending"}`}>
          {preview ? (
            <>
              <div className="pp-icon">{categoryIcon(effectiveCategory)}</div>
              <div className="pp-meta">
                <div className="pp-note">{preview.note || effectiveCategory}</div>
                <div className="pp-cat">{effectiveCategory}</div>
              </div>
              <div className={`pp-amt ${type}`}>
                {type === "income" ? "+" : "−"}
                {money(preview.amount, space.currency)}
              </div>
            </>
          ) : (
            <span className="muted" style={{ fontSize: 13 }}>
              Start typing an amount to see a preview…
            </span>
          )}
        </div>

        {type === "expense" && isShared && (
          <>
            <label className="field">Who is this for?</label>
            <div className="segmented">
              <button
                className={scope === "personal" ? "active" : ""}
                onClick={() => {
                  haptic("select");
                  setScope("personal");
                }}
              >
                🙋 Just me
              </button>
              <button
                className={scope === "shared" ? "active" : ""}
                onClick={() => {
                  haptic("select");
                  setScope("shared");
                }}
              >
                👥 Shared
              </button>
            </div>
            {showShared && preview && (
              <p className="split-hint">
                Split equally across {memberCount} people ·{" "}
                <strong>{money(perHead, space.currency)}</strong> each
              </p>
            )}
          </>
        )}

        {type === "expense" && (
          <>
            <label className="field">
              Category{" "}
              <span className="muted">
                {category ? "" : "· auto-detected, tap to override"}
              </span>
            </label>
            <div className="chip-row">
              {QUICK_CATEGORIES.map((c) => (
                <button
                  key={c}
                  className={`chip ${
                    (category || preview?.category) === c ? "active" : ""
                  }`}
                  onClick={() => {
                    haptic("select");
                    setCategory(category === c ? "" : c);
                  }}
                >
                  {c}
                </button>
              ))}
            </div>
          </>
        )}

        {error && <p style={{ color: "var(--red)", fontSize: 13 }}>{error}</p>}

        {!hasMainButton && (
          <button className="primary" onClick={submit} disabled={!canSubmit}>
            {submitting
              ? "Adding…"
              : type === "income"
                ? "Add income"
                : "Add expense"}
          </button>
        )}
      </div>
    </div>
  );
}
