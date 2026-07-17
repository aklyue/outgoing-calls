import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Chip,
  Grid,
  MenuItem,
  Select,
  Slider,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import HistoryIcon from "@mui/icons-material/History";

import { CATEGORY_OPTIONS } from "../../../const/CATEGORY_OPTIONS";
import { SLIDER_MARKS } from "../../../const/SLIDER_MARKS";
import type { Category } from "../../../api/api";
import AdvancedSettingsPanel from "../AdvancedSettingsPanel";

// Импортируем твой хук валидации
import { useAdvancedSettingsValidation } from "../../../hooks/useAdvancedSettingsValidation/useAdvancedSettingsValidation";

interface SettingsPanelProps {
  isDirty: boolean;
  saving: boolean;
  currentCall: any;
  pausedLocal: boolean;
  setPausedLocal: (paused: boolean) => void;
  ttsTypeLocal: string;
  setTtsTypeLocal: (ttsType: string) => void;
  ttsOptions: string[];
  categoriesLocal: Category[];
  setCategoriesLocal: (categories: Category[]) => void;
  retryLimitLocal: number;
  setRetryLimitLocal: (limit: number) => void;
  setScheduleTemp: (schedule: any[]) => void;
  scheduleLocal: any[];
  setScheduleModalOpen: (open: boolean) => void;
  handleSave: () => Promise<void>;

  // === ПРОПСЫ ДЛЯ НОВЫХ НАСТРОЕК ===
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
}

function SettingsPanel({
  isDirty,
  saving,
  currentCall,
  pausedLocal,
  setPausedLocal,
  ttsTypeLocal,
  setTtsTypeLocal,
  ttsOptions,
  categoriesLocal,
  setCategoriesLocal,
  retryLimitLocal,
  setRetryLimitLocal,
  setScheduleTemp,
  scheduleLocal,
  setScheduleModalOpen,
  handleSave,

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
}: SettingsPanelProps) {
  // === ПЕРЕНЕСЛИ ВАЛИДАЦИЮ СЮДА ===
  const errors = useAdvancedSettingsValidation({
    controlCallEnabled: controlCallEnabledLocal,
    controlCallNumber: controlCallNumberLocal,
    controlCallInterval: controlCallIntervalLocal,
    emailReportEnabled: emailReportEnabledLocal,
    emailReportAddress: emailReportAddressLocal,
    emailReportInterval: emailReportIntervalLocal,
  });

  // Проверка на наличие хоть одной ошибки
  const hasErrors = Object.values(errors).some((err) => err !== "");

  return (
    <Box
      sx={{
        p: 2,
        mb: 2,
        borderRadius: 3,
        border: "1px solid",
        borderColor: isDirty ? "warning.light" : "divider",
        bgcolor: isDirty ? "#fff9f0" : "transparent",
        boxShadow: 1,
      }}
    >
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        {isDirty && (
          <Chip
            label="Есть несохранённые изменения"
            color="warning"
            variant="outlined"
            size="small"
          />
        )}
        {isDirty && (
          <Stack direction="row" gap={1}>
            <Button
              size="small"
              onClick={() => setPausedLocal(Boolean(currentCall.is_paused))}
            >
              Отменить
            </Button>
            <LoadingButton
              size="small"
              variant="contained"
              loading={saving}
              onClick={handleSave}
              // Блокируем кнопку, если есть локальные ошибки валидации
              disabled={hasErrors}
            >
              Сохранить
            </LoadingButton>
          </Stack>
        )}
      </Stack>

      <Stack direction="row" alignItems="center" gap={1}>
        <Typography variant="body2">Приостановлен:</Typography>
        <Switch
          checked={pausedLocal}
          onChange={(e) => setPausedLocal(e.target.checked)}
        />
      </Stack>
      <Grid container spacing={2}>
        <Grid sx={{ xs: 12, md: 4 }}>
          <Typography variant="caption" color="textSecondary">
            Сервис синтеза:
          </Typography>
          <Select
            fullWidth
            size="small"
            value={ttsTypeLocal || ""}
            onChange={(e) => setTtsTypeLocal(e.target.value)}
            displayEmpty
          >
            {Array.from(new Set([...ttsOptions, ttsTypeLocal]))
              .filter(Boolean)
              .map((opt) => (
                <MenuItem key={opt} value={opt}>
                  {opt === "ssugt"
                    ? "СГУГиТ"
                    : opt === "yandex"
                      ? "Yandex"
                      : opt}
                </MenuItem>
              ))}
          </Select>
        </Grid>
        <Grid sx={{ xs: 12, md: 5 }}>
          <Typography variant="caption" color="textSecondary">
            Категории номеров:
          </Typography>
          <Select
            multiple
            fullWidth
            size="small"
            value={categoriesLocal}
            onChange={(e) => {
              const value = e.target.value;
              setCategoriesLocal(value as Category[]);
            }}
            renderValue={(selected) => (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                {(selected as string[]).map((val) => (
                  <Chip
                    key={val}
                    size="small"
                    label={CATEGORY_OPTIONS.find((c) => c.value === val)?.label}
                    onDelete={() => {
                      const next = categoriesLocal.filter(
                        (item) => item !== val,
                      );
                      setCategoriesLocal(next);
                    }}
                    onMouseDown={(e) => e.stopPropagation()}
                  />
                ))}
              </Box>
            )}
          >
            {CATEGORY_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </Grid>
      </Grid>

      <Stack direction="row" alignItems="center" gap={4} mt={2}>
        <Box sx={{ width: 300 }}>
          <Typography variant="body2" gutterBottom>
            Попыток дозвона: {retryLimitLocal}
          </Typography>
          <Slider
            value={retryLimitLocal}
            min={0}
            max={10}
            step={1}
            marks={SLIDER_MARKS}
            onChange={(_, v) => setRetryLimitLocal(v as number)}
          />
        </Box>
        <Button
          variant="outlined"
          startIcon={<HistoryIcon />}
          onClick={() => {
            setScheduleTemp(JSON.parse(JSON.stringify(scheduleLocal)));
            setScheduleModalOpen(true);
          }}
        >
          Расписание
        </Button>
      </Stack>
      <AdvancedSettingsPanel
        controlCallEnabledLocal={controlCallEnabledLocal}
        setControlCallEnabledLocal={setControlCallEnabledLocal}
        controlCallNumberLocal={controlCallNumberLocal}
        setControlCallNumberLocal={setControlCallNumberLocal}
        controlCallIntervalLocal={controlCallIntervalLocal}
        setControlCallIntervalLocal={setControlCallIntervalLocal}
        emailReportEnabledLocal={emailReportEnabledLocal}
        setEmailReportEnabledLocal={setEmailReportEnabledLocal}
        emailReportAddressLocal={emailReportAddressLocal}
        setEmailReportAddressLocal={setEmailReportAddressLocal}
        emailReportIntervalLocal={emailReportIntervalLocal}
        setEmailReportIntervalLocal={setEmailReportIntervalLocal}
        triggerStartLocal={triggerStartLocal}
        setTriggerStartLocal={setTriggerStartLocal}
        triggerIntervalLocal={triggerIntervalLocal}
        setTriggerIntervalLocal={setTriggerIntervalLocal}
        triggerFinalLocal={triggerFinalLocal}
        setTriggerFinalLocal={setTriggerFinalLocal}
        // Передаем готовый объект ошибок вниз
        errors={errors}
      />
    </Box>
  );
}

export default SettingsPanel;
