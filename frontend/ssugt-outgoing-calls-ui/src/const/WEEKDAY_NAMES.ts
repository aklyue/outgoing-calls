import type { DaySchedule } from "../types/Schedule";

export const WEEKDAY_NAMES: Record<DaySchedule["weekday"], string> = {
  monday: "Понедельник",
  tuesday: "Вторник",
  wednesday: "Среда",
  thursday: "Четверг",
  friday: "Пятница",
  saturday: "Суббота",
  sunday: "Воскресенье",
};
