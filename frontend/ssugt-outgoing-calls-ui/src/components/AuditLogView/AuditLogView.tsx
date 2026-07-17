import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Stack,
  Collapse,
  IconButton,
  Pagination,
  MenuItem,
  Select,
  CircularProgress,
  TextField,
  InputAdornment,
  useMediaQuery,
  useTheme,
} from "@mui/material";

import HistoryIcon from "@mui/icons-material/History";
import PersonIcon from "@mui/icons-material/Person";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import LanIcon from "@mui/icons-material/Lan";
import SearchIcon from "@mui/icons-material/Search";
import FilterListIcon from "@mui/icons-material/FilterList";
import { PayloadRenderer } from "../ui/PayloadRenderer";
import { useDebouncedValue } from "../../hooks/useDebouncedValue/useDebouncedValue";
import { useAuth } from "../../hooks/useAuth/useAuth";
import { formatLogDate } from "../../utils/formatLogDate";
import { auditMap } from "../../const/auditMap";
import { getIcon } from "../../utils/getIcon";
import { useLogs } from "../../hooks/useLogs/useLogs";

function AuditLogView() {
  const { isAdmin, isOwner } = useAuth();

  const isMobile = useMediaQuery(useTheme().breakpoints.down("md"));

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebouncedValue(searchQuery, 500);

  const {
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
  } = useLogs({ debouncedSearch });

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 4,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderColor: "divider",
        overflow: "hidden",
        boxShadow: 1,
        position: "relative",
      }}
    >
      <Box
        sx={{
          p: 2,
          bgcolor: "grey.50",
          borderBottom: "1px solid",
          borderColor: "divider",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <HistoryIcon fontSize="small" color="action" />
          <Typography variant="subtitle2" fontWeight="bold">
            Журнал аудита
          </Typography>
          {isLoading && <CircularProgress size={16} sx={{ ml: 1 }} />}
        </Stack>

        <Typography
          variant="caption"
          sx={{ color: "text.secondary", fontWeight: 500 }}
        >
          Всего записей: {total}
        </Typography>
      </Box>

      <Box
        sx={{
          p: 2,
          borderBottom: "1px solid",
          borderColor: "divider",
          bgcolor: "#fff",
        }}
      >
        <Stack direction={isMobile ? "column" : "row"} spacing={2}>
          {(isAdmin || isOwner) && (
            <TextField
              size="small"
              placeholder="Поиск по пользователю..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(0);
              }}
              sx={{ flex: 2 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />
          )}
          <TextField
            select
            size="small"
            label="Тип действия"
            value={filterAction}
            onChange={(e) => {
              setFilterAction(e.target.value);
              setPage(0);
            }}
            sx={{ flex: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <FilterListIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          >
            <MenuItem value="all">Все действия</MenuItem>
            {Object.entries(auditMap).map(([key, label]) => (
              <MenuItem key={key} value={key}>
                {label}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
      </Box>

      <Box
        sx={{
          position: "relative",
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {isLoading && (
          <Box
            sx={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "rgba(255, 255, 255, 0.7)",
              backdropFilter: "blur(1px)",
            }}
          >
            <CircularProgress size={40} />
          </Box>
        )}

        <List
          sx={{
            p: 0,
            overflowY: "auto",
            flex: 1,
            opacity: isLoading ? 0.6 : 1,
            transition: "opacity 0.2s",
          }}
        >
          {items.length > 0
            ? items.map((log, index) => {
                const isExpanded = expandedId === log.id;
                const hasPayload = Boolean(log.payload);
                const readableAction =
                  auditMap[log.action_type] || log.action_description;

                return (
                  <React.Fragment key={log.id}>
                    <ListItem
                      disablePadding
                      sx={{
                        flexDirection: "column",
                        alignItems: "stretch",
                        bgcolor: isExpanded ? "action.hover" : "transparent",
                        "&:hover": {
                          bgcolor: "action.hover",
                          cursor: hasPayload ? "pointer" : "default",
                        },
                      }}
                      onClick={() =>
                        hasPayload && setExpandedId(isExpanded ? null : log.id)
                      }
                    >
                      <Box
                        sx={{
                          px: 2,
                          py: 1.5,
                          display: "flex",
                          alignItems: "flex-start",
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
                          {getIcon(log.action_type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box
                              sx={{
                                display: "flex",
                                justifyContent: "space-between",
                              }}
                            >
                              <Typography variant="body2" fontWeight="600">
                                {readableAction}
                              </Typography>
                              <Typography
                                variant="caption"
                                sx={{
                                  color: "text.disabled",
                                  fontVariantNumeric: "tabular-nums",
                                }}
                              >
                                {formatLogDate(log.created_at)}
                              </Typography>
                            </Box>
                          }
                          secondary={
                            <Stack
                              direction="row"
                              spacing={2}
                              sx={{ mt: 0.5 }}
                              alignItems="center"
                            >
                              <Stack
                                direction="row"
                                spacing={0.5}
                                alignItems="center"
                              >
                                <PersonIcon
                                  sx={{ fontSize: 14, color: "text.secondary" }}
                                />
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  {log.username}
                                </Typography>
                              </Stack>
                              <Stack
                                direction="row"
                                spacing={0.5}
                                alignItems="center"
                              >
                                <LanIcon
                                  sx={{ fontSize: 14, color: "text.secondary" }}
                                />
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  {log.ip_address}
                                </Typography>
                              </Stack>
                              {hasPayload && (
                                <Box sx={{ ml: "auto !important" }}>
                                  <IconButton
                                    size="small"
                                    component="div"
                                    color="primary"
                                  >
                                    {isExpanded ? (
                                      <KeyboardArrowUpIcon />
                                    ) : (
                                      <KeyboardArrowDownIcon />
                                    )}
                                  </IconButton>
                                </Box>
                              )}
                            </Stack>
                          }
                          secondaryTypographyProps={{ component: "div" }}
                        />
                      </Box>
                      <Collapse
                        in={isExpanded}
                        timeout="auto"
                        unmountOnExit
                        sx={{ borderTop: "1px solid #efefef" }}
                      >
                        <Box sx={{ px: 2, pb: 2, ml: 5, mt: 1 }}>
                          <PayloadRenderer
                            action={log.action_type}
                            payload={log.payload}
                          />
                        </Box>
                      </Collapse>
                    </ListItem>
                    {index < items.length - 1 && <Divider component="li" />}
                  </React.Fragment>
                );
              })
            : !isLoading && (
                <Box sx={{ p: 4, textAlign: "center" }}>
                  <Typography variant="body2" color="text.disabled">
                    Событий не найдено
                  </Typography>
                </Box>
              )}
        </List>
      </Box>

      <Divider />

      <Box
        sx={{
          px: 2,
          py: 1,
          bgcolor: "grey.50",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Stack
          direction={isMobile ? "column" : "row"}
          alignItems="center"
          spacing={1}
        >
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            ЗАПИСЕЙ:
          </Typography>
          <Select
            value={rowsPerPage}
            onChange={(e) => {
              setRowsPerPage(Number(e.target.value));
              setPage(0);
            }}
            size="small"
            variant="standard"
            disableUnderline
            sx={{ fontSize: "0.75rem", fontWeight: 700, color: "primary.main" }}
          >
            {[5, 10, 25, 50].map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </Stack>

        <Pagination
          count={totalPages}
          page={page + 1}
          onChange={(_, p) => handleChangePage(null, p - 1)}
          color="primary"
          size="small"
          shape="rounded"
          disabled={isLoading}
          siblingCount={isMobile ? 0 : 1}
          boundaryCount={isMobile ? 1 : 2}
        />
      </Box>
    </Paper>
  );
}

export default AuditLogView;
