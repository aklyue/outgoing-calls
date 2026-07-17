import { createAction, createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

interface ValidationState {
  advancedSettingsErrors: {
    controlCallNumber: string;
    controlCallInterval: string;
    emailReportAddress: string;
    emailReportInterval: string;
  };
}

const initialState: ValidationState = {
  advancedSettingsErrors: {
    controlCallNumber: "",
    controlCallInterval: "",
    emailReportAddress: "",
    emailReportInterval: "",
  },
};

const validationSlice = createSlice({
  name: "validation",
  initialState,
  reducers: {
    setAdvancedSettingsErrors: (
      state,
      action: PayloadAction<Partial<ValidationState["advancedSettingsErrors"]>>,
    ) => {
      state.advancedSettingsErrors = {
        ...state.advancedSettingsErrors,
        ...action.payload,
      };
    },
    clearAdvancedSettingsErrors: (state) => {
      state.advancedSettingsErrors = initialState.advancedSettingsErrors;
    },
  },
});

export const runAdvancedValidation = createAction<{
  controlCallEnabled: boolean;
  controlCallNumber: string;
  controlCallInterval: number;
  emailReportEnabled: boolean;
  emailReportAddress: string;
  emailReportInterval: number;
}>("validation/runAdvanced");

export const { setAdvancedSettingsErrors, clearAdvancedSettingsErrors } =
  validationSlice.actions;
export default validationSlice.reducer;
