import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "../../store";
import { useEffect, useState } from "react";
import { fetchLogs } from "../../store/api/logsSlice";

interface useLogsProps {
  debouncedSearch: string;
}

export const useLogs = ({
  debouncedSearch,
}: useLogsProps) => {
  const dispatch = useDispatch<AppDispatch>();

  const {
    items = [],
    total = 0,
    isLoading,
  } = useSelector((state: RootState) => state.logs);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const [filterAction, setFilterAction] = useState("all");

  useEffect(() => {
    const offset = page * rowsPerPage;
    dispatch(
      fetchLogs({
        limit: rowsPerPage,
        offset,
        username: debouncedSearch || undefined,
        action_type: filterAction === "all" ? undefined : filterAction,
      }),
    );
  }, [dispatch, page, rowsPerPage, debouncedSearch, filterAction]);

  const totalPages = Math.ceil(total / rowsPerPage);

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
    setExpandedId(null);
  };

  return {
    isLoading,
    total,
    setPage,
    setFilterAction,
    filterAction,
    items,
    expandedId,
    setExpandedId,
    rowsPerPage,
    setRowsPerPage,
    totalPages,
    page,
    handleChangePage,
  };
};
