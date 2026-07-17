import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { API } from "../../api/api";

export interface User {
  id: string;
  username: string;
  email?: string;
  role: "user" | "admin" | "owner";
  created_at?: string;
}

interface UserState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}

const initialState: UserState = {
  user: null,
  isLoading: false,
  error: null,
  isAuthenticated: !!localStorage.getItem("isAuthenticated"),
};

export const login = createAsyncThunk(
  "user/login",
  async (
    { username, password }: { username: string; password: string },
    { rejectWithValue },
  ) => {
    try {
      const response = await API.post("/auth/login", { username, password });
      localStorage.setItem("isAuthenticated", "true");
      return response.data;
    } catch (err: any) {
      const detail = err.response?.data?.detail || "Ошибка при входе";
      return rejectWithValue(detail);
    }
  },
);

export const register = createAsyncThunk(
  "user/register",
  async (
    data: { username: string; password: string; role?: string },
    { rejectWithValue },
  ) => {
    try {
      const response = await API.post("/auth/register", {
        username: data.username,
        password: data.password,
        role: data.role || "user",
      });
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || "Ошибка регистрации";
      return rejectWithValue(errorMessage);
    }
  },
);

export const fetchCurrentUser = createAsyncThunk(
  "user/fetchCurrentUser",
  async (_, { rejectWithValue }) => {
    try {
      const response = await API.get("/auth/me");
      return response.data;
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem("isAuthenticated");
      }
      return rejectWithValue(
        err.response?.data?.detail || "Не удалось загрузить пользователя",
      );
    }
  },
);

export const logout = createAsyncThunk(
  "user/logout",
  async (_, { rejectWithValue }) => {
    try {
      await API.post("/auth/logout");
    } catch (err: any) {
    } finally {
      localStorage.removeItem("isAuthenticated");
    }
  },
);

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })

      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      .addCase(fetchCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.isLoading = false;
        state.user = null;
        state.isAuthenticated = false;
      })

      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError } = userSlice.actions;
export default userSlice.reducer;
