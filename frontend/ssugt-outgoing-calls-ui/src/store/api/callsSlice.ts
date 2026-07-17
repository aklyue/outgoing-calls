import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { API } from "../../api/api";

// Загрузка списка (с поддержкой бесконечного скролла)
export const fetchCalls = createAsyncThunk(
  "calls/fetch",
  async ({
    offset,
    limit,
    isRefresh,
  }: {
    offset: number;
    limit: number;
    isRefresh: boolean;
  }) => {
    const r = await API.get("/calls/", { params: { offset, limit } });
    return { data: r.data, isRefresh };
  },
);

// Тихое обновление статусов (поллинг)
export const refreshCallsSnapshot = createAsyncThunk(
  "calls/refreshSnapshot",
  async (limit: number) => {
    const r = await API.get("/calls/", { params: { offset: 0, limit } });
    return r.data;
  },
);

export const patchCallAction = createAsyncThunk(
  "calls/patch",
  async ({ id, data }: { id: string; data: any }) => {
    const r = await API.patch(`/calls/${id}`, data);
    return r.data;
  },
);

export const deleteCallAction = createAsyncThunk(
  "calls/delete",
  async (id: string) => {
    await API.delete(`/calls/${id}`);
    return id;
  },
);

const callsSlice = createSlice({
  name: "calls",
  initialState: {
    items: [] as any[],
    loading: false,
    hasMore: true,
    patchingId: null as string | null,
    deletingId: null as string | null,
  },
  reducers: {
    setCallsLocal: (state, action) => {
      state.items = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCalls.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchCalls.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.isRefresh
          ? action.payload.data
          : [...state.items, ...action.payload.data];
        state.hasMore = action.payload.data.length === 50;
      })
      .addCase(refreshCallsSnapshot.fulfilled, (state, action) => {
        state.items = action.payload; // Тихое обновление без смены loading
      })
      .addCase(deleteCallAction.fulfilled, (state, action) => {
        state.items = state.items.filter((c) => c.id !== action.payload);
        state.deletingId = null;
      })
      .addCase(deleteCallAction.pending, (state, action) => {
        state.deletingId = action.meta.arg;
      })
      .addCase(deleteCallAction.rejected, (state) => {
        state.deletingId = null;
      })
      .addCase(patchCallAction.fulfilled, (state, action) => {
        const index = state.items.findIndex((c) => c.id === action.payload.id);
        state.patchingId = null;
        if (index !== -1) state.items[index] = action.payload;
      })
      .addCase(patchCallAction.pending, (state, action) => {
        state.patchingId = action.meta.arg.id;
      })
      .addCase(patchCallAction.rejected, (state) => {
        state.patchingId = null;
      });
  },
});

export const { setCallsLocal } = callsSlice.actions;
export default callsSlice.reducer;
