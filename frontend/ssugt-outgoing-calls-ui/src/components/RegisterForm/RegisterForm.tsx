import React, { useState } from "react";
import {
  TextField,
  Button,
  InputAdornment,
  IconButton,
  CircularProgress,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  type SelectChangeEvent,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { useDispatch } from "react-redux";

interface RegisterFormProps {
  onSubmit: (data: any) => void;
  loading: boolean;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onSubmit, loading }) => {
  const dispatch = useDispatch();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    login: "",
    role: "",
    password: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleChange = (e: SelectChangeEvent) => {
    setFormData({ ...formData, role: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch({
      type: "user/registration/attempt",
      payload: {
        targetLogin: formData.login,
        role: formData.role,
      },
    });
    onSubmit(formData);
  };

  const commonInputStyles = {
    borderRadius: 3,
    bgcolor: "rgba(0,0,0,0.02)",
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing={3} pt={2}>
        <TextField
          fullWidth
          label="Логин"
          name="login"
          variant="outlined"
          margin="normal"
          required
          value={formData.login}
          onChange={handleChange}
          InputProps={{ sx: commonInputStyles }}
        />
        <TextField
          fullWidth
          label="Пароль"
          name="password"
          variant="outlined"
          margin="normal"
          required
          type={showPassword ? "text" : "password"}
          value={formData.password}
          onChange={handleChange}
          InputProps={{
            sx: commonInputStyles,
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <FormControl fullWidth margin="normal">
          <InputLabel id="role-select-label">Роль</InputLabel>
          <Select
            labelId="role-select-label"
            id="role-select"
            value={formData.role}
            label="Роль"
            onChange={handleRoleChange}
            sx={commonInputStyles}
          >
            <MenuItem value="user">Пользователь</MenuItem>
            <MenuItem value="admin">Администратор</MenuItem>
          </Select>
        </FormControl>
      </Stack>
      <Button
        fullWidth
        variant="contained"
        size="large"
        type="submit"
        disabled={loading}
        sx={{
          mt: 5,
          py: 1.8,
          borderRadius: 3,
          fontSize: "1rem",
          fontWeight: 700,
          textTransform: "none",
          boxShadow: "0 6px 20px rgba(25, 118, 210, 0.3)",
          transition: "all 0.3s ease",
          "&:hover": {
            boxShadow: "0 8px 25px rgba(25, 118, 210, 0.4)",
          },
        }}
      >
        {loading ? (
          <CircularProgress size={26} color="inherit" />
        ) : (
          "Создать аккаунт"
        )}
      </Button>
    </form>
  );
};

export default RegisterForm;
