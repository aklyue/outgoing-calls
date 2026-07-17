import React from "react";
import {
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
} from "@mui/material";
import { formatDate } from "../../../utils/canonicalizeSchedule";
import { STATUS_COLORS } from "../../../const/STATUS_COLORS";
import { STATUS_MAP } from "../../../const/STATUS_MAP";

interface CallsTableProps {
  phoneCalls: any[];
  loadingMore: boolean | undefined;
  sentinelRef: React.RefObject<HTMLDivElement | null>;
}

function CallsTable({ phoneCalls, loadingMore, sentinelRef }: CallsTableProps) {
  const sortedCalls = React.useMemo(() => {
    if (!phoneCalls) return [];
    const parseTime = (s?: string): number => {
      if (!s) return 0;
      const str = /\d{4}-\d{2}-\d{2}T/.test(s) ? (/[zZ]|[+-]/.test(s) ? s : s + "Z") : s;
      const d = new Date(str);
      const t = d.getTime();
      return Number.isFinite(t) ? t : 0;
    };
    return [...phoneCalls].sort((a, b) => parseTime(a.created_at) - parseTime(b.created_at));
  }, [phoneCalls]);
  return (
    <TableContainer
      component={Paper}
      sx={{
        flex: 1,
        borderRadius: 3,
        overflowY: "auto",
        border: "1px solid",
        borderColor: "divider",
        minHeight: 300
      }}
    >
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            <TableCell width={50}>№</TableCell>
            <TableCell width={140}>Телефон</TableCell>
            <TableCell>Текст</TableCell>
            <TableCell width={130}>Начало</TableCell>
            <TableCell width={130}>Поднял</TableCell>
            <TableCell width={130}>Завершен</TableCell>
            <TableCell width={80}>%</TableCell>
            <TableCell width={120}>Статус</TableCell>
            <TableCell width={150}>Причина</TableCell>
            <TableCell width={150}>Попыток</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedCalls.map((call) => (
            <TableRow key={call.id} hover>
              <TableCell>{call.id}</TableCell>
              <TableCell sx={{ fontWeight: 500 }}>
                {call.phone_number}
              </TableCell>
              <TableCell
                sx={{
                  maxWidth: 200,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
                title={call.synthesis}
              >
                {call.synthesis}
              </TableCell>
              <TableCell>{formatDate(call.ringing_at)}</TableCell>
              <TableCell>{formatDate(call.picked_up_at)}</TableCell>
              <TableCell>{formatDate(call.completed_at)}</TableCell>
              <TableCell>{call.progress}%</TableCell>
              <TableCell
                sx={{
                  color: STATUS_COLORS[call.status] || "#000",
                  fontWeight: 700,
                }}
              >
                {STATUS_MAP[call.status] || "Неизвестно"}
              </TableCell>
              <TableCell
                variant="body"
                sx={{ color: "text.secondary", fontSize: "0.75rem" }}
              >
                {call.cause}
              </TableCell>
              <TableCell> {call.retry_count ?? 0}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Box ref={sentinelRef} sx={{ p: 2, textAlign: "center" }}>
        {loadingMore && <CircularProgress size={20} />}
      </Box>
    </TableContainer>
  );
}

export default CallsTable;
