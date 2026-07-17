import React from "react";
import {
  Card,
  Snackbar,
  Alert,
  Fade,
  Slide,
  Box,
  CircularProgress,
  Typography,
} from "@mui/material";
import { Background } from "../../components/ui/Background";
import { Header } from "../../components/ui/Header";
import { LoginForm } from "../../components/LoginForm";
import SSUGT_LOGO from "../../assets/ssugt-logo.png";
import { useLogin } from "../../hooks/useLogin/useLogin";

const LoginPage: React.FC = () => {
  const { isLoading, handleLogin, openSnackbar, handleCloseSnackbar, error } =
    useLogin();

  return (
    <Background>
      <Fade in timeout={800}>
        <Card
          sx={{
            p: 5,
            width: "100%",
            maxWidth: 420,
            borderRadius: 8,
            backgroundColor: "rgba(255, 255, 255, 0.85)",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.2)",
            textAlign: "center",
            zIndex: 1,
            border: "1px solid rgba(255, 255, 255, 0.3)",
            position: "relative",
            overflow: "hidden",
            backdropFilter: "blur(10px)",
          }}
        >
          {/* Эффект стекла и лоадер */}
          <Fade in={isLoading}>
            <Box
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 10,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                backdropFilter: "blur(6px)",
                backgroundColor: "rgba(255, 255, 255, 0.4)",
                gap: 2,
              }}
            >
              <CircularProgress size={50} thickness={4} color="primary" />
              <Typography
                variant="body2"
                sx={{ fontWeight: 600, color: "primary.main" }}
              >
                Вход в систему...
              </Typography>
            </Box>
          </Fade>

          {/* Контент карточки */}
          <Box
            sx={{
              filter: isLoading ? "blur(2px)" : "none",
              transition: "filter 0.3s ease",
            }}
          >
            <img
              src={SSUGT_LOGO}
              width={250}
              style={{ marginBottom: 24 }}
              alt="SSUGT Logo"
            />
            <Header />
            <LoginForm onSubmit={handleLogin} loading={isLoading} />
          </Box>
        </Card>
      </Fade>

      {/* Snackbar остается без изменений */}
      <Snackbar
        open={openSnackbar}
        autoHideDuration={5000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        TransitionComponent={(props) => <Slide {...props} direction="up" />}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity="error"
          variant="filled"
          sx={{ width: "100%", borderRadius: 3, fontWeight: 500 }}
        >
          {error}
        </Alert>
      </Snackbar>
    </Background>
  );
};

export default LoginPage;
