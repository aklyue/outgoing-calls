import { useCallback, useEffect, useRef, useState } from "react";
import type { View } from "../../types/View";
import type { Category } from "../../api/api";

interface UsePhoneCallsProps {
  getPhoneCalls: (
    callId: string,
    offset?: number,
    limit?: number,
  ) => Promise<any>;
  activeViewRef: React.RefObject<View>;
  patchCall: (
    id: string,
    data: {
      is_paused?: boolean | undefined;
      name?: string | undefined;
      retry_limit?: number | undefined;
      schedule?: any[] | undefined;
      tts_type?: string | undefined;
      categories?: Category[] | undefined;
    },
  ) => Promise<any>;
  setCalls: (value: React.SetStateAction<any[]>) => void;
}

const phoneCallsLimit = 100;

export const usePhoneCalls = ({
  getPhoneCalls,
  activeViewRef,
  patchCall,
  setCalls,
}: UsePhoneCallsProps) => {
  const [currentCall, setCurrentCall] = useState<any>(null);

  const [phoneCalls, setPhoneCalls] = useState<any[]>([]);
  const [phoneCallsLoading, setPhoneCallsLoading] = useState(false);
  const [phoneCallsHasMore, setPhoneCallsHasMore] = useState(true);
  const [phoneCallsOffset, setPhoneCallsOffset] = useState(0);

  const phoneRefreshInFlight = useRef(false);
  const phoneCallsOffsetRef = useRef(phoneCallsOffset);
  const currentCallRef = useRef(currentCall);

  const loadPhoneCalls = useCallback(
    async (reset = false) => {
      const call = currentCallRef.current;
      if (!call || phoneCallsLoading) return;
      setPhoneCallsLoading(true);
      try {
        const offset = reset ? 0 : phoneCallsOffset;
        const page = await getPhoneCalls(call.id, offset, phoneCallsLimit);
        setPhoneCalls((prev) => (reset ? page : [...prev, ...page]));
        setPhoneCallsOffset((prev) => (reset ? 0 : prev) + page.length);
        setPhoneCallsHasMore(page.length === phoneCallsLimit);
      } finally {
        setPhoneCallsLoading(false);
      }
    },
    [getPhoneCalls, phoneCallsLoading, phoneCallsOffset],
  );

  const refreshPhoneCallsSnapshot = useCallback(async () => {
    const call = currentCallRef.current;
    if (
      activeViewRef.current !== "calls" ||
      phoneRefreshInFlight.current ||
      !call
    )
      return;
    const offset = phoneCallsOffsetRef.current;
    if (offset <= 0) return;

    phoneRefreshInFlight.current = true;
    try {
      const fresh = await getPhoneCalls(call.id, 0, offset);
      setPhoneCalls(fresh);
    } finally {
      phoneRefreshInFlight.current = false;
    }
  }, [getPhoneCalls]);

  const togglePaused = async (val: boolean) => {
    if (!currentCall) return;
    const updated = await patchCall(currentCall.id, { is_paused: val });
    setCurrentCall(updated);
    setCalls((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  };

  const onCallDeleted = (payload: { id: string; call: any }) => {
    const { id } = payload;
    setCalls((prev) => prev.filter((c) => c.id !== id));
    if (currentCall?.id === id) {
      setCurrentCall(null);
      setPhoneCalls([]);
    }
  };

  const selectCall = useCallback((call: any) => {
    const isSameCall = currentCallRef.current?.id === call?.id;

    currentCallRef.current = call;
    setCurrentCall(call);

    if (!isSameCall) {
      setPhoneCalls([]);
      setPhoneCallsOffset(0);
      phoneCallsOffsetRef.current = 0;
      setPhoneCallsHasMore(true);
    }
  }, []);

  useEffect(() => {
    if (currentCall?.id) loadPhoneCalls(true);
  }, [currentCall?.id]);

  useEffect(() => {
  if (currentCall) {
    setCurrentCall((prev: any) => {
      if (!prev) return null;
      return prev; 
    });
  }
}, [currentCall?.updated_at]);

  return {
    currentCall,
    currentCallRef,
    phoneCalls,
    setPhoneCalls,
    phoneCallsLoading,
    phoneCallsHasMore,
    loadPhoneCalls,
    refreshPhoneCallsSnapshot,
    phoneCallsOffsetRef,
    phoneCallsOffset,
    setPhoneCallsOffset,
    togglePaused,
    onCallDeleted,
    selectCall,
  };
};
