import React from "react";
import { Box, Typography } from "@mui/material";
import { LockOutlined as LockIcon } from "@mui/icons-material";

const Header: React.FC = () => (
  <>
    {/* <Box
      sx={{
        width: 60,
        height: 60,
        bgcolor: "info.main",
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        margin: "0 auto 24px",
        boxShadow: "0 8px 16px rgba(110, 197, 251, 0.4)",
        color: "white",
      }}
    >
      <LockIcon fontSize="large" />
    </Box> */}
    <Typography variant="h4" fontWeight={800} color="text.primary" gutterBottom>
      Добро пожаловать!
    </Typography>
    <Typography variant="body2" color="text.secondary" mb={4}>
      Пожалуйста, войдите в свой аккаунт
    </Typography>
  </>
);

export default Header;