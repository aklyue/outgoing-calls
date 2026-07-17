import { useEffect, useRef } from "react";

interface UseAppPollersProps {
  loadBalance: () => Promise<void>;
  loadCalls: (reset?: boolean, params?: any) => Promise<void>;
  refreshCallsSnapshot: (params?: any) => Promise<void>;
  refreshPhoneCallsSnapshot: () => Promise<void>;
  filters: any;
}

export const useAppPollers = (props: UseAppPollersProps) => {
  const savedProps = useRef(props);

  useEffect(() => {
    savedProps.current = props;
  });

  useEffect(() => {
    savedProps.current.loadBalance();

    const balanceTimer = setInterval(() => {
      savedProps.current.loadBalance();
    }, 10000);

    const callsPoller = setInterval(() => {
      if (!document.hidden) {
        savedProps.current.refreshCallsSnapshot();
      }
    }, 10000);

    const phonePoller = setInterval(() => {
      if (!document.hidden) {
        savedProps.current.refreshPhoneCallsSnapshot();
      }
    }, 5000);

    return () => {
      clearInterval(balanceTimer);
      clearInterval(callsPoller);
      clearInterval(phonePoller);
    };
  }, []);
};
