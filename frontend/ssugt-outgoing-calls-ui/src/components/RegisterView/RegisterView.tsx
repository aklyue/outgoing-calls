import React, { useEffect, useState } from "react";
import {
  Box,
  Card,
  Typography,
  useTheme,
  Snackbar,
  Alert,
  Slide,
} from "@mui/material";
import { RegisterForm } from "../RegisterForm";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "../../store";
import { clearError, register } from "../../store/api/userSlice";
import { motion } from "framer-motion";

const RegisterView: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const theme = useTheme();
  const { isLoading, error } = useSelector((state: RootState) => state.user);

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error",
  });

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  useEffect(() => {
    if (error) {
      setSnackbar({
        open: true,
        message: error,
        severity: "error",
      });
    }
  }, [error]);

  const handleRegister = async (data: any) => {
    dispatch(clearError());
    const result = await dispatch(
      register({
        username: data.login,
        password: data.password,
        role: data.role,
      }),
    );

    if (register.fulfilled.match(result)) {
      dispatch({
        type: "user/registration/fulfilled",
        payload: {
          targetLogin: data.login,
          role: data.role,
        },
      });
      setSnackbar({
        open: true,
        message: "Регистрация прошла успешно",
        severity: "success",
      });
    }
  };

  const handleClose = () => {
    setSnackbar({ ...snackbar, open: false });
    if (snackbar.severity === "error") {
      dispatch(clearError());
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        p: 2,
      }}
    >
      <motion.div style={{ width: "100%", maxWidth: 480 }}>
        <Card
          elevation={0}
          sx={{
            p: { xs: 3, md: 5 },
            borderRadius: 8,
            background: "rgba(255, 255, 255, 0.8)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(255, 255, 255, 0.3)",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.1)",
          }}
        >
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h4"
              fontWeight={800}
              sx={{
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                letterSpacing: "-1px",
              }}
            >
              Создать аккаунт
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 1, opacity: 0.8 }}
            >
              Заполните данные для доступа к системе
            </Typography>
          </Box>

          <RegisterForm onSubmit={handleRegister} loading={isLoading} />
        </Card>
      </motion.div>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        TransitionComponent={(props) => <Slide {...props} direction="up" />}
      >
        <Alert
          onClose={handleClose}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: "100%", borderRadius: 3, fontWeight: 500 }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RegisterView;
