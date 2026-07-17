import {
  TextField,
  FormControlLabel,
  Checkbox,
  Typography,
  Box,
  Stack,
} from "@mui/material";

interface AdvancedSettingsTabProps {
  // Контрольный звонок
  controlCallEnabled: boolean;
  setControlCallEnabled: (v: boolean) => void;
  controlCallNumber: string;
  setControlCallNumber: (v: string) => void;
  controlCallInterval: number;
  setControlCallInterval: (v: number) => void;

  // Email отчетность
  emailReportEnabled: boolean;
  setEmailReportEnabled: (v: boolean) => void;
  emailReportAddress: string;
  setEmailReportAddress: (v: string) => void;
  emailReportInterval: number;
  setEmailReportInterval: (v: number) => void;

  // Триггеры
  triggerStart: boolean;
  setTriggerStart: (v: boolean) => void;
  triggerInterval: boolean;
  setTriggerInterval: (v: boolean) => void;
  triggerFinal: boolean;
  setTriggerFinal: (v: boolean) => void;

  // ДОБАВИЛИ ОБЪЕКТ ОШИБОК В ИНТЕРФЕЙС ПРОПСОВ
  errors: {
    controlCallNumber: string;
    controlCallInterval: string;
    emailReportAddress: string;
    emailReportInterval: string;
  };
}

const AdvancedSettingsTab = ({
  controlCallEnabled,
  setControlCallEnabled,
  controlCallNumber,
  setControlCallNumber,
  controlCallInterval,
  setControlCallInterval,
  emailReportEnabled,
  setEmailReportEnabled,
  emailReportAddress,
  setEmailReportAddress,
  emailReportInterval,
  setEmailReportInterval,
  triggerStart,
  setTriggerStart,
  triggerInterval,
  setTriggerInterval,
  triggerFinal,
  setTriggerFinal,
  // Принимаем ошибки
  errors,
}: AdvancedSettingsTabProps) => {
  return (
    <Stack direction="column" gap={3}>
      {/* СЕКЦИЯ: КОНТРОЛЬНЫЙ ЗВОНОК */}
      <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
        <FormControlLabel
          sx={{ mb: 2, display: "flex", width: "max-content" }}
          control={
            <Checkbox
              checked={controlCallEnabled}
              onChange={(e) => setControlCallEnabled(e.target.checked)}
            />
          }
          label={
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Включить контрольный вызов
            </Typography>
          }
        />

        {/* Инпуты на чистом Flexbox */}
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            gap: 2,
            width: "100%",
          }}
        >
          <Box sx={{ flex: 1, width: "100%" }}>
            <TextField
              label="Номер телефона для контроля"
              size="small"
              fullWidth
              disabled={!controlCallEnabled}
              value={controlCallNumber}
              onChange={(e) => setControlCallNumber(e.target.value)}
              placeholder="+79991234567"
              // ВЫВОД ОШИБКИ
              error={!!errors.controlCallNumber}
              helperText={
                errors.controlCallNumber ||
                "Номер, на который пойдет проверочный вызов"
              }
            />
          </Box>

          <Box sx={{ flex: 1, width: "100%" }}>
            <TextField
              label="Интервал контроля (каждые N звонков)"
              type="number"
              size="small"
              fullWidth
              disabled={!controlCallEnabled}
              value={controlCallInterval || ""}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                setControlCallInterval(isNaN(val) ? 0 : val);
              }}
              inputProps={{ min: 1 }}
              // ВЫВОД ОШИБКИ
              error={!!errors.controlCallInterval}
              helperText={
                errors.controlCallInterval ||
                "Через сколько успешных звонков совершать проверку линии"
              }
            />
          </Box>
        </Box>
      </Box>

      {/* СЕКЦИЯ: EMAIL-ОТЧЕТНОСТЬ */}
      <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
        <FormControlLabel
          sx={{ mb: 2, display: "flex", width: "max-content" }}
          control={
            <Checkbox
              checked={emailReportEnabled}
              onChange={(e) => setEmailReportEnabled(e.target.checked)}
            />
          }
          label={
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Автоматическая Email-отчетность
            </Typography>
          }
        />

        {/* Инпуты на чистом Flexbox */}
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            gap: 2,
            mb: 2,
            width: "100%",
          }}
        >
          <Box sx={{ flex: 1, width: "100%" }}>
            <TextField
              label="Email адрес для отчетов"
              type="email"
              size="small"
              fullWidth
              disabled={!emailReportEnabled}
              value={emailReportAddress}
              onChange={(e) => setEmailReportAddress(e.target.value)}
              placeholder="report@sgugit.ru"
              // ВЫВОД ОШИБКИ
              error={!!errors.emailReportAddress}
              helperText={errors.emailReportAddress}
            />
          </Box>

          <Box sx={{ flex: 1, width: "100%" }}>
            <TextField
              label="Интервал отправки отчетов (записей)"
              type="number"
              size="small"
              fullWidth
              disabled={!emailReportEnabled}
              value={emailReportInterval || ""}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                setEmailReportInterval(isNaN(val) ? 0 : val);
              }}
              inputProps={{ min: 1 }}
              // ВЫВОД ОШИБКИ
              error={!!errors.emailReportInterval}
              helperText={
                errors.emailReportInterval ||
                "Отправлять промежуточный отчет каждые N звонков"
              }
            />
          </Box>
        </Box>

        {/* ТРИГГЕРЫ ОТПРАВКИ */}
        <Box sx={{ pl: 1 }}>
          <Typography
            variant="caption"
            color="textSecondary"
            display="block"
            sx={{ mb: 0.5, fontWeight: 500 }}
          >
            Условия и триггеры отправки писем:
          </Typography>

          {/* Чекбоксы триггеров на чистом Flexbox */}
          <Box
            sx={{
              display: "flex",
              flexDirection: { xs: "column", sm: "row" },
              gap: 1,
              flexWrap: "wrap",
            }}
          >
            <Box sx={{ flex: { xs: "none", sm: 1 }, minWidth: "max-content" }}>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    disabled={!emailReportEnabled}
                    checked={triggerStart}
                    onChange={(e) => setTriggerStart(e.target.checked)}
                  />
                }
                label={
                  <Typography variant="caption">При старте обзвона</Typography>
                }
              />
            </Box>

            <Box sx={{ flex: { xs: "none", sm: 1 }, minWidth: "max-content" }}>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    disabled={!emailReportEnabled}
                    checked={triggerInterval}
                    onChange={(e) => setTriggerInterval(e.target.checked)}
                  />
                }
                label={
                  <Typography variant="caption">По интервалу шагов</Typography>
                }
              />
            </Box>

            <Box sx={{ flex: { xs: "none", sm: 1 }, minWidth: "max-content" }}>
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    disabled={!emailReportEnabled}
                    checked={triggerFinal}
                    onChange={(e) => setTriggerFinal(e.target.checked)}
                  />
                }
                label={
                  <Typography variant="caption">
                    По завершении обзвона
                  </Typography>
                }
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </Stack>
  );
};

export default AdvancedSettingsTab;
