export const DEFAULT_SCHEDULE = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
]
  .map((weekday) => ({
    weekday,
    time_ranges: [
      {
        start_time_at: "09:00",
        end_time_at: "17:00",
        max_num_channels_occupied: 2,
      },
      {
        start_time_at: "00:00",
        end_time_at: "09:00",
        max_num_channels_occupied: 5,
      },
      {
        start_time_at: "17:00",
        end_time_at: "23:59",
        max_num_channels_occupied: 5,
      },
    ],
  }))
  .concat([
    {
      weekday: "saturday",
      time_ranges: [
        {
          start_time_at: "00:00",
          end_time_at: "23:59",
          max_num_channels_occupied: 5,
        },
      ],
    },
    {
      weekday: "sunday",
      time_ranges: [
        {
          start_time_at: "00:00",
          end_time_at: "23:59",
          max_num_channels_occupied: 5,
        },
      ],
    },
  ]);
