import { useEffect, useMemo, useState } from "react";
import type { Category } from "../../api/api";
import { canonicalizeSchedule } from "../../utils/canonicalizeSchedule";
import { ALLOWED_CATEGORIES } from "../../const/ALLOWED_CATEGORIES";

interface UseCallDetailsProps {
  patchCall: (
    id: string,
    data: {
      is_paused?: boolean | undefined;
      name?: string | undefined;
      retry_limit?: number | undefined;
      schedule?: any[] | undefined;
      tts_type?: string | null | undefined;
      categories?: Category[] | undefined;
      // === ТИПИЗАЦИЯ НОВЫХ ПОЛЕЙ ДЛЯ PATCH ===
      control_call_enabled?: boolean;
      control_call_number?: string | null;
      control_call_interval?: number;
      email_report_enabled?: boolean;
      email_report_address?: string | null;
      email_report_interval?: number;
      email_report_trigger_start?: boolean;
      email_report_trigger_interval?: boolean;
      email_report_trigger_final?: boolean;
    },
  ) => Promise<any>;
  getSynthesizers: () => Promise<string[]>;
  currentCall: any;
  onUpdateCall: (updatedCall: any) => void;
}

export const useCallDetails = ({
  patchCall,
  getSynthesizers,
  currentCall,
  onUpdateCall,
}: UseCallDetailsProps) => {
  const [callNameLocal, setCallNameLocal] = useState("");
  const [pausedLocal, setPausedLocal] = useState(false);
  const [retryLimitLocal, setRetryLimitLocal] = useState(3);
  const [categoriesLocal, setCategoriesLocal] = useState<Category[]>([]);
  const [ttsTypeLocal, setTtsTypeLocal] = useState("");
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsOptions, setTtsOptions] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [scheduleLocal, setScheduleLocal] = useState<any[]>([]);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [scheduleTemp, setScheduleTemp] = useState<any[]>([]);

  // Доп настройки
  const [controlCallEnabledLocal, setControlCallEnabledLocal] = useState(
    currentCall?.control_call_enabled || false,
  );
  const [controlCallNumberLocal, setControlCallNumberLocal] = useState(
    currentCall?.control_call_number || "",
  );
  const [controlCallIntervalLocal, setControlCallIntervalLocal] = useState(
    currentCall?.control_call_interval || 50,
  );

  const [emailReportEnabledLocal, setEmailReportEnabledLocal] = useState(
    currentCall?.email_report_enabled || false,
  );
  const [emailReportAddressLocal, setEmailReportAddressLocal] = useState(
    currentCall?.email_report_address || "",
  );
  const [emailReportIntervalLocal, setEmailReportIntervalLocal] = useState(
    currentCall?.email_report_interval || 100,
  );

  const [triggerStartLocal, setTriggerStartLocal] = useState(
    currentCall?.email_report_trigger_start || false,
  );
  const [triggerIntervalLocal, setTriggerIntervalLocal] = useState(
    currentCall?.email_report_trigger_interval || false,
  );
  const [triggerFinalLocal, setTriggerFinalLocal] = useState(
    currentCall?.email_report_trigger_final || false,
  );

  // Синхронизация стейтов при смене текущего обзвона
  useEffect(() => {
    if (currentCall) {
      const filteredCats = Array.isArray(currentCall.categories)
        ? currentCall.categories.filter((c: string) =>
            ALLOWED_CATEGORIES.includes(c),
          )
        : [];
      setCategoriesLocal(filteredCats);
      setPausedLocal(Boolean(currentCall.is_paused));
      setRetryLimitLocal(Number(currentCall.retry_limit ?? 3));
      setTtsTypeLocal(String(currentCall.tts_type ?? ""));
      setCallNameLocal(currentCall.name);
      setScheduleLocal(canonicalizeSchedule(currentCall.schedule || []));
      setScheduleTemp(canonicalizeSchedule(currentCall.schedule || []));

      // Обновляем настройки контрольного звонка и email
      setControlCallEnabledLocal(Boolean(currentCall.control_call_enabled));
      setControlCallNumberLocal(currentCall.control_call_number || "");
      setControlCallIntervalLocal(
        Number(currentCall.control_call_interval ?? 50),
      );

      setEmailReportEnabledLocal(Boolean(currentCall.email_report_enabled));
      setEmailReportAddressLocal(currentCall.email_report_address || "");
      setEmailReportIntervalLocal(
        Number(currentCall.email_report_interval ?? 100),
      );

      setTriggerStartLocal(Boolean(currentCall.email_report_trigger_start));
      setTriggerIntervalLocal(
        Boolean(currentCall.email_report_trigger_interval),
      );
      setTriggerFinalLocal(Boolean(currentCall.email_report_trigger_final));
    }
  }, [currentCall, canonicalizeSchedule]);

  useEffect(() => {
    setTtsLoading(true);
    getSynthesizers()
      .then((list) => setTtsOptions(list || []))
      .finally(() => setTtsLoading(false));
  }, [getSynthesizers]);

  // Проверка изменений (isDirty) с учетом новых полей
  const isDirty = useMemo(() => {
    if (!currentCall) return false;
    const serverSchedule = JSON.stringify(
      canonicalizeSchedule(currentCall.schedule || []),
    );
    const localSchedule = JSON.stringify(canonicalizeSchedule(scheduleLocal));
    const serverCats = [...(currentCall.categories || [])]
      .filter((c) => ALLOWED_CATEGORIES.includes(c))
      .sort();
    const localCats = [...categoriesLocal].sort();

    return (
      pausedLocal !== Boolean(currentCall.is_paused) ||
      retryLimitLocal !== Number(currentCall.retry_limit ?? 3) ||
      ttsTypeLocal !== String(currentCall.tts_type ?? "") ||
      serverSchedule !== localSchedule ||
      JSON.stringify(serverCats) !== JSON.stringify(localCats) ||
      // Проверка полей контроля и отчетов:
      controlCallEnabledLocal !== Boolean(currentCall.control_call_enabled) ||
      controlCallNumberLocal !== (currentCall.control_call_number || "") ||
      controlCallIntervalLocal !==
        Number(currentCall.control_call_interval ?? 50) ||
      emailReportEnabledLocal !== Boolean(currentCall.email_report_enabled) ||
      emailReportAddressLocal !== (currentCall.email_report_address || "") ||
      emailReportIntervalLocal !==
        Number(currentCall.email_report_interval ?? 100) ||
      triggerStartLocal !== Boolean(currentCall.email_report_trigger_start) ||
      triggerIntervalLocal !==
        Boolean(currentCall.email_report_trigger_interval) ||
      triggerFinalLocal !== Boolean(currentCall.email_report_trigger_final)
    );
  }, [
    currentCall,
    pausedLocal,
    retryLimitLocal,
    ttsTypeLocal,
    scheduleLocal,
    categoriesLocal,
    canonicalizeSchedule,
    controlCallEnabledLocal,
    controlCallNumberLocal,
    controlCallIntervalLocal,
    emailReportEnabledLocal,
    emailReportAddressLocal,
    emailReportIntervalLocal,
    triggerStartLocal,
    triggerIntervalLocal,
    triggerFinalLocal,
  ]);

  const handleSave = async () => {
    if (!currentCall || saving) return;
    setSaving(true);
    try {
      const payload = {
        name: callNameLocal,
        is_paused: pausedLocal,
        retry_limit: retryLimitLocal,
        schedule: scheduleLocal,
        tts_type: ttsTypeLocal || null,
        categories: categoriesLocal,
        // Посылаем новые настройки на бэкэнд
        control_call_enabled: controlCallEnabledLocal,
        control_call_number: controlCallNumberLocal || null,
        control_call_interval: controlCallIntervalLocal,
        email_report_enabled: emailReportEnabledLocal,
        email_report_address: emailReportAddressLocal || null,
        email_report_interval: emailReportIntervalLocal,
        email_report_trigger_start: triggerStartLocal,
        email_report_trigger_interval: triggerIntervalLocal,
        email_report_trigger_final: triggerFinalLocal,
      };
      const updated = await patchCall(currentCall.id, payload);
      onUpdateCall(updated);
    } finally {
      setSaving(false);
    }
  };

  return {
    isDirty,
    setPausedLocal,
    saving,
    handleSave,
    pausedLocal,
    ttsTypeLocal,
    setTtsTypeLocal,
    ttsOptions,
    categoriesLocal,
    setCategoriesLocal,
    retryLimitLocal,
    setRetryLimitLocal,
    scheduleLocal,
    setScheduleLocal,
    setScheduleTemp,
    setScheduleModalOpen,
    scheduleModalOpen,
    scheduleTemp,
    ttsLoading,
    // === ВОЗВРАЩАЕМ НОВЫЕ СТЕЙТЫ НАРУЖУ ===
    controlCallEnabledLocal,
    setControlCallEnabledLocal,
    controlCallNumberLocal,
    setControlCallNumberLocal,
    controlCallIntervalLocal,
    setControlCallIntervalLocal,
    emailReportEnabledLocal,
    setEmailReportEnabledLocal,
    emailReportAddressLocal,
    setEmailReportAddressLocal,
    emailReportIntervalLocal,
    setEmailReportIntervalLocal,
    triggerStartLocal,
    setTriggerStartLocal,
    triggerIntervalLocal,
    setTriggerIntervalLocal,
    triggerFinalLocal,
    setTriggerFinalLocal,
  };
};
