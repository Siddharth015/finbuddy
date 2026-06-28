import { useCallback, useEffect, useRef, useState } from "react";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Standardised data-fetching hook so every screen gets consistent
 * loading / error / retry behaviour instead of bare spinners and silent
 * failures.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const aliveRef = useRef(true);

  const run = useCallback(() => {
    setLoading(true);
    setError(null);
    fnRef
      .current()
      .then((d) => aliveRef.current && setData(d))
      .catch(
        (e) =>
          aliveRef.current &&
          setError(e instanceof Error ? e.message : "Something went wrong"),
      )
      .finally(() => aliveRef.current && setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    aliveRef.current = true;
    run();
    return () => {
      aliveRef.current = false;
    };
  }, [run]);

  return { data, loading, error, reload: run };
}
