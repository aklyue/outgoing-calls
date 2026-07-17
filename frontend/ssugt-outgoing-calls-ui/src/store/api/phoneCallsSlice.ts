import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { API } from "../../api/api";

export const fetchPhoneCalls = createAsyncThunk(
  "phoneCalls/fetch",
  async ({
    id,
    offset,
    limit,
    isRefresh,
  }: {
    id: string;
    offset: number;
    limit: number;
    isRefresh: boolean;
  }) => {
    const r = await API.get(`/phone_calls/${id}`, {
      params: { offset, limit },
    });
    const transformed = r.data.map((c: any, i: number) => ({
      ...c,
      id: offset + i + 1,
    }));
    return { data: transformed, isRefresh };
  },
);

const phoneCallsSlice = createSlice({
  name: "phoneCalls",
  initialState: { items: [], loading: false, hasMore: true },
  reducers: {
    clearPhoneCalls: (state) => {
      state.items = [];
      state.hasMore = true;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPhoneCalls.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchPhoneCalls.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.isRefresh
          ? action.payload.data
          : [...state.items, ...action.payload.data];
        state.hasMore = action.payload.data.length === 100;
      });
  },
});

export const { clearPhoneCalls } = phoneCallsSlice.actions;
export default phoneCallsSlice.reducer;
