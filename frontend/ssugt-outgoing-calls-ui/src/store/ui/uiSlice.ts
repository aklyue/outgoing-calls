// src/store/uiSlice.ts
import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { View } from "../../types/View";

interface UIState {
  activeView: View;
  selectedCall: any | null;
}

const initialState: UIState = {
  activeView: "calls",
  selectedCall: null,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setActiveView: (state, action: PayloadAction<View>) => {
      state.activeView = action.payload;
    },
    selectCall: (state, action: PayloadAction<any | null>) => {
      state.selectedCall = action.payload;
    },
  },
});

export const { setActiveView, selectCall } = uiSlice.actions;
export default uiSlice.reducer;
