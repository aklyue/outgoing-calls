import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { API } from "../../api/api";

interface FetchLogsParams {
  limit?: number;
  offset?: number;
  user_id?: string;
  username?: string;
  action_type?: string;
}

interface FetchLogsResponse {
  items: LogEntry[];
  total: number;
  offset: number;
  limit: number;
}

export interface LogEntry {
  id: string;
  user_id: string;
  username: string;
  action_type: string;
  action_description: string;
  payload: any;
  ip_address: string;
  created_at: string;
}

export const fetchLogs = createAsyncThunk(
  "logs/fetchAll",
  async (params: FetchLogsParams = {}) => {
    const response = await API.get<FetchLogsResponse>("/logs/", { params });
    return response.data;
  },
);

interface LogsState {
  items: LogEntry[];
  total: number;
  isLoading: boolean;
  limit: number;
  offset: number;
}

const initialState: LogsState = {
  items: [],
  total: 0,
  isLoading: false,
  limit: 50,
  offset: 0,
};

const logsSlice = createSlice({
  name: "logs",
  initialState,
  reducers: {
    resetLogs: (state) => {
      state.items = [];
      state.total = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchLogs.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchLogs.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
        state.limit = action.payload.limit;
        state.offset = action.payload.offset;
      })
      .addCase(fetchLogs.rejected, (state) => {
        state.isLoading = false;
      });
  },
});

export const { resetLogs } = logsSlice.actions;
export default logsSlice.reducer;
