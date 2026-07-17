import React from "react";
import { Box, Typography } from "@mui/material";
import { InboxOutlined } from "@mui/icons-material";

interface EmptyProps {
  description?: string;
}

const Empty: React.FC<EmptyProps> = ({ description = "Нет данных" }) => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        p: 4,
        color: "text.secondary",
      }}
    >
      <InboxOutlined sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
      <Typography variant="body2">{description}</Typography>
    </Box>
  );
};

export default Empty;
