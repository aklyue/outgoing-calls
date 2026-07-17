import axios from "axios";

export type Category =
  | "ru_mobile_numbers"
  | "ru_city_numbers"
  | "international_numbers";

export const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});
