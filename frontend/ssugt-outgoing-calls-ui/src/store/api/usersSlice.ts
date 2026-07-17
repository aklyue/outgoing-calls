import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { API } from "../../api/api";

export interface User {
  id: string;
  username: string;
  role: string;
}

interface UsersState {
  items: User[];
  total: number;
  isLoading: boolean;
}

export const fetchUsers = createAsyncThunk(
  "users/fetchAll",
  async (params: {
    offset: number;
    limit: number;
    username?: string;
    role?: string;
  }) => {
    const response = await API.get("/users/", { params });
    return response.data;
  },
);

export const updateUser = createAsyncThunk(
  "users/update",
  async ({ id, data }: { id: string; data: any }) => {
    const response = await API.patch(`/users/${id}`, data);
    return response.data;
  },
);

const usersSlice = createSlice({
  name: "users",
  initialState: { items: [], total: 0, isLoading: false } as UsersState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(updateUser.fulfilled, (state, action) => {
        const index = state.items.findIndex((u) => u.id === action.payload.id);
        if (index !== -1) state.items[index] = action.payload;
      });
  },
});

export default usersSlice.reducer;
