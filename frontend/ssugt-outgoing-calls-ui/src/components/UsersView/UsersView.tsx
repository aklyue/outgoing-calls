import { useState } from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  MenuItem,
  TablePagination,
  CircularProgress,
  Chip,
  Select,
  Typography,
  FormControl,
  useMediaQuery,
  useTheme,
  Stack,
  Divider,
} from "@mui/material";
import { useDebouncedValue } from "../../hooks/useDebouncedValue/useDebouncedValue";
import { useAuth } from "../../hooks/useAuth/useAuth";
import { useUsers } from "../../hooks/useUsers/useUsers";

const UsersView = () => {
  const isMobile = useMediaQuery(useTheme().breakpoints.down("md"));
  const { isAdmin, isOwner, user: currentUser } = useAuth();

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebouncedValue(search, 300);

  const {
    roleFilter,
    setRoleFilter,
    setPage,
    page,
    rowsPerPage,
    setRowsPerPage,
    sortedItems,
    handleRoleChange,
    isLoading,
    total,
    items,
  } = useUsers({ debouncedSearch, currentUser });

  return (
    <Box
      sx={{ p: 2, display: "flex", flexDirection: "column", height: "100%" }}
    >
      <Typography variant="h6" sx={{ mb: 2 }}>
        Управление пользователями
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <TextField
          label="Поиск по логину"
          size="small"
          placeholder="Введите имя..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <TextField
          select
          label="Фильтр роли"
          size="small"
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(0);
          }}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="all">Все роли</MenuItem>
          <MenuItem value="owner">Гл. админ</MenuItem>
          <MenuItem value="admin">Только админы</MenuItem>
          <MenuItem value="user">Только пользователи</MenuItem>
        </TextField>
      </Box>

      {isMobile ? (
        <Box sx={{ flex: 1, overflow: "auto", mt: 1 }}>
          {sortedItems.map((user) => {
            const isMe = user.id === currentUser?.id;
            const canEdit = isOwner ? !isMe : isAdmin && user.role === "user";

            return (
              <Paper
                key={user.id}
                sx={{
                  mb: 2,
                  p: 2,
                  borderLeft: isMe ? "4px solid #2e7d32" : "none",
                }}
                elevation={1}
              >
                <Stack spacing={1.5}>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                    }}
                  >
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {user.username}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          fontFamily: "monospace",
                          color: "text.secondary",
                          display: "block",
                        }}
                      >
                        ID: {user.id}
                      </Typography>
                    </Box>
                    {isMe && (
                      <Chip
                        label="Вы"
                        color="success"
                        size="small"
                        variant="filled"
                      />
                    )}
                  </Box>

                  <Divider />

                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <Typography variant="body2">Роль:</Typography>
                    <FormControl size="small" sx={{ minWidth: 160 }}>
                      <Select
                        value={user.role}
                        disabled={!canEdit}
                        onChange={(e) =>
                          handleRoleChange(user.id, e.target.value)
                        }
                        sx={{ height: 32, fontSize: "0.875rem" }}
                      >
                        <MenuItem value="user">Пользователь</MenuItem>
                        <MenuItem value="admin">Администратор</MenuItem>
                        <MenuItem value="owner" disabled>
                          Гл. администратор
                        </MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                </Stack>
              </Paper>
            );
          })}
        </Box>
      ) : (
        <TableContainer component={Paper} sx={{ flex: 1, overflow: "auto" }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell width="30%">ID</TableCell>
                <TableCell>Логин</TableCell>
                <TableCell align="right">Роль</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading && items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : (
                sortedItems.map((user) => {
                  const isMe = user.id === currentUser?.id;
                  const canEdit = isOwner
                    ? !isMe
                    : isAdmin && user.role === "user";
                  return (
                    <TableRow key={user.id} hover>
                      <TableCell
                        sx={{
                          fontSize: "0.7rem",
                          color: "text.secondary",
                          fontFamily: "monospace",
                        }}
                      >
                        {user.id}
                        {isMe && (
                          <Chip
                            label="Текущий аккаунт"
                            color="success"
                            variant="outlined"
                            size="small"
                            sx={{
                              ml: 2,
                            }}
                          />
                        )}
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {user.username}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <FormControl
                          size="small"
                          sx={{ m: 0.5, minWidth: 180 }}
                        >
                          <Select
                            value={user.role}
                            disabled={!canEdit}
                            onChange={(e) =>
                              handleRoleChange(user.id, e.target.value)
                            }
                            sx={{
                              fontSize: "0.8rem",
                              height: 32,
                              opacity: user.id === currentUser?.id ? 0.6 : 1,
                            }}
                          >
                            <MenuItem value="user">Пользователь</MenuItem>
                            <MenuItem value="admin">Администратор</MenuItem>
                            <MenuItem value="owner" disabled>
                              Гл. администратор
                            </MenuItem>
                          </Select>
                        </FormControl>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <TablePagination
        component="div"
        count={total}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10));
          setPage(0);
        }}
        labelRowsPerPage="Строк:"
      />
    </Box>
  );
};

export default UsersView;
