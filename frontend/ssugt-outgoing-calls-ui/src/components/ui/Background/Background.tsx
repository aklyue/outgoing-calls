import React from "react";
import { Box } from "@mui/material";

const Background: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Box
    sx={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      position: "relative",
      overflow: "hidden",
      background: "radial-gradient(circle at top left, #ffffff, #ffffff)",
      "&::before": {
        content: '""',
        position: "absolute",
        width: "300px",
        height: "300px",
        background: "rgba(131, 131, 131, 0.1)",
        borderRadius: "50%",
        top: "-100px",
        right: "-50px",
      },
      "&::after": {
        content: '""',
        position: "absolute",
        width: "200px",
        height: "200px",
        background: "rgba(105, 105, 105, 0.1)",
        borderRadius: "50%",
        bottom: "-50px",
        left: "-50px",
      },
    }}
  >
    {children}
  </Box>
);

export default Background;
