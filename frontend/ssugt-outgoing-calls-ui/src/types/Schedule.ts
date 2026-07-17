export interface TimeRange {
  start_time_at: string;
  end_time_at: string;
  max_num_channels_occupied: number;
}

export interface DaySchedule {
  weekday:
    | "monday"
    | "tuesday"
    | "wednesday"
    | "thursday"
    | "friday"
    | "saturday"
    | "sunday";
  time_ranges: TimeRange[];
}
