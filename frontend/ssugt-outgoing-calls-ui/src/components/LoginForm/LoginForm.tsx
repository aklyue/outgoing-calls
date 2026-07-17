import React, { useState } from "react";
import {
  TextField,
  Button,
  InputAdornment,
  IconButton,
  CircularProgress,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { useDispatch } from "react-redux";

interface LoginFormProps {
  onSubmit: (login: string, pass: string) => void;
  loading: boolean;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSubmit, loading }) => {
  const dispatch = useDispatch();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch({
      type: "user/login/attempt",
      payload: { login },
    });
    onSubmit(login, password);
  };

  return (
    <form onSubmit={handleSubmit}>
      <TextField
        fullWidth
        label="Логин"
        variant="outlined"
        margin="normal"
        required
        value={login}
        onChange={(e) => setLogin(e.target.value)}
        InputProps={{ sx: { borderRadius: 3, bgcolor: "rgba(0,0,0,0.02)" } }}
      />
      <TextField
        fullWidth
        label="Пароль"
        variant="outlined"
        margin="normal"
        required
        type={showPassword ? "text" : "password"}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        InputProps={{
          sx: { borderRadius: 3, bgcolor: "rgba(0,0,0,0.02)" },
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                onClick={() => setShowPassword(!showPassword)}
                edge="end"
                sx={{
                  mr: -0.5,
                }}
              >
                {showPassword ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      <Button
        fullWidth
        variant="outlined"
        size="large"
        type="submit"
        disabled={loading}
        sx={{
          mt: 4,
          py: 1.8,
          borderRadius: 3,
          fontWeight: 700,
          textTransform: "none",
          boxShadow: "0 6px 20px rgba(110, 142, 251, 0.3)",
          "&:hover": { boxShadow: "0 8px 25px rgba(110, 142, 251, 0.4)" },
        }}
      >
        {loading ? <CircularProgress size={26} color="inherit" /> : "Войти"}
      </Button>
    </form>
  );
};

export default LoginForm;
