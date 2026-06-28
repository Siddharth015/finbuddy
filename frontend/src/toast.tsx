import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { haptic } from "./telegram";

interface ToastState {
  id: number;
  message: string;
  undo?: () => void;
}

interface ToastApi {
  /** Simple transient message. */
  show: (message: string) => void;
  /**
   * Show an undoable action. The destructive side-effect (`onCommit`) only
   * runs after the toast times out without the user tapping "Undo".
   */
  showUndo: (
    message: string,
    handlers: { onCommit: () => void; onUndo: () => void; duration?: number },
  ) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within <ToastProvider>");
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingCommit = useRef<(() => void) | null>(null);
  const idRef = useRef(0);

  const clearTimer = () => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };

  // Flush any in-flight commit immediately (e.g. when replaced or unmounting).
  const flush = useCallback(() => {
    clearTimer();
    if (pendingCommit.current) {
      pendingCommit.current();
      pendingCommit.current = null;
    }
  }, []);

  const show = useCallback(
    (message: string) => {
      flush();
      const id = ++idRef.current;
      setToast({ id, message });
      timer.current = setTimeout(() => {
        setToast((t) => (t?.id === id ? null : t));
      }, 2600);
    },
    [flush],
  );

  const showUndo = useCallback<ToastApi["showUndo"]>(
    (message, { onCommit, onUndo, duration = 4500 }) => {
      flush();
      const id = ++idRef.current;
      pendingCommit.current = onCommit;
      setToast({
        id,
        message,
        undo: () => {
          clearTimer();
          pendingCommit.current = null;
          onUndo();
          setToast((t) => (t?.id === id ? null : t));
          haptic("light");
        },
      });
      timer.current = setTimeout(() => {
        if (pendingCommit.current) {
          pendingCommit.current();
          pendingCommit.current = null;
        }
        setToast((t) => (t?.id === id ? null : t));
      }, duration);
    },
    [flush],
  );

  useEffect(() => () => flush(), [flush]);

  return (
    <ToastContext.Provider value={{ show, showUndo }}>
      {children}
      {toast && (
        <div className="toast" role="status">
          <span className="toast-msg">{toast.message}</span>
          {toast.undo && (
            <button className="toast-undo" onClick={toast.undo}>
              Undo
            </button>
          )}
        </div>
      )}
    </ToastContext.Provider>
  );
}
