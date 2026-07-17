import type { Middleware } from "@reduxjs/toolkit";
import type { RootState } from "../index";
import { API } from "../../api/api";

export const loggerMiddleware: Middleware =
  (store) => (next) => async (action: any) => {
    const result = next(action);
    const state = store.getState() as RootState;

    const auditMap: Record<string, string> = {
      "calls/setCalls": "Просмотр списка обзвонов",
      "calls/createCall/fulfilled": "Создание нового обзвона",
      "calls/updateSettings": "Изменение параметров обзвона",
      "calls/delete": "Удаление обзвона",
      "calls/downloadXlsx/fulfilled": "Экспорт результатов обзвона в XLSX",
      "user/login/attempt": "Попытка входа в систему",
      "user/login/success": "Успешная авторизация",
      "user/registration/attempt": "Регистрация нового пользователя",
      "user/logout/fulfilled": "Выход из системы",
    };

    if (Object.prototype.hasOwnProperty.call(auditMap, action.type)) {
      const logEntry = {
        userId: state.user.user?.id || "anonymous",
        username: state.user.user?.username || "unknown",
        action_type: action.type,
        action_description: auditMap[action.type],
        payload: action.payload || null,
        timestamp: new Date().toISOString().replace("Z", ""),
      };

      try {
        await API.post("/logs/", logEntry);
      } catch (e) {
        console.error("Failed to send audit log:", e);
      }
    }

    return result;
  };
