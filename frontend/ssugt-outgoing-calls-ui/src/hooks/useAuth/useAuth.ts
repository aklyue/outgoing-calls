import { useCallback, useMemo } from "react";
import {
  logout as logoutThunk,
  fetchCurrentUser,
} from "../../store/api/userSlice";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "../../store";

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { user, isLoading, isAuthenticated } = useSelector(
    (state: RootState) => state.user,
  );

  const logout = useCallback(async () => {
    await dispatch(logoutThunk());
  }, [dispatch]);

  const refreshUser = useCallback(async () => {
    await dispatch(fetchCurrentUser());
  }, [dispatch]);

  const isAdmin = useMemo(() => user?.role === "admin", [user]);
  const isOwner = useMemo(() => user?.role === "owner", [user]);

  return {
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    isOwner,
    logout,
    refreshUser,
  };
};
