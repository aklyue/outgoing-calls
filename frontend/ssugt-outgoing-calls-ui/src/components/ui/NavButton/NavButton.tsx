import { Box, Typography, useMediaQuery, useTheme } from "@mui/material";

const NavButton = ({ active, onClick, icon, label, color }: any) => {
  const isMobile = useMediaQuery(useTheme().breakpoints.down("md"));
  return (
    <Box
      onClick={onClick}
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        cursor: "pointer",
        p: "4px 12px",
        width: isMobile ? "100%" : undefined,
        borderRadius: 2,
        transition: "all 0.2s",
        color: active ? color : "#8c8c8c",
        bgcolor: active ? `${color}1A` : "transparent",
        "&:hover": { bgcolor: `${color}10`, color: color },
      }}
    >
      {icon}
      <Typography sx={{ fontSize: "12px", fontWeight: 400 }}>
        {label}
      </Typography>
    </Box>
  );
};

export default NavButton;
