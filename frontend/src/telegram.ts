// Thin wrapper around the Telegram Web App SDK injected by telegram-web-app.js.

export const tg = window.Telegram?.WebApp;

export function initTelegram(): void {
  if (tg) {
    tg.ready();
    tg.expand();
    applyTheme();
    tg.onEvent?.("themeChanged", applyTheme);
  } else {
    // Browser dev fallback: seed the neutral overlay vars so the dark theme
    // looks correct outside Telegram too.
    const root = document.documentElement;
    root.style.setProperty("--hairline", "rgba(255, 255, 255, 0.07)");
    root.style.setProperty("--chip", "rgba(255, 255, 255, 0.06)");
    root.style.setProperty("--chip-strong", "rgba(255, 255, 255, 0.10)");
    root.style.setProperty("--skeleton", "rgba(255, 255, 255, 0.06)");
    root.style.setProperty("--skeleton-shine", "rgba(255, 255, 255, 0.12)");
  }
}

export function getInitData(): string {
  // Inside Telegram this is signed initData. For browser development you can
  // set VITE_DEV_INIT_DATA to a captured initData string.
  return tg?.initData || import.meta.env.VITE_DEV_INIT_DATA || "";
}

export function haptic(
  type: "success" | "error" | "warning" | "light" | "medium" | "heavy" | "select" = "light",
): void {
  const h = tg?.HapticFeedback;
  if (!h) return;
  if (type === "success" || type === "error" || type === "warning") {
    h.notificationOccurred(type);
  } else if (type === "select") {
    h.selectionChanged?.();
  } else {
    h.impactOccurred(type);
  }
}

export function colorScheme(): "light" | "dark" {
  return tg?.colorScheme ?? "dark";
}

function applyTheme(): void {
  const root = document.documentElement;
  const scheme = tg?.colorScheme ?? "dark";
  const p = tg?.themeParams ?? {};

  const map: Record<string, string | undefined> = {
    "--tg-bg": p.bg_color,
    "--tg-text": p.text_color,
    "--tg-hint": p.hint_color,
    "--tg-card": p.secondary_bg_color,
    "--tg-accent": p.button_color,
    "--tg-accent-text": p.button_text_color,
  };
  for (const [key, value] of Object.entries(map)) {
    if (value) root.style.setProperty(key, value);
  }

  // Neutral overlay tints that read correctly on both light and dark
  // surfaces (the previous hardcoded white overlays vanished on light bg).
  if (scheme === "light") {
    root.style.setProperty("--hairline", "rgba(0, 0, 0, 0.08)");
    root.style.setProperty("--chip", "rgba(0, 0, 0, 0.05)");
    root.style.setProperty("--chip-strong", "rgba(0, 0, 0, 0.08)");
    root.style.setProperty("--skeleton", "rgba(0, 0, 0, 0.06)");
    root.style.setProperty("--skeleton-shine", "rgba(0, 0, 0, 0.10)");
  } else {
    root.style.setProperty("--hairline", "rgba(255, 255, 255, 0.07)");
    root.style.setProperty("--chip", "rgba(255, 255, 255, 0.06)");
    root.style.setProperty("--chip-strong", "rgba(255, 255, 255, 0.10)");
    root.style.setProperty("--skeleton", "rgba(255, 255, 255, 0.06)");
    root.style.setProperty("--skeleton-shine", "rgba(255, 255, 255, 0.12)");
  }
  document.documentElement.dataset.theme = scheme;

  if (p.bg_color) {
    tg?.setHeaderColor?.(p.bg_color);
    tg?.setBackgroundColor?.(p.bg_color);
  }
}
