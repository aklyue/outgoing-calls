import { Box, Stack, Typography, Chip, Paper, Divider } from "@mui/material";
import CallIcon from "@mui/icons-material/Call";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import RecordVoiceOverIcon from "@mui/icons-material/RecordVoiceOver";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import CategoryIcon from "@mui/icons-material/Category";
import PersonIcon from "@mui/icons-material/Person";

const weekdayRu: Record<string, string> = {
  monday: "Пн",
  tuesday: "Вт",
  wednesday: "Ср",
  thursday: "Чт",
  friday: "Пт",
  saturday: "Сб",
  sunday: "Вс",
};

const PayloadRenderer = ({
  action,
  payload,
}: {
  action: string;
  payload: any;
}) => {
  if (!payload) return null;

  const isCallAction =
    action.includes("calls/updateSettings") ||
    action.includes("calls/createCall");

  if (action === "calls/delete") {
    return (
      <Box
        sx={{
          p: 2,
          bgcolor: "error.lighter",
          borderRadius: 2,
          borderLeft: "4px solid",
          borderColor: "error.main",
          display: "flex",
          alignItems: "center",
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          gap: 2,
          backgroundColor: "#fff",
        }}
      >
        <DeleteForeverIcon color="error" />
        <Box>
          <Typography variant="caption" color="error.main" fontWeight={800}>
            Объект удален навсегда
          </Typography>
          <Typography
            variant="body2"
            sx={{ fontFamily: "monospace", fontWeight: 600 }}
          >
            ID: {payload.id}
          </Typography>
        </Box>
      </Box>
    );
  }

  if (isCallAction) {
    const retryLimit = payload.retry_limit ?? payload.retryLimit;
    const ttsType = payload.tts_type ?? payload.ttsType;

    return (
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderRadius: 2,
          borderLeft: "4px solid",
          borderColor: "primary.main",
          bgcolor: "background.paper",
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
        }}
      >
        <Stack spacing={2}>
          {payload.name && (
            <Box>
              <Stack
                direction="row"
                spacing={1}
                alignItems="center"
                sx={{ mb: 0.5 }}
              >
                <CallIcon sx={{ fontSize: 18, color: "primary.main" }} />
                <Typography
                  variant="subtitle2"
                  fontWeight={800}
                  color="text.primary"
                >
                  {payload.name}
                </Typography>
              </Stack>
              <Divider />
            </Box>
          )}

          <Stack direction="row" spacing={4}>
            {retryLimit !== undefined && (
              <Box>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  fontWeight={700}
                >
                  ПОВТОРЫ
                </Typography>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  sx={{ color: "primary.dark" }}
                >
                  {retryLimit} попыток
                </Typography>
              </Box>
            )}
            {ttsType && (
              <Box>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  fontWeight={700}
                  sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                >
                  <RecordVoiceOverIcon sx={{ fontSize: 12 }} /> ГОЛОС
                </Typography>
                <Chip
                  label={ttsType}
                  size="small"
                  color="primary"
                  variant="filled"
                  sx={{
                    mt: 0.5,
                    fontWeight: 700,
                    borderRadius: "4px",
                    height: 20,
                  }}
                />
              </Box>
            )}
          </Stack>

          {payload.categories && payload.categories.length > 0 && (
            <Box>
              <Typography
                variant="caption"
                color="text.secondary"
                fontWeight={700}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  mb: 0.5,
                }}
              >
                <CategoryIcon sx={{ fontSize: 12 }} /> КАТЕГОРИИ
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                {payload.categories.map((cat: any) => (
                  <Chip
                    key={typeof cat === "string" ? cat : cat.id}
                    label={typeof cat === "string" ? cat : cat.name}
                    size="small"
                    variant="outlined"
                    sx={{
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: 600,
                    }}
                  />
                ))}
              </Stack>
            </Box>
          )}

          {payload.schedule && (
            <Box sx={{ bgcolor: "grey.50", p: 1, borderRadius: 1 }}>
              <Typography
                variant="caption"
                color="text.secondary"
                fontWeight={700}
                sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 1 }}
              >
                <CalendarMonthIcon sx={{ fontSize: 12 }} /> ГРАФИК РАБОТЫ
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap">
                {payload.schedule.map((s: any) => (
                  <Box
                    key={s.weekday}
                    sx={{
                      px: 1,
                      py: 0.3,
                      borderRadius: "4px",
                      bgcolor: "primary.main",
                      color: "white",
                      fontSize: "11px",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    {weekdayRu[s.weekday.toLowerCase()] || s.weekday}
                  </Box>
                ))}
              </Stack>
            </Box>
          )}
        </Stack>
      </Paper>
    );
  }

  if (action.includes("calls/downloadXlsx/fulfilled")) {
    return (
      <Box
        sx={{
          p: 1.5,
          bgcolor: "info.lighter",
          borderRadius: 2,
          borderLeft: "4px solid",
          borderColor: "info.main",
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          backgroundColor: "#fff",
        }}
      >
        <PersonIcon color="info" />
        <Box>
          <Typography variant="caption" color="info.main" fontWeight={800}>
            ЭКСПОРТ
          </Typography>
          <Typography variant="body2" fontWeight={600}>
            {payload.filename}
          </Typography>
          <Typography variant="caption" fontWeight={400}>
            <strong>ID:</strong> {payload.id}
          </Typography>
        </Box>
      </Box>
    );
  }

  if (action.includes("user/login")) {
    return (
      <Box
        sx={{
          p: 1.5,
          bgcolor: "info.lighter",
          borderRadius: 2,
          borderLeft: "4px solid",
          borderColor: "info.main",
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          backgroundColor: "#fff",
        }}
      >
        <PersonIcon color="info" />
        <Box>
          <Typography variant="caption" color="info.main" fontWeight={800}>
            АВТОРИЗАЦИЯ
          </Typography>
          <Typography variant="body2" fontWeight={600}>
            {payload.username || payload.login || "Пользователь"}
          </Typography>
        </Box>
      </Box>
    );
  }

  // Дефолтный JSON (для всего остального)
  return (
    <Paper
      variant="outlined"
      sx={{
        mt: 1,
        p: 1.5,
        bgcolor: "#1e1e1e", // Темная тема для "сырого" кода
        borderRadius: 2,
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: "0.75rem",
      }}
    >
      <pre style={{ margin: 0, color: "#9cdcfe", overflow: "auto" }}>
        {JSON.stringify(payload, null, 2)}
      </pre>
    </Paper>
  );
};

export default PayloadRenderer;
