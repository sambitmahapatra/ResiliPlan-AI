import { useCallback, useEffect, useState } from "react";

export type ResultState = "idle" | "loading" | "ready" | "empty" | "error";

export interface ApiResult<T> {
  data: T | null;
  state: ResultState;
  error: string | null;
  refetch: () => void;
}

/** Generic data hook with explicit loading/empty/error states (spec §7.4). */
export function useApi<T>(fn: () => Promise<T>, deps: unknown[] = [],
                         isEmpty?: (d: T) => boolean): ApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [state, setState] = useState<ResultState>("loading");
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(() => {
    let alive = true;
    setState("loading"); setError(null);
    fn()
      .then((d) => {
        if (!alive) return;
        setData(d);
        setState(isEmpty && isEmpty(d) ? "empty" : "ready");
      })
      .catch((e) => {
        if (!alive) return;
        setError(e?.message || "Request failed");
        setState("error");
      });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => run(), [run]);
  return { data, state, error, refetch: run };
}
