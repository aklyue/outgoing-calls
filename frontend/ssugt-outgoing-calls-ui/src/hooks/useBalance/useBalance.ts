import { useCallback, useMemo, useState } from "react";

export const useBalance = ({
  getBalance,
}: {
  getBalance: () => Promise<any>;
}) => {
  const [balance, setBalance] = useState<number>(0);
  const loadBalance = useCallback(async () => {
    try {
      const b = await getBalance();
      setBalance(b || 0);
    } catch (e) {}
  }, [getBalance]);

  const balanceText = useMemo(() => {
    return (balance ?? 0).toLocaleString("ru-RU", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }, [balance]);

  return {
    balance,
    loadBalance,
    balanceText,
  };
};
