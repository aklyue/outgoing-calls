import { useCallback, useMemo } from "react";
import { useSnackbar } from "notistack";
import { saveAs } from "file-saver";
import { API } from "../../api/api";
import type { Category } from "../../api/api";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";

export function useApi() {
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();

  const navigate = useNavigate();

  const request = useCallback(
    async <T>(promise: Promise<T>): Promise<T | undefined> => {
      try {
        return await promise;
      } catch (err: any) {
        if (err.response?.status === 401) {
          enqueueSnackbar("Сессия истекла. Пожалуйста, войдите снова.", {
            variant: "warning",
          });
          localStorage.removeItem("isAuthenticated");
          navigate("/login");
          return;
        }

        enqueueSnackbar("Произошла ошибка, повторите попытку позже", {
          variant: "error",
        });
        throw err;
      }
    },
    [enqueueSnackbar],
  );

  const logout = useCallback(async () => {
    await request(API.post("/auth/logout"));
    dispatch({ type: "user/logout/fulfilled" });
    localStorage.removeItem("isAuthenticated");
    navigate("/login");
  }, [request, dispatch]);

  const getBalance = useCallback(async () => {
    const r = await request(API.get("/balance/"));
    return r?.data.balance;
  }, [request]);

  const getCalls = useCallback(
    async (offset = 0, limit = 50, filters = {}) => {
      const r = await request(
        API.get("/calls/", {
          params: {
            offset,
            limit,
            ...filters,
          },
        }),
      );

      const items = r?.data?.items || [];
      const total = r?.data?.total || 0;

      return { items, total };
    },
    [request],
  );

  const getPhoneCalls = useCallback(
    async (id: string, offset = 0, limit = 100) => {
      const r = await request(
        API.get(`/phone_calls/${id}`, { params: { offset, limit } }),
      );
      return r?.data.map((c: any, i: number) => ({ ...c, id: offset + i + 1 }));
    },
    [request],
  );

  const patchCall = useCallback(
    async (
      id: string,
      data: {
        schedule?: any[];
        name?: string;
        is_paused?: boolean;
        retry_limit?: number;
        tts_type?: string | null;
        categories?: Category[];
      },
    ) => {
      const r = await request(API.patch(`/calls/${id}`, data));
      dispatch({ type: "calls/updateSettings", payload: { id, ...data } });
      return r?.data;
    },
    [request, dispatch],
  );

  const deleteCall = useCallback(
    async (id: string) => {
      const r = await request(API.delete(`/calls/${id}`));
      dispatch({ type: "calls/delete", payload: { id } });
      return r?.data;
    },
    [request, dispatch],
  );

  const getSynthesizers = useCallback(async (): Promise<string[]> => {
    const r = await request(API.get("/synthesizers/"));
    return (r?.data as string[]) || [];
  }, [request]);

  const createCall = useCallback(
    async (
      name: string,
      calls: Array<{ phone_number: string; text: string }>,
      startPaused: boolean,
      retryLimit: number,
      schedule: any[],
      ttsType: string,
      categories: Category[],
      // === НАШИ НОВЫЕ ПАРАМЕТРЫ КОНТРОЛЯ И ОТЧЕТОВ ===
      advancedOptions?: {
        control_call_enabled: boolean;
        control_call_number: string | null;
        control_call_interval: number;
        email_report_enabled: boolean;
        email_report_address: string | null;
        email_report_interval: number;
        email_report_trigger_start: boolean;
        email_report_trigger_interval: boolean;
        email_report_trigger_final: boolean;
      },
    ) => {
      const callData = {
        name,
        start_at: new Date().toISOString(),
        calls,
        retry_limit: retryLimit,
        is_paused: startPaused,
        schedule,
        tts_type: ttsType,
        categories,
        // Разворачиваем доп. настройки прямо в тело запроса
        ...advancedOptions,
      };

      const r = await request(API.post("/calls/", callData));

      if (r?.data) {
        dispatch({
          type: "calls/createCall/fulfilled",
          payload: {
            ...callData,
            ...r.data,
          },
        });
      }

      return r?.data;
    },
    [request, dispatch],
  );
  
  const synthesize = useCallback(
    async (text: string, type: string) => {
      const r = await request(
        API.post(
          "/synthesize/",
          { text, type },
          { responseType: "arraybuffer" },
        ),
      );
      return r?.data;
    },
    [request],
  );

  const downloadXlsx = useCallback(
    async (id: string, filename: string) => {
      const r = await request(
        API.get(`/phone_calls/${id}?format=xlsx`, {
          responseType: "arraybuffer",
        }),
      );
      if (r) {
        saveAs(new Blob([r.data]), filename);
        dispatch({
          type: "calls/downloadXlsx/fulfilled",
          payload: { id, filename },
        });
      }
    },
    [request, dispatch],
  );

  const normalizeCallList = useCallback(
    async (file: File): Promise<Blob> => {
      const formData = new FormData();
      formData.append("file", file, file.name);

      const merge_config = [
        {
          concated_column: "Телефон",
          columns: ["Телефон мобильный", "Телефон", "Мобильный телефон"],
          priority_column: "Телефон мобильный",
        },
      ];
      formData.append("config", JSON.stringify(merge_config));

      const res = await request(
        API.post("/normalize_xlsx/", formData, { responseType: "blob" }),
      );
      return res?.data as Blob;
    },
    [request],
  );

  return useMemo(
    () => ({
      getBalance,
      getCalls,
      getPhoneCalls,
      patchCall,
      deleteCall,
      createCall,
      synthesize,
      downloadXlsx,
      normalizeCallList,
      getSynthesizers,
      logout,
    }),
    [
      getBalance,
      getCalls,
      getPhoneCalls,
      patchCall,
      deleteCall,
      createCall,
      synthesize,
      downloadXlsx,
      normalizeCallList,
      getSynthesizers,
      logout,
    ],
  );
}
