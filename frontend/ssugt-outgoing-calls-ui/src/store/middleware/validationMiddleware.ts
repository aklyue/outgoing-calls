import { createListenerMiddleware } from "@reduxjs/toolkit";
import {
  runAdvancedValidation,
  setAdvancedSettingsErrors,
} from "../ui/validationSlice";

export const validationListenerMiddleware = createListenerMiddleware();

const phoneRegex = /^\+?[1-9]\d{6,14}$/;
const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

validationListenerMiddleware.startListening({
  actionCreator: runAdvancedValidation,
  effect: async (action, listenerApi) => {
    listenerApi.cancelActiveListeners();

    await listenerApi.delay(400);

    const {
      controlCallEnabled,
      controlCallNumber,
      controlCallInterval,
      emailReportEnabled,
      emailReportAddress,
      emailReportInterval,
    } = action.payload;

    const errors = {
      controlCallNumber: "",
      controlCallInterval: "",
      emailReportAddress: "",
      emailReportInterval: "",
    };

    if (controlCallEnabled) {
      if (!controlCallNumber)
        errors.controlCallNumber = "Номер телефона обязателен";
      else if (!phoneRegex.test(controlCallNumber))
        errors.controlCallNumber = "Неверный формат номера";

      const num = Number(controlCallInterval);
      if (!controlCallInterval || isNaN(num))
        errors.controlCallInterval = "Укажите интервал";
      else if (num < 1)
        errors.controlCallInterval = "Интервал должен быть больше 0";
    }

    // Валидация Email
    if (emailReportEnabled) {
      if (!emailReportAddress) errors.emailReportAddress = "Email обязателен";
      else if (!emailRegex.test(emailReportAddress))
        errors.emailReportAddress = "Некорректный формат email";

      const num = Number(emailReportInterval);
      if (!emailReportInterval || isNaN(num))
        errors.emailReportInterval = "Укажите интервал";
      else if (num < 1)
        errors.emailReportInterval = "Интервал должен быть больше 0";
    }

    listenerApi.dispatch(setAdvancedSettingsErrors(errors));
  },
});
