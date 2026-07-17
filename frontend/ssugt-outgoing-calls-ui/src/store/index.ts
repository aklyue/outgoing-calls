import { configureStore } from "@reduxjs/toolkit";
import callsReducer from "./api/callsSlice";
import balanceReducer from "./api/balanceSlice";
import { errorMiddleware } from "./middleware/errorMiddleware";
import { loggerMiddleware } from "./middleware/loggerMiddleware";
import { validationListenerMiddleware } from "./middleware/validationMiddleware";
import uiReducer from "./ui/uiSlice";
import validationReducer from "./ui/validationSlice";
import userReducer from "./api/userSlice";
import logsReducer from "./api/logsSlice";
import usersReducer from "./api/usersSlice";

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    validation: validationReducer,
    calls: callsReducer,
    balance: balanceReducer,
    user: userReducer,
    logs: logsReducer,
    users: usersReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    })
      .prepend(validationListenerMiddleware.middleware)
      .concat(errorMiddleware)
      .concat(loggerMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
