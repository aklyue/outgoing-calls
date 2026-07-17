import {
  Paper,
  Chip,
  FormControl,
  InputLabel,
  Stack,
  Typography,
  Tooltip,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Slider,
  Divider,
  TextField,
  Button,
  Box,
} from "@mui/material";

import { HelpOutline as QuestionCircleOutlined } from "@mui/icons-material";
import { CATEGORY_OPTIONS } from "../../../const/CATEGORY_OPTIONS";
import { AudioPreview } from "../../AudioPreview";
import AttachFileIcon from "@mui/icons-material/AttachFile";

interface GeneralSettingsTabProps {
  callName: string;
  setCallName: (value: string) => void;
  handleFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  ttsType: string;
  setTtsType: (value: string) => void;
  ttsOptions: string[];
  ttsLoading: boolean;
  ttsExtraText: string;
  categoriesSelected: string[];
  setCategoriesSelected: (value: string[]) => void;
  columns: string[];
  textTemplate: string;
  handleInput: (e: React.ChangeEvent<HTMLTextAreaElement, Element>) => void;
  finalDf: any[];
  phoneColumn: string;
  setPhoneColumn: (value: string) => void;
  retryLimit: number;
  setRetryLimit: (value: number) => void;
  isPaused: boolean;
  setIsPaused: (value: boolean) => void;
  editorWrapRef: React.RefObject<HTMLDivElement | null>;
  pauseMs: number;
  setPauseMs: (value: number) => void;
  textAreaRef: React.RefObject<HTMLTextAreaElement | null>;
  insertToken: (token: string) => void;
  showAutocomplete: boolean;
  autocompletePos: { top: number; left: number };
  hovered: string;
  fileName: string;
  handleKeyDown: (e: React.KeyboardEvent<any>) => void;
}

function GeneralSettingsTab({
  callName,
  setCallName,
  handleFileUpload,
  ttsType,
  setTtsType,
  ttsOptions,
  ttsLoading,
  ttsExtraText,
  categoriesSelected,
  setCategoriesSelected,
  columns,
  textTemplate,
  handleInput,
  finalDf,
  phoneColumn,
  setPhoneColumn,
  retryLimit,
  setRetryLimit,
  isPaused,
  setIsPaused,
  editorWrapRef,
  pauseMs,
  setPauseMs,
  textAreaRef,
  insertToken,
  showAutocomplete,
  autocompletePos,
  hovered,
  fileName,
  handleKeyDown,
}: GeneralSettingsTabProps) {
  return (
    <Stack spacing={2}>
      <TextField
        label="Название обзвона"
        fullWidth
        size="small"
        value={callName}
        onChange={(e) => setCallName(e.target.value)}
      />

      <Button variant="outlined" component="label" fullWidth>
        Загрузить лист обзвона (.xlsx, .csv)
        <input
          type="file"
          hidden
          accept=".xlsx,.xls,.csv"
          onChange={handleFileUpload}
        />
      </Button>

      <Box
        sx={{
          p: 0.5,
          borderRadius: 1,
          transition: "background-color 0.2s ease",
          "&:hover": {
            backgroundColor: "action.hover",
            cursor: "pointer",
          },
        }}
      >
        {fileName && (
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <AttachFileIcon
              sx={{
                fontSize: 16,
                color: "info.main",
              }}
            />

            <Typography
              variant="caption"
              display="block"
              sx={{
                color: "info.main",
                fontWeight: 500,
                margin: 0,
              }}
            >
              Выбран файл: {fileName}
            </Typography>
          </Stack>
        )}
      </Box>

      <Box>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 1,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              Сервис синтеза речи
            </Typography>
            <Tooltip title="Этот выбор определяет, каким сервисом синтеза речи будет озвучен текст в предпрослушивании и при запуске обзвона.">
              <QuestionCircleOutlined
                sx={{
                  fontSize: 18,
                  color: "text.secondary",
                  cursor: "help",
                }}
              />
            </Tooltip>
          </Box>

          <Typography
            variant="caption"
            sx={{
              color: "text.secondary",
              fontSize: "12px",
              textAlign: "right",
              maxWidth: "50%",
            }}
          >
            {ttsExtraText}
          </Typography>
        </Box>
        <Select
          fullWidth
          size="small"
          value={ttsType}
          onChange={(e) => setTtsType(e.target.value)}
          disabled={ttsLoading || ttsOptions.length === 0}
        >
          {ttsOptions.map((v) => (
            <MenuItem key={v} value={v}>
              {v === "ssugt" ? "СГУГиТ" : v === "edge-tts" ? "Edge-TTS" : "Яндекс"}
            </MenuItem>
          ))}
        </Select>
      </Box>

      <Box>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Категории номеров
        </Typography>
        <Select
          multiple
          fullWidth
          size="small"
          value={categoriesSelected}
          onChange={(e) => {
            const value = e.target.value;
            setCategoriesSelected(
              typeof value === "string" ? value.split(",") : value,
            );
          }}
          renderValue={(selected) => (
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {(selected as string[]).map((val) => (
                <Chip
                  key={val}
                  size="small"
                  label={CATEGORY_OPTIONS.find((c) => c.value === val)?.label}
                  onDelete={() => {
                    const next = categoriesSelected.filter(
                      (item) => item !== val,
                    );
                    setCategoriesSelected(next);
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
      </Box>

      <Box ref={editorWrapRef} sx={{ position: "relative" }}>
        <TextField
          label="Текст синтеза"
          multiline
          rows={4}
          fullWidth
          value={textTemplate}
          onChange={handleInput}
          inputRef={textAreaRef}
          placeholder="Введите текст. Используйте '[' для подстановок"
          inputProps={{
            onKeyDown: handleKeyDown,
          }}
        />

        {showAutocomplete && (
          <Paper
            sx={{
              position: "absolute",
              top: autocompletePos.top,
              left: autocompletePos.left,
              zIndex: 1300,
              width: 300,
              boxShadow: 4,
              border: "1px solid #ddd",
            }}
          >
            <Box
              sx={{
                p: 1,
                bgcolor: hovered === "__pause__" ? "#fff1b8" : "#fffbe6",
              }}
            >
              <Typography variant="caption" fontWeight="bold">
                ⏱ Пауза (мс)
              </Typography>
              <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                <TextField
                  size="small"
                  type="number"
                  value={pauseMs}
                  onChange={(e) => setPauseMs(Number(e.target.value))}
                />
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => insertToken(`пауза ${pauseMs}]`)}
                >
                  Вставить
                </Button>
              </Box>
            </Box>
            <Divider />
            <Box sx={{ maxHeight: 160, overflow: "auto" }}>
              {columns.map((col) => (
                <MenuItem key={col} onClick={() => insertToken(`${col}]`)}>
                  [{col}]
                </MenuItem>
              ))}
            </Box>
          </Paper>
        )}
      </Box>

      <AudioPreview
        template={textTemplate}
        rows={finalDf}
        col={phoneColumn}
        ttsType={ttsType}
      />

      <FormControl fullWidth size="small">
        <InputLabel id="phone-column-label">Колонка с телефоном</InputLabel>
        <Select
          labelId="phone-column-label"
          value={phoneColumn}
          onChange={(e) => setPhoneColumn(e.target.value)}
          disabled={!columns.length}
          label="Колонка с телефоном"
        >
          {columns.map((c) => (
            <MenuItem key={c} value={c}>
              {c}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Box sx={{ px: 2 }}>
        <Typography variant="caption">Попытки дозвона</Typography>
        <Slider
          value={retryLimit}
          onChange={(_, v) => setRetryLimit(v as number)}
          min={0}
          max={10}
          marks
          valueLabelDisplay="auto"
        />
      </Box>

      <FormControlLabel
        control={
          <Checkbox
            checked={isPaused}
            onChange={(e) => setIsPaused(e.target.checked)}
          />
        }
        label="Создать в режиме паузы"
      />
    </Stack>
  );
}

export default GeneralSettingsTab;
