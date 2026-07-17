import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Checkbox,
  FormControlLabel,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SettingsIcon from "@mui/icons-material/Settings";

interface AdvancedSettingsPanelProps {
  controlCallEnabledLocal: boolean;
  setControlCallEnabledLocal: (v: boolean) => void;
  controlCallNumberLocal: string;
  setControlCallNumberLocal: (v: string) => void;
  controlCallIntervalLocal: number;
  setControlCallIntervalLocal: (v: number) => void;
  emailReportEnabledLocal: boolean;
  setEmailReportEnabledLocal: (v: boolean) => void;
  emailReportAddressLocal: string;
  setEmailReportAddressLocal: (v: string) => void;
  emailReportIntervalLocal: number;
  setEmailReportIntervalLocal: (v: number) => void;
  triggerStartLocal: boolean;
  setTriggerStartLocal: (v: boolean) => void;
  triggerIntervalLocal: boolean;
  setTriggerIntervalLocal: (v: boolean) => void;
  triggerFinalLocal: boolean;
  setTriggerFinalLocal: (v: boolean) => void;
  // Добавили в интерфейс пропсов ошибки
  errors: {
    controlCallNumber: string;
    controlCallInterval: string;
    emailReportAddress: string;
    emailReportInterval: string;
  };
}

export const AdvancedSettingsPanel = ({
  controlCallEnabledLocal,
  setControlCallEnabledLocal,
  controlCallNumberLocal,
  setControlCallNumberLocal,
  controlCallIntervalLocal,
  setControlCallIntervalLocal,
  emailReportEnabledLocal,
  setEmailReportEnabledLocal,
  emailReportAddressLocal,
  setEmailReportAddressLocal,
  emailReportIntervalLocal,
  setEmailReportIntervalLocal,
  triggerStartLocal,
  setTriggerStartLocal,
  triggerIntervalLocal,
  setTriggerIntervalLocal,
  triggerFinalLocal,
  setTriggerFinalLocal,
  // Принимаем ошибки сверху из SettingsPanel
  errors,
}: AdvancedSettingsPanelProps) => {
  return (
    <Accordion
      variant="outlined"
      sx={{ borderRadius: 1, mt: 2, "&:before": { display: "none" } }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" alignItems="center" gap={1}>
          <SettingsIcon fontSize="small" color="action" />
          <Typography variant="body2" fontWeight={600}>
            Дополнительные настройки (Контроль и Email-отчеты)
          </Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0 }}>
        <Stack direction="column" gap={3}>
          {/* БЛОК КОНТРОЛЬНОГО ЗВОНКА */}
          <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
            <FormControlLabel
              sx={{ mb: 2, display: "flex", width: "max-content" }}
              control={
                <Checkbox
                  checked={controlCallEnabledLocal}
                  onChange={(e) => setControlCallEnabledLocal(e.target.checked)}
                />
              }
              label={
                <Typography variant="subtitle2" fontWeight={600}>
                  Включить контрольный вызов
                </Typography>
              }
            />

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
                  disabled={!controlCallEnabledLocal}
                  value={controlCallNumberLocal}
                  error={!!errors.controlCallNumber}
                  helperText={errors.controlCallNumber}
                  onChange={(e) => setControlCallNumberLocal(e.target.value)}
                  placeholder="+79991234567"
                />
              </Box>

              <Box sx={{ flex: 1, width: "100%" }}>
                <TextField
                  label="Интервал контроля (каждые N звонков)"
                  type="number"
                  size="small"
                  fullWidth
                  disabled={!controlCallEnabledLocal}
                  value={controlCallIntervalLocal || ""}
                  error={!!errors.controlCallInterval}
                  helperText={errors.controlCallInterval}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setControlCallIntervalLocal(isNaN(val) ? 0 : val);
                  }}
                  inputProps={{ min: 1 }}
                />
              </Box>
            </Box>
          </Box>

          {/* БЛОК EMAIL ОТЧЕТНОСТИ */}
          <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
            <FormControlLabel
              sx={{ mb: 2, display: "flex", width: "max-content" }}
              control={
                <Checkbox
                  checked={emailReportEnabledLocal}
                  onChange={(e) => setEmailReportEnabledLocal(e.target.checked)}
                />
              }
              label={
                <Typography variant="subtitle2" fontWeight={600}>
                  Автоматическая Email-отчетность
                </Typography>
              }
            />

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
                  disabled={!emailReportEnabledLocal}
                  value={emailReportAddressLocal}
                  error={!!errors.emailReportAddress}
                  helperText={errors.emailReportAddress}
                  onChange={(e) => setEmailReportAddressLocal(e.target.value)}
                  placeholder="report@sgugit.ru"
                />
              </Box>

              <Box sx={{ flex: 1, width: "100%" }}>
                <TextField
                  label="Интервал отправки отчетов (записей)"
                  type="number"
                  size="small"
                  fullWidth
                  disabled={!emailReportEnabledLocal}
                  value={emailReportIntervalLocal || ""}
                  error={!!errors.emailReportInterval}
                  helperText={errors.emailReportInterval}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setEmailReportIntervalLocal(isNaN(val) ? 0 : val);
                  }}
                  inputProps={{ min: 1 }}
                />
              </Box>
            </Box>

            {/* ТРИГГЕРЫ */}
            <Box sx={{ pl: 1 }}>
              <Typography
                variant="caption"
                color="textSecondary"
                display="block"
                sx={{ mb: 0.5 }}
              >
                Условия отправки отчетов:
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  flexDirection: { xs: "column", sm: "row" },
                  gap: 1,
                  flexWrap: "wrap",
                }}
              >
                <FormControlLabel
                  control={
                    <Checkbox
                      size="small"
                      disabled={!emailReportEnabledLocal}
                      checked={triggerStartLocal}
                      onChange={(e) => setTriggerStartLocal(e.target.checked)}
                    />
                  }
                  label={<Typography variant="caption">При старте</Typography>}
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      size="small"
                      disabled={!emailReportEnabledLocal}
                      checked={triggerIntervalLocal}
                      onChange={(e) =>
                        setTriggerIntervalLocal(e.target.checked)
                      }
                    />
                  }
                  label={
                    <Typography variant="caption">
                      По интервалу шагов
                    </Typography>
                  }
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      size="small"
                      disabled={!emailReportEnabledLocal}
                      checked={triggerFinalLocal}
                      onChange={(e) => setTriggerFinalLocal(e.target.checked)}
                    />
                  }
                  label={
                    <Typography variant="caption">По завершении</Typography>
                  }
                />
              </Box>
            </Box>
          </Box>
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
};

export default AdvancedSettingsPanel;
