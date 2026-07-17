import React, { useMemo } from "react";
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  TextField,
  Slider,
  Button,
  Alert,
  Stack,
  Chip,
  Divider,
} from "@mui/material";
import {
  Add as PlusOutlined,
  Delete as DeleteOutlined,
  Warning as WarningIcon,
} from "@mui/icons-material";
import type { DaySchedule, TimeRange } from "../../types/Schedule";
import {
  hasOverlap,
  isValidTime,
  timeToMinutes,
} from "../../utils/scheduleHelpers";

import { WEEKDAY_NAMES } from "../../const/WEEKDAY_NAMES";

interface ScheduleCardProps {
  day: DaySchedule;
  idx: number;
  minChannels: number;
  maxChannels: number;
  onUpdateDay: (dayIdx: number, updatedDay: DaySchedule) => void;
  onAddRange: (dayIdx: number) => void;
  onRemoveRange: (dayIdx: number, rangeIdx: number) => void;
}

const ScheduleCard: React.FC<ScheduleCardProps> = ({
  day,
  idx,
  minChannels,
  maxChannels,
  onUpdateDay,
  onAddRange,
  onRemoveRange,
}) => {
  const overlap = useMemo(() => hasOverlap(day.time_ranges), [day.time_ranges]);

  const updateRangeField = (
    rangeIdx: number,
    field: keyof TimeRange,
    value: any,
  ) => {
    const newDay = { ...day };
    newDay.time_ranges = [...day.time_ranges];
    newDay.time_ranges[rangeIdx] = {
      ...newDay.time_ranges[rangeIdx],
      [field]: value,
    };
    onUpdateDay(idx, newDay);
  };

  return (
    <Card
      variant="outlined"
      sx={{
        bgcolor: "#fcfcfc",
        borderRadius: 2,
        height: "100%",
        "& .MuiCardHeader-title": {
          fontSize: "1rem",
          fontWeight: 600,
          textAlign: "center",
        },
      }}
    >
      <CardHeader
        title={WEEKDAY_NAMES[day.weekday]}
        action={
          overlap ? (
            <Chip
              label="Пересечения"
              color="error"
              size="small"
              variant="filled"
            />
          ) : null
        }
      />
      <Divider />
      <CardContent sx={{ p: 1.5 }}>
        <Stack spacing={2}>
          {day.time_ranges.map((range, rIdx) => (
            <Box
              key={rIdx}
              sx={{
                border: "1px solid #f0f0f0",
                borderRadius: 2,
                p: 1.5,
                bgcolor: "#fff",
              }}
            >
              <Stack spacing={1.5}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Typography variant="caption">С</Typography>
                  <TextField
                    size="small"
                    placeholder="HH:MM"
                    value={range.start_time_at}
                    onChange={(e) =>
                      updateRangeField(rIdx, "start_time_at", e.target.value)
                    }
                    sx={{ width: 85 }}
                  />
                  <Typography variant="caption">До</Typography>
                  <TextField
                    size="small"
                    placeholder="HH:MM"
                    value={range.end_time_at}
                    onChange={(e) =>
                      updateRangeField(rIdx, "end_time_at", e.target.value)
                    }
                    sx={{ width: 85 }}
                  />
                </Box>

                <Box sx={{ px: 1 }}>
                  <Typography
                    variant="caption"
                    sx={{ color: "text.secondary" }}
                  >
                    Каналы: {range.max_num_channels_occupied}
                  </Typography>
                  <Slider
                    size="small"
                    value={range.max_num_channels_occupied}
                    min={minChannels}
                    max={maxChannels}
                    onChange={(_, val) =>
                      updateRangeField(
                        rIdx,
                        "max_num_channels_occupied",
                        val as number,
                      )
                    }
                  />
                </Box>

                {!isValidTime(range.start_time_at) ||
                !isValidTime(range.end_time_at) ? (
                  <Alert
                    severity="warning"
                    icon={<WarningIcon fontSize="inherit" />}
                    sx={{ py: 0 }}
                  >
                    Неверный формат
                  </Alert>
                ) : timeToMinutes(range.end_time_at) <=
                  timeToMinutes(range.start_time_at) ? (
                  <Alert
                    severity="warning"
                    icon={<WarningIcon fontSize="inherit" />}
                    sx={{ py: 0 }}
                  >
                    Конец должен быть позже
                  </Alert>
                ) : null}

                <Button
                  color="error"
                  size="small"
                  fullWidth
                  startIcon={<DeleteOutlined />}
                  onClick={() => onRemoveRange(idx, rIdx)}
                  disabled={day.time_ranges.length === 1}
                >
                  Удалить
                </Button>
              </Stack>
            </Box>
          ))}

          <Button
            variant="outlined"
            fullWidth
            startIcon={<PlusOutlined />}
            onClick={() => onAddRange(idx)}
            sx={{
              borderStyle: "dashed",
              borderWidth: 1,
              textTransform: "none",
            }}
          >
            Добавить интервал
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default ScheduleCard;
