import type { TimeRange } from "../types/Schedule";

export const isValidTime = (v: string): boolean =>
  /^([01]\d|2[0-3]):[0-5]\d$/.test(v);

export const timeToMinutes = (v: string): number => {
  if (!isValidTime(v)) return -1;
  const [h, m] = v.split(":").map(Number);
  return h * 60 + m;
};

export const hasOverlap = (ranges: TimeRange[]): boolean => {
  const valid = ranges
    .filter((r) => isValidTime(r.start_time_at) && isValidTime(r.end_time_at))
    .map((r) => ({
      s: timeToMinutes(r.start_time_at),
      e: timeToMinutes(r.end_time_at),
    }))
    .filter((r) => r.e > r.s)
    .sort((a, b) => a.s - b.s);

  for (let i = 1; i < valid.length; i++) {
    if (valid[i].s < valid[i - 1].e) return true;
  }
  return false;
};
