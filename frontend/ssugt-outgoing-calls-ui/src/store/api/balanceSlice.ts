import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { API as api } from "../../api/api";

export const fetchBalance = createAsyncThunk("balance/fetch", async () => {
  const response = await api.get("/balance/");
  return response.data.balance;
});

const balanceSlice = createSlice({
  name: "balance",
  initialState: { value: "0.00", loading: false },
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchBalance.fulfilled, (state, action) => {
      state.value = action.payload ?? "0.00";
    });
  },
});

export default balanceSlice.reducer;
