import dayjs from "dayjs";

const NSK_TZ = "Asia/Novosibirsk";

function parseAsUtc(val: string) {
  // If the string lacks timezone info, treat it as UTC by appending Z.
  if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(val)) {
    return new Date(val + "Z");
  }
  return new Date(val);
}

export const formatDate = (val?: string) => {
  if (!val) return "";
  try {
    const d = parseAsUtc(val);
    return new Intl.DateTimeFormat("ru-RU", {
      timeZone: NSK_TZ,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);
  } catch (e) {
    return "";
  }
};

export const canonicalizeSchedule = (input: any[]) => {
  const weekdayOrder = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
  ];
  const map = new Map(input.map((d) => [d.weekday, d]));

  return weekdayOrder.map((w) => {
    const day = map.get(w) || { weekday: w, time_ranges: [] };
    return {
      weekday: day.weekday,
      time_ranges: [...day.time_ranges]
        .map((r: any) => ({
          start_time_at: r.start_time_at,
          end_time_at: r.end_time_at,
          max_num_channels_occupied: Number(r.max_num_channels_occupied ?? 0),
        }))
        .sort((a, b) => a.start_time_at.localeCompare(b.start_time_at)),
    };
  });
};
