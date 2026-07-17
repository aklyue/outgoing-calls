import { useState, useEffect } from "react";
import { useDebouncedValue } from "../useDebouncedValue/useDebouncedValue";

interface ValidationInputs {
  controlCallEnabled: boolean;
  controlCallNumber: string;
  controlCallInterval: number;
  emailReportEnabled: boolean;
  emailReportAddress: string;
  emailReportInterval: number;
}

export function useAdvancedSettingsValidation(inputs: ValidationInputs) {
  const [errors, setErrors] = useState({
    controlCallNumber: "",
    controlCallInterval: "",
    emailReportAddress: "",
    emailReportInterval: "",
  });

  // Дебаунсим всё внутри хука
  const [debouncedPhone] = useDebouncedValue(inputs.controlCallNumber, 400);
  const [debouncedPhoneInterval] = useDebouncedValue(
    inputs.controlCallInterval,
    400,
  );
  const [debouncedEmail] = useDebouncedValue(inputs.emailReportAddress, 400);
  const [debouncedEmailInterval] = useDebouncedValue(
    inputs.emailReportInterval,
    400,
  );

  const phoneRegex = /^\+?[1-9]\d{6,14}$/;
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  useEffect(() => {
    let errorText = "";
    if (inputs.controlCallEnabled) {
      if (!debouncedPhone) errorText = "Номер телефона обязателен";
      else if (!phoneRegex.test(debouncedPhone))
        errorText = "Неверный формат номера";
    }
    setErrors((prev) => ({ ...prev, controlCallNumber: errorText }));
  }, [debouncedPhone, inputs.controlCallEnabled]);

  useEffect(() => {
    let errorText = "";
    if (inputs.controlCallEnabled) {
      const num = Number(debouncedPhoneInterval);
      if (!debouncedPhoneInterval || isNaN(num)) errorText = "Укажите интервал";
      else if (num < 1) errorText = "Интервал должен быть больше 0";
    }
    setErrors((prev) => ({ ...prev, controlCallInterval: errorText }));
  }, [debouncedPhoneInterval, inputs.controlCallEnabled]);

  useEffect(() => {
    let errorText = "";
    if (inputs.emailReportEnabled) {
      if (!debouncedEmail) errorText = "Email обязателен";
      else if (!emailRegex.test(debouncedEmail))
        errorText = "Некорректный формат email";
    }
    setErrors((prev) => ({ ...prev, emailReportAddress: errorText }));
  }, [debouncedEmail, inputs.emailReportEnabled]);

  useEffect(() => {
    let errorText = "";
    if (inputs.emailReportEnabled) {
      const num = Number(debouncedEmailInterval);
      if (!debouncedEmailInterval || isNaN(num)) errorText = "Укажите интервал";
      else if (num < 1) errorText = "Интервал должен быть больше 0";
    }
    setErrors((prev) => ({ ...prev, emailReportInterval: errorText }));
  }, [debouncedEmailInterval, inputs.emailReportEnabled]);

  return errors;
}
