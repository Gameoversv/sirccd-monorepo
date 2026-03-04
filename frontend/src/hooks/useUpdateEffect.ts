import { useEffect, useRef } from 'react';

/**
 * Hook that runs effect only after first render (skips mount)
 */
export function useUpdateEffect(
  effect: React.EffectCallback,
  deps?: React.DependencyList
) {
  const isMounted = useRef(false);

  useEffect(() => {
    if (isMounted.current) {
      return effect();
    } else {
      isMounted.current = true;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
