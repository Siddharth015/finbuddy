import { useEffect, useRef } from "react";
import { tg } from "./telegram";

export const hasMainButton = !!tg?.MainButton;
export const hasBackButton = !!tg?.BackButton;

/**
 * Drives Telegram's native MainButton (the big bottom CTA) for the lifetime
 * of the component. Falls back to no-op outside Telegram, where screens render
 * their own in-DOM button instead.
 */
export function useMainButton(opts: {
  text: string;
  onClick: () => void;
  visible?: boolean;
  enabled?: boolean;
  progress?: boolean;
}): void {
  const { text, onClick, visible = true, enabled = true, progress = false } = opts;
  const cb = useRef(onClick);
  cb.current = onClick;

  useEffect(() => {
    const mb = tg?.MainButton;
    if (!mb) return;
    const handler = () => cb.current();
    mb.onClick(handler);
    return () => {
      mb.offClick(handler);
      mb.hide();
    };
  }, []);

  useEffect(() => {
    const mb = tg?.MainButton;
    if (!mb) return;
    mb.setText(text);
    if (enabled) mb.enable();
    else mb.disable();
    if (progress) mb.showProgress();
    else mb.hideProgress();
    if (visible) mb.show();
    else mb.hide();
  }, [text, visible, enabled, progress]);
}

/** Shows Telegram's native BackButton and routes it to `onClick`. */
export function useBackButton(onClick: () => void, visible = true): void {
  const cb = useRef(onClick);
  cb.current = onClick;

  useEffect(() => {
    const bb = tg?.BackButton;
    if (!bb) return;
    const handler = () => cb.current();
    bb.onClick(handler);
    if (visible) bb.show();
    return () => {
      bb.offClick(handler);
      bb.hide();
    };
  }, [visible]);
}
