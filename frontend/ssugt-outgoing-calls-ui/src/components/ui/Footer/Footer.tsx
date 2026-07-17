import { Box, Paper, Typography, useMediaQuery, useTheme } from "@mui/material";
import { NavButton } from "../NavButton";
import type { View } from "../../../types/View";
import { useApi } from "../../../hooks/useApi/useApi";
import { useAuth } from "../../../hooks/useAuth/useAuth";
import SSUGT_LOGO from "../../../assets/ssugt-logo.png";

import {
  PhoneOutlined as PhoneIcon,
  PeopleOutlined as TeamIcon,
  DescriptionOutlined as JournalIcon,
  ExitToAppOutlined as LogoutIcon,
  PersonAddAlt1Outlined as RegisterIcon,
} from "@mui/icons-material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ConfirmDialog } from "../ConfirmDialog";

const PRIMARY_COLOR = "#009FE3";
const NEUTRAL_COLOR = "#637381";

interface FooterProps {
  activeView: View;
  setActiveView: (value: React.SetStateAction<View>) => void;
  balanceText: string;
}

function Footer(props: FooterProps) {
  const { balanceText, activeView, setActiveView } = props;
  const { logout } = useApi();
  const { isAdmin, isOwner } = useAuth();

  const isMobile = useMediaQuery(useTheme().breakpoints.down("md"));

  const navigate = useNavigate();

  const [isLogoutOpen, setIsLogoutOpen] = useState(false);

  const handleLogoutClick = () => {
    setIsLogoutOpen(true);
  };

  return (
    <>
      <Paper
        elevation={0}
        component="footer"
        sx={{
          position: "sticky",
          bottom: 0,
          zIndex: 1000,
          p: 1.5,
          borderTop: "1px solid #f0f0f0",
          bgcolor: "rgba(255, 255, 255, 0.9)",
          backdropFilter: "blur(10px)",
        }}
      >
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr auto 1fr" },
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Box>
            <img src={SSUGT_LOGO} alt="Logo" width={180} />
          </Box>

          <Box
            sx={{
              display: "flex",
              bgcolor: "#f4f6f8",
              width: isMobile ? "100%" : undefined,
              justifyContent: "center",
              p: 0.5,
              borderRadius: 3,
              gap: 0.5,
            }}
          >
            {!isMobile && (
              <NavButton
                active={activeView === "calls"}
                onClick={() => setActiveView("calls")}
                icon={<PhoneIcon />}
                label="Обзвоны"
                color={activeView === "calls" ? PRIMARY_COLOR : NEUTRAL_COLOR}
              />
            )}

            {isOwner && (
              <NavButton
                active={activeView === "users"}
                onClick={() => setActiveView("users")}
                icon={<TeamIcon />}
                label="Пользователи"
                color={activeView === "users" ? PRIMARY_COLOR : NEUTRAL_COLOR}
              />
            )}

            {/* {(isAdmin || isOwner) && (
              <>
                <NavButton
                  active={activeView === "register"}
                  onClick={() => setActiveView("register")}
                  icon={<RegisterIcon />}
                  label="Регистрация пользователя"
                  color={
                    activeView === "register" ? PRIMARY_COLOR : NEUTRAL_COLOR
                  }
                />
              </>
            )} */}

            <NavButton
              active={activeView === "journal"}
              onClick={() => setActiveView("journal")}
              icon={<JournalIcon />}
              label="Журнал"
              color={activeView === "journal" ? PRIMARY_COLOR : NEUTRAL_COLOR}
            />
            <NavButton
              active={false}
              onClick={handleLogoutClick}
              icon={<LogoutIcon />}
              label="Выход"
              color={NEUTRAL_COLOR}
            />
          </Box>

          <Box
            sx={{
              display: "flex",
              justifyContent: { xs: "center", md: "flex-end" },
              mt: { xs: 2, md: 0 },
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                px: 2,
                py: 0.75,
                borderRadius: "12px",
                bgcolor: "#fff",
                border: "1px solid #e0e0e0",
                boxShadow: "0 2px 4px rgba(0,0,0,0.02)",
              }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  bgcolor:
                    parseFloat(balanceText) > 100 ? "#278fd4" : "#ff9800",
                }}
              />
              <Typography
                variant="body2"
                sx={{ fontWeight: 500, color: "#454f5b" }}
              >
                Яндекс:{" "}
                <span style={{ color: "#212b36", fontWeight: 700 }}>
                  {balanceText} ₽
                </span>
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>

      <ConfirmDialog
        open={isLogoutOpen}
        title="Выход из системы"
        description="Вы действительно хотите выйти?"
        confirmText="Выйти"
        confirmColor="error"
        onClose={() => setIsLogoutOpen(false)}
        onConfirm={async () => {
          setIsLogoutOpen(false);
          await logout();
        }}
      />
    </>
  );
}

export default Footer;
