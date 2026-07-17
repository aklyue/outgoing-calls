import { useCallback, useRef, useState } from "react";
import type { View } from "../../types/View";

interface UseCallsProps {
  // Обновили сигнатуру: теперь принимает фильтры и возвращает объект с items и total
  getCalls: (
    offset?: number,
    limit?: number,
    filters?: any,
  ) => Promise<{ items: any[]; total: number }>;
  activeViewRef: React.RefObject<View>;
}

const callsLimit = 10; // Можно оставить 50, если это список

export const useCalls = ({ getCalls, activeViewRef }: UseCallsProps) => {
  const [calls, setCalls] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState(0); // Новое состояние для общего количества
  const [callsLoading, setCallsLoading] = useState(false);
  const [callsOffset, setCallsOffset] = useState(0);

  const callsOffsetRef = useRef(callsOffset);
  callsOffsetRef.current = callsOffset;

  // Добавляем состояние фильтров
  const [filters, setFilters] = useState({
    call_name: "",
    username: "",
    role: "",
  });

  const callsRefreshInFlight = useRef(false);

  const loadCalls = useCallback(
    async (reset = false, newFilters = {}) => {
      if (callsLoading) return;
      setCallsLoading(true);

      try {
        const currentFilters = { ...filters, ...newFilters };
        const offset = reset ? 0 : callsOffset;

        // Деструктурируем ответ от API
        const { items, total } = await getCalls(
          offset,
          callsLimit,
          currentFilters,
        );

        setCalls((prev) => (reset ? items : [...prev, ...items]));
        setTotalCount(total);
        setCallsOffset((prev) => (reset ? 0 : prev) + items.length);

        if (reset) setFilters(currentFilters);
      } catch (e) {
        console.error("Failed to load calls", e);
      } finally {
        setCallsLoading(false);
      }
    },
    [getCalls, callsLoading, callsOffset, filters],
  );

  const refreshCallsSnapshot = useCallback(
    async (params?: any) => {
      if (activeViewRef.current !== "calls" || callsRefreshInFlight.current)
        return;

      const currentOffset = params?.offset ?? 0;
      const currentLimit = params?.limit ?? (calls.length || callsLimit);
      const currentFilters = params?.filters ?? filters;

      callsRefreshInFlight.current = true;
      try {
        const { items } = await getCalls(
          currentOffset,
          currentLimit,
          currentFilters,
        );

        setCalls((prev) => {
          if (prev.length && prev[0]?.id !== items[0]?.id) return items;

          return prev.map((oldCall) => {
            const updated = items.find((f) => f.id === oldCall.id);
            return updated ? { ...oldCall, ...updated } : oldCall;
          });
        });
      } finally {
        callsRefreshInFlight.current = false;
      }
    },
    [getCalls, calls.length, filters, activeViewRef],
  );

  return {
    calls,
    setCalls,
    totalCount,
    callsLoading,
    callsHasMore: calls.length < totalCount,
    loadCalls,
    refreshCallsSnapshot,
    setFilters,
    filters,
    callsOffset,
    callsOffsetRef,
  };
};
