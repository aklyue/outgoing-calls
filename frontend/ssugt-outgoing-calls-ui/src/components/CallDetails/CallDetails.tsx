import React, { useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Box,
  CircularProgress,
} from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";

import { useApi } from "../../hooks/useApi/useApi";
import { canonicalizeSchedule } from "../../utils/canonicalizeSchedule";
import { useCallDetails } from "../../hooks/useCallDetails/useCallDetails";
import { ScheduleDialog } from "../ui/ScheduleDialog";
import { CallsTable } from "../ui/CallsTable";
import { SettingsPanel } from "../ui/SettingsPanel";

interface Props {
  currentCall: any;
  phoneCalls: any[];
  loadingMore?: boolean;
  hasMore?: boolean;
  onExport: () => void;
  onLoadMore: () => void;
  onUpdateCall: (updatedCall: any) => void;
}

const CallDetails: React.FC<Props> = ({
  currentCall,
  phoneCalls,
  loadingMore,
  hasMore,
  onExport,
  onLoadMore,
  onUpdateCall,
}) => {
  const { patchCall, getSynthesizers } = useApi();

  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingMore && hasMore) onLoadMore();
      },
      { threshold: 0.1, rootMargin: "200px" },
    );
    if (sentinelRef.current) observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [loadingMore, hasMore, onLoadMore]);

  const {
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
    // === ДЕСТРУКТУРИРУЕМ НОВЫЕ СТЕЙТЫ КОНТРОЛЯ И ОТЧЕТОВ ИЗ ХУКА ===
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
  } = useCallDetails({ patchCall, getSynthesizers, currentCall, onUpdateCall });

  if (ttsLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!currentCall)
    return (
      <Card sx={{ borderRadius: 4, textAlign: "center", p: 8, height: "100%" }}>
        <Typography color="textSecondary">
          Выберите обзвон из списка слева
        </Typography>
      </Card>
    );

  return (
    <Card
      key={currentCall?.id}
      sx={{
        borderRadius: 4,
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <CardHeader
        title={
          <Typography variant="h6" fontWeight={700}>
            {currentCall.name}
          </Typography>
        }
        action={
          <Button
            variant="contained"
            startIcon={<FileDownloadIcon />}
            onClick={onExport}
          >
            Экспорт Excel
          </Button>
        }
      />

      <CardContent
        sx={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          pt: 0,
        }}
      >
        <SettingsPanel
          categoriesLocal={categoriesLocal}
          currentCall={currentCall}
          handleSave={handleSave}
          isDirty={isDirty}
          pausedLocal={pausedLocal}
          setPausedLocal={setPausedLocal}
          ttsTypeLocal={ttsTypeLocal}
          setTtsTypeLocal={setTtsTypeLocal}
          ttsOptions={ttsOptions}
          setCategoriesLocal={setCategoriesLocal}
          retryLimitLocal={retryLimitLocal}
          setRetryLimitLocal={setRetryLimitLocal}
          setScheduleTemp={setScheduleTemp}
          scheduleLocal={scheduleLocal}
          setScheduleModalOpen={setScheduleModalOpen}
          saving={saving}
          // Пропсы для контроля и email-отчетности
          controlCallEnabledLocal={controlCallEnabledLocal}
          setControlCallEnabledLocal={setControlCallEnabledLocal}
          controlCallNumberLocal={controlCallNumberLocal}
          setControlCallNumberLocal={setControlCallNumberLocal}
          controlCallIntervalLocal={controlCallIntervalLocal}
          setControlCallIntervalLocal={setControlCallIntervalLocal}
          emailReportEnabledLocal={emailReportEnabledLocal}
          setEmailReportEnabledLocal={setEmailReportEnabledLocal}
          emailReportAddressLocal={emailReportAddressLocal}
          setEmailReportAddressLocal={setEmailReportAddressLocal}
          emailReportIntervalLocal={emailReportIntervalLocal}
          setEmailReportIntervalLocal={setEmailReportIntervalLocal}
          triggerStartLocal={triggerStartLocal}
          setTriggerStartLocal={setTriggerStartLocal}
          triggerIntervalLocal={triggerIntervalLocal}
          setTriggerIntervalLocal={setTriggerIntervalLocal}
          triggerFinalLocal={triggerFinalLocal}
          setTriggerFinalLocal={setTriggerFinalLocal}
        />

        <CallsTable
          phoneCalls={phoneCalls}
          loadingMore={loadingMore}
          sentinelRef={sentinelRef}
        />
      </CardContent>

      <ScheduleDialog
        canonicalizeSchedule={canonicalizeSchedule}
        scheduleModalOpen={scheduleModalOpen}
        setScheduleModalOpen={setScheduleModalOpen}
        scheduleTemp={scheduleTemp}
        setScheduleLocal={setScheduleLocal}
        setScheduleTemp={setScheduleTemp}
      />
    </Card>
  );
};

export default CallDetails;
