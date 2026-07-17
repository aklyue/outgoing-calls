import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
  Grid,
} from "@mui/material";

import { useApi } from "../../hooks/useApi/useApi";
import type { Category } from "../../api/api";
import { CallListPreview } from "../CallListPreview";
import { ScheduleCard } from "../ScheduleCard";
import { DEFAULT_SCHEDULE } from "../../const/DEFAULT_SCHEDULE";
import { useTemplateEditor } from "../../hooks/useTemplateEditor/useTemplateEditor";
import { useTts } from "../../hooks/useTts/useTts";
import { useCallFileManager } from "../../hooks/useCallFileManager/useCallFileManager";
import { mapTemplateToCalls } from "../../utils/callHelpers";
import { GeneralSettingsTab } from "../ui/GeneralSettingsTab";
import AdvancedSettingsTab from "../ui/AdvancedSettingsTab";

import { useAdvancedSettingsValidation } from "../../hooks/useAdvancedSettingsValidation/useAdvancedSettingsValidation";

const CreateCallModal = ({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) => {
  const { normalizeCallList, createCall, getSynthesizers } = useApi();

  const [activeTab, setActiveTab] = useState(0);
  const [callName, setCallName] = useState(
    `Тестовый обзвон от ${new Date().toLocaleDateString("ru-RU")}`,
  );

  const [isPaused, setIsPaused] = useState(false);
  const [retryLimit, setRetryLimit] = useState(3);
  const [categoriesSelected, setCategoriesSelected] = useState<string[]>([
    "ru_mobile_numbers",
    "ru_city_numbers",
  ]);

  const [pauseMs, setPauseMs] = useState(1000);

  const [callSchedule, setCallSchedule] = useState<any[]>(
    JSON.parse(JSON.stringify(DEFAULT_SCHEDULE)),
  );

  const { ttsOptions, ttsType, setTtsType, ttsLoading, ttsExtraText } = useTts({
    open,
    getSynthesizers,
  });

  const [controlCallEnabled, setControlCallEnabled] = useState(false);
  const [controlCallNumber, setControlCallNumber] = useState("");
  const [controlCallInterval, setControlCallInterval] = useState(50);

  const [emailReportEnabled, setEmailReportEnabled] = useState(false);
  const [emailReportAddress, setEmailReportAddress] = useState("");
  const [emailReportInterval, setEmailReportInterval] = useState(100);

  const [triggerStart, setTriggerStart] = useState(false);
  const [triggerInterval, setTriggerInterval] = useState(false);
  const [triggerFinal, setTriggerFinal] = useState(false);

  const {
    textTemplate,
    textAreaRef,
    editorWrapRef,
    showAutocomplete,
    autocompletePos,
    hovered,
    insertToken,
    handleInput,
    handleKeyDown,
  } = useTemplateEditor();

  const {
    columns,
    finalDf,
    phoneColumn,
    setPhoneColumn,
    handleFileUpload,
    fileName,
  } = useCallFileManager({ normalizeCallList });

  const advancedErrors = useAdvancedSettingsValidation({
    controlCallEnabled,
    controlCallNumber,
    controlCallInterval,
    emailReportEnabled,
    emailReportAddress,
    emailReportInterval,
  });

  const hasAdvancedErrors = Object.values(advancedErrors).some(
    (err) => err !== "",
  );

  const canSubmit =
    callName &&
    textTemplate &&
    finalDf.length > 0 &&
    phoneColumn &&
    ttsType &&
    categoriesSelected.length > 0 &&
    !hasAdvancedErrors;

  const onSubmit = async () => {
    const calls = mapTemplateToCalls(finalDf, textTemplate, phoneColumn);

    await createCall(
      callName,
      calls,
      isPaused,
      retryLimit,
      callSchedule,
      ttsType,
      categoriesSelected as Category[],
      {
        control_call_enabled: controlCallEnabled,
        control_call_number: controlCallNumber || null,
        control_call_interval: controlCallInterval,

        email_report_enabled: emailReportEnabled,
        email_report_address: emailReportAddress || null,
        email_report_interval: emailReportInterval,

        email_report_trigger_start: triggerStart,
        email_report_trigger_interval: triggerInterval,
        email_report_trigger_final: triggerFinal,
      },
    );
    onCreated();
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Создание обзвона</DialogTitle>
      <DialogContent dividers sx={{ p: 0 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="fullWidth"
        >
          <Tab label="Основные настройки" />
          <Tab label="Дополнительные настройки" />
          <Tab label="Расписание" />
          <Tab label="Предпросмотр" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && (
            <GeneralSettingsTab
              autocompletePos={autocompletePos}
              callName={callName}
              categoriesSelected={categoriesSelected}
              columns={columns}
              editorWrapRef={editorWrapRef}
              textAreaRef={textAreaRef}
              showAutocomplete={showAutocomplete}
              hovered={hovered}
              insertToken={insertToken}
              handleInput={handleInput}
              finalDf={finalDf}
              handleFileUpload={handleFileUpload}
              phoneColumn={phoneColumn}
              setPhoneColumn={setPhoneColumn}
              retryLimit={retryLimit}
              setRetryLimit={setRetryLimit}
              isPaused={isPaused}
              setIsPaused={setIsPaused}
              ttsType={ttsType}
              setTtsType={setTtsType}
              ttsOptions={ttsOptions}
              ttsLoading={ttsLoading}
              ttsExtraText={ttsExtraText}
              pauseMs={pauseMs}
              setPauseMs={setPauseMs}
              setCallName={setCallName}
              setCategoriesSelected={setCategoriesSelected}
              textTemplate={textTemplate}
              fileName={fileName}
              handleKeyDown={handleKeyDown}
            />
          )}

          {activeTab === 1 && (
            <AdvancedSettingsTab
              controlCallEnabled={controlCallEnabled}
              setControlCallEnabled={setControlCallEnabled}
              controlCallNumber={controlCallNumber}
              setControlCallNumber={setControlCallNumber}
              controlCallInterval={controlCallInterval}
              setControlCallInterval={setControlCallInterval}
              emailReportEnabled={emailReportEnabled}
              setEmailReportEnabled={setEmailReportEnabled}
              emailReportAddress={emailReportAddress}
              setEmailReportAddress={setEmailReportAddress}
              emailReportInterval={emailReportInterval}
              setEmailReportInterval={setEmailReportInterval}
              triggerStart={triggerStart}
              setTriggerStart={setTriggerStart}
              triggerInterval={triggerInterval}
              setTriggerInterval={setTriggerInterval}
              triggerFinal={triggerFinal}
              setTriggerFinal={setTriggerFinal}
              errors={advancedErrors}
            />
          )}

          {activeTab === 2 && (
            <Grid container spacing={2}>
              {callSchedule.map((day, idx) => (
                <Grid
                  key={day.weekday}
                  sx={{
                    xs: 12,
                    md: 4,
                    height: "fit-content",
                  }}
                >
                  <ScheduleCard
                    day={day}
                    idx={idx}
                    minChannels={1}
                    maxChannels={5}
                    onUpdateDay={(dayIdx, updatedDay) => {
                      const newSchedule = [...callSchedule];
                      newSchedule[dayIdx] = updatedDay;
                      setCallSchedule(newSchedule);
                    }}
                    onAddRange={(dayIdx) => {
                      const newSchedule = [...callSchedule];
                      newSchedule[dayIdx].time_ranges.push({
                        start_time_at: "09:00",
                        end_time_at: "18:00",
                        max_num_channels_occupied: 1,
                      });
                      setCallSchedule(newSchedule);
                    }}
                    onRemoveRange={(dayIdx, rangeIdx) => {
                      const newSchedule = [...callSchedule];
                      newSchedule[dayIdx].time_ranges.splice(rangeIdx, 1);
                      setCallSchedule(newSchedule);
                    }}
                  />
                </Grid>
              ))}
            </Grid>
          )}

          {activeTab === 3 && (
            <CallListPreview rows={finalDf} col={phoneColumn} />
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose}>Отмена</Button>
        <Button variant="contained" onClick={onSubmit} disabled={!canSubmit}>
          Создать обзвон
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateCallModal;
