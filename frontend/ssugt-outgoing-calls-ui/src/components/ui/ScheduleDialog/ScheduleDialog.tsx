import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
} from "@mui/material";
import { ScheduleCard } from "../../ScheduleCard"; // путь к вашему компоненту карточки
import type { DaySchedule } from "../../../types/Schedule";

interface ScheduleDialogProps {
  scheduleModalOpen: boolean;
  setScheduleModalOpen: (open: boolean) => void;
  // scheduleTemp — это массив из 7 дней, который мы редактируем
  scheduleTemp: DaySchedule[];
  // Функция для обновления массива scheduleTemp в родителе
  setScheduleTemp: React.Dispatch<React.SetStateAction<DaySchedule[]>>;
  // Сохранение итогового результата
  setScheduleLocal: (schedule: any) => void;
  canonicalizeSchedule: (schedule: any[]) => any[];
  minChannels?: number;
  maxChannels?: number;
}

function ScheduleDialog({
  scheduleModalOpen,
  setScheduleModalOpen,
  scheduleTemp,
  setScheduleTemp,
  setScheduleLocal,
  canonicalizeSchedule,
  minChannels = 0,
  maxChannels = 5,
}: ScheduleDialogProps) {
  const handleUpdateDay = (dayIdx: number, updatedDay: DaySchedule) => {
    const nextSchedule = [...scheduleTemp];
    nextSchedule[dayIdx] = updatedDay;
    setScheduleTemp(nextSchedule);
  };

  const handleAddRange = (dayIdx: number) => {
    const nextSchedule = [...scheduleTemp];
    const day = nextSchedule[dayIdx];
    day.time_ranges.push({
      start_time_at: "09:00",
      end_time_at: "18:00",
      max_num_channels_occupied: 1,
    });
    setScheduleTemp(nextSchedule);
  };

  const handleRemoveRange = (dayIdx: number, rangeIdx: number) => {
    const nextSchedule = [...scheduleTemp];
    nextSchedule[dayIdx].time_ranges.splice(rangeIdx, 1);
    setScheduleTemp(nextSchedule);
  };

  return (
    <Dialog
      open={scheduleModalOpen}
      onClose={() => setScheduleModalOpen(false)}
      maxWidth={"md"}
      fullWidth
    >
      <DialogTitle>Настройка расписания обзвона</DialogTitle>
      <DialogContent dividers sx={{ bgcolor: "#f5f5f5" }}>
        <Grid container spacing={2}>
          {scheduleTemp.map((day, dIdx) => (
            <Grid
              key={day.weekday}
              sx={{
                xs: 12,
                md: 4,
                height: "fit-content",
              }}
            >
              <ScheduleCard
                day={day}
                idx={dIdx}
                minChannels={minChannels}
                maxChannels={maxChannels}
                onUpdateDay={handleUpdateDay}
                onAddRange={handleAddRange}
                onRemoveRange={handleRemoveRange}
              />
            </Grid>
          ))}
        </Grid>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={() => setScheduleModalOpen(false)} color="inherit">
          Отмена
        </Button>
        <Button
          variant="contained"
          onClick={() => {
            const final = canonicalizeSchedule(scheduleTemp);
            setScheduleLocal(final);
            setScheduleModalOpen(false);
          }}
        >
          Применить изменения
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default ScheduleDialog;
