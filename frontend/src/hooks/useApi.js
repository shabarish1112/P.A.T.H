import { useCallback, useEffect, useState } from 'react';

export function useApi(fetcher, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0);

  const retry = useCallback(() => setVersion((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.resolve()
      .then(() => {
        if (controller.signal.aborted) return;
        setLoading(true);
        setError(null);
        return fetcher(controller.signal);
      })
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((requestError) => {
        if (!controller.signal.aborted && requestError?.name !== 'AbortError')
          setError(requestError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [...dependencies, version]); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, setData, loading, error, retry };
}
