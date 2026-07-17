import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import type { AppDispatch, RootState } from "../../store";
import { useEffect, useState } from "react";
import { clearError, login } from "../../store/api/userSlice";

export const useLogin = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();

  const { isLoading, error, isAuthenticated } = useSelector(
    (state: RootState) => state.user,
  );

  const [openSnackbar, setOpenSnackbar] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (error) {
      setOpenSnackbar(true);
    }
  }, [error]);

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
    dispatch(clearError());
  };

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleLogin = async (username: string, password: string) => {
    dispatch(clearError());
    const r = await dispatch(login({ username, password }));
    if (r) {
      dispatch({ type: "user/login/success", payload: { username } });
    }
  };

  return {
    isLoading,
    handleLogin,
    openSnackbar,
    handleCloseSnackbar,
    error,
  };
};
