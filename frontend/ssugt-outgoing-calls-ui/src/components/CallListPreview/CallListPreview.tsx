import React, { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";

interface Props {
  rows: Record<string, any>[];
  col: string;
}

const CallListPreview: React.FC<Props> = ({ rows, col }) => {
  const [page, setPage] = useState(1);
  const rowsPerPage = 5;

  const columnKeys = useMemo(() => {
    if (!rows.length) return [];
    return Object.keys(rows[0]);
  }, [rows]);

  const visibleRows = useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    return rows.slice(start, start + rowsPerPage);
  }, [rows, page]);

  if (!rows.length) return null;

  return (
    <Box sx={{ mt: 1.5 }}>
      <TableContainer
        component={Paper}
        variant="outlined"
        sx={{
          borderRadius: 2,
          maxHeight: 250,
          overflowY: "auto",
          overflowX: "auto",
          "&::-webkit-scrollbar": { width: 6, height: 6 },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: "#ccc",
            borderRadius: 3,
          },
        }}
      >
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columnKeys.map((key) => (
                <TableCell
                  key={key}
                  sx={{
                    fontWeight: "bold",
                    bgcolor: "#f5f5f5 !important",
                    whiteSpace: "nowrap",
                    zIndex: 2,
                  }}
                >
                  {key}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleRows.map((row, index) => (
              <TableRow key={index} hover>
                {columnKeys.map((key) => (
                  <TableCell
                    key={key}
                    sx={{
                      backgroundColor: key === col ? "#e6fffb" : "inherit",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {row[key]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mt: 2, px: 1 }}
      >
        <Typography variant="body2" color="text.secondary">
          {Math.min((page - 1) * rowsPerPage + 1, rows.length)}-
          {Math.min(page * rowsPerPage, rows.length)} из {rows.length}
        </Typography>

        <Pagination
          count={Math.ceil(rows.length / rowsPerPage)}
          page={page}
          onChange={(_, value) => setPage(value)}
          shape="rounded"
          color="primary"
          size="small"
        />
      </Stack>
    </Box>
  );
};

export default CallListPreview;
