import { isRejectedWithValue } from "@reduxjs/toolkit";
import type { Middleware } from "@reduxjs/toolkit";

export const errorMiddleware: Middleware = () => (next) => (action) => {
  if (isRejectedWithValue(action)) {
    const message = action.payload || "Произошла ошибка";
    console.error("Middleware caught error:", message);
  }
  return next(action);
};
