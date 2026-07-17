import React from "react";
import {
  Card,
  CardHeader,
  CardContent,
  IconButton,
  List,
  ListItem,
  Avatar,
  Typography,
  CircularProgress,
  Box,
  useMediaQuery,
  useTheme,
  Tooltip,
  Chip,
  Divider,
  Pagination,
} from "@mui/material";
import {
  Add as PlusIcon,
  Phone as PhoneIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
} from "@mui/icons-material";
import { useApi } from "../../hooks/useApi/useApi";
import type { Call } from "../../types/Call";
import { useCallActions } from "../../hooks/useCallActions/useCallActions";
import { CallListEditing } from "../ui/CallListEditing";
import { useAuth } from "../../hooks/useAuth/useAuth";
import { CallListFilters } from "../ui/CallListFilters";
import { ConfirmDialog } from "../ui/ConfirmDialog";

interface CallWithCreator extends Call {
  user?: {
    id: string;
    username: string;
    fullname?: string;
    role?: string;
  };
  user_id?: string;
}

interface Props {
  calls: Call[];
  loading?: boolean;
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newSize: number) => void;
  onFiltersChange: (filters: {
    call_name?: string;
    role?: string;
    username?: string;
  }) => void;
  onSelect: (call: Call) => void;
  onCreate: () => void;
  onDeleted: (payload: { id: string; call: Call }) => void;
  selectedId?: string | number | null;
  onUpdated: (updated: Call) => void;
}

const CallList: React.FC<Props> = ({
  calls,
  loading,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onFiltersChange,
  onSelect,
  onCreate,
  onDeleted,
  selectedId,
  onUpdated,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const { patchCall, deleteCall } = useApi();
  const { isAdmin, user: currentUser, isOwner } = useAuth();

  const {
    itemToDelete,
    editingId,
    editValue,
    setEditValue,
    savingId,
    deletingId,
    startEdit,
    cancelEdit,
    handleSave,
    handleDeleteTrigger,
    cancelDelete,
    handleConfirmDelete,
  } = useCallActions({ patchCall, deleteCall, onDeleted, onUpdated });

  const getCreatorName = (call: CallWithCreator): string => {
    if (call.user?.fullname) return call.user.fullname;
    if (call.user?.username) return call.user.username;
    if (call.user_id) return `ID: ${call.user_id.substring(0, 8)}...`;
    return "Неизвестно";
  };

  const getCreatorColor = (call: CallWithCreator): string => {
    if (call.user?.role === "admin") return theme.palette.error.main;
    if (call.user?.role === "owner") return theme.palette.secondary.main;
    if (call.user_id === currentUser?.id) return theme.palette.success.main;
    return theme.palette.primary.main;
  };

  return (
    <>
      <Card
        sx={{
          borderRadius: 4,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: 1,
        }}
      >
        <CardHeader
          title="Обзвоны"
          titleTypographyProps={{ variant: "h6", fontWeight: "bold" }}
          sx={{ borderBottom: "1px solid transparent", pb: 1 }}
          action={
            <IconButton
              color="primary"
              onClick={onCreate}
              sx={{
                bgcolor: "primary.main",
                color: "white",
                "&:hover": { bgcolor: "primary.dark" },
                borderRadius: 2,
              }}
            >
              <PlusIcon />
            </IconButton>
          }
        />

        <CallListFilters onFiltersChange={onFiltersChange} />

        <Divider />

        <CardContent
          sx={{
            p: "0 !important",
            flex: 1,
            overflowY: "auto",
            minHeight: 0,
            bgcolor: "#fafafa",
            position: "relative",
          }}
        >
          {loading && calls.length === 0 ? (
            <Box
              sx={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                height: "100%",
              }}
            >
              <CircularProgress size={32} />
            </Box>
          ) : calls.length === 0 ? (
            <Box sx={{ p: 4, textAlign: "center", color: "text.secondary" }}>
              <Typography variant="body2">Обзвоны не найдены</Typography>
            </Box>
          ) : (
            <List sx={{ p: 1 }}>
              {calls.map((item) => {
                const isEditing = editingId === item.id;
                const isSelected = selectedId === item.id;
                const callWithCreator = item as CallWithCreator;

                return (
                  <ListItem
                    key={item.id}
                    disablePadding
                    onClick={() => !isEditing && onSelect(item)}
                    sx={{
                      borderRadius: 3,
                      mb: 1,
                      transition: "all 0.2s",
                      cursor: "pointer",
                      bgcolor: isSelected
                        ? "rgba(31, 107, 193, 0.08)"
                        : "background.paper",
                      border: "1px solid",
                      borderColor: isSelected ? "primary.light" : "transparent",
                      "&:hover": {
                        bgcolor: isSelected
                          ? "rgba(31, 107, 193, 0.12)"
                          : "rgba(0, 0, 0, 0.02)",
                      },
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        p: 1.5,
                        width: "100%",
                        gap: 2,
                      }}
                    >
                      <Avatar
                        variant="rounded"
                        sx={{
                          bgcolor: isSelected
                            ? "primary.main"
                            : "primary.light",
                          width: isMobile ? 32 : 40,
                          height: isMobile ? 32 : 40,
                        }}
                      >
                        <PhoneIcon fontSize={isMobile ? "small" : "medium"} />
                      </Avatar>

                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <CallListEditing
                          cancelEdit={cancelEdit}
                          editValue={editValue}
                          handleDelete={handleDeleteTrigger}
                          handleSave={handleSave}
                          isDeleting={deletingId === item.id}
                          isEditing={isEditing}
                          isMobile={isMobile}
                          isSaving={savingId === item.id}
                          setEditValue={setEditValue}
                          startEdit={startEdit}
                          item={item}
                        />

                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mt: 0.5,
                            flexWrap: "wrap",
                          }}
                        >
                          <Typography variant="caption" color="text.secondary">
                            Номеров:{" "}
                            {item.phone_calls?.length ??
                              item.phone_calls_count ??
                              0}
                          </Typography>

                          {(isAdmin || isOwner) && (
                            <Tooltip
                              title={`Создатель: ${getCreatorName(callWithCreator)}`}
                            >
                              <Chip
                                size="small"
                                icon={
                                  callWithCreator.user?.role === "admin" ? (
                                    <AdminIcon />
                                  ) : callWithCreator.user?.role === "owner" ? (
                                    <AdminIcon />
                                  ) : (
                                    <PersonIcon />
                                  )
                                }
                                label={getCreatorName(callWithCreator)}
                                variant="outlined"
                                sx={{
                                  height: 20,
                                  bgcolor: "rgba(0,0,0,0.02)",
                                  borderColor: getCreatorColor(callWithCreator),
                                  color: getCreatorColor(callWithCreator),
                                  "& .MuiChip-label": {
                                    px: 1,
                                    fontSize: "0.7rem",
                                    maxWidth: isMobile ? 80 : 120,
                                  },
                                  "& .MuiChip-icon": {
                                    fontSize: "0.9rem",
                                    ml: 0.5,
                                  },
                                }}
                              />
                            </Tooltip>
                          )}

                          {(callWithCreator.user?.role === "admin" ||
                            callWithCreator.user?.role === "owner") && (
                            <Tooltip
                              title={
                                callWithCreator.user?.role === "admin"
                                  ? "Создано администратором"
                                  : "Создано гл. администратором"
                              }
                            >
                              <Chip
                                size="small"
                                icon={<AdminIcon fontSize="small" />}
                                label={
                                  callWithCreator.user?.role === "admin"
                                    ? "Админ"
                                    : "Гл. админ"
                                }
                                variant="filled"
                                color={
                                  callWithCreator.user?.role === "admin"
                                    ? "error"
                                    : "secondary"
                                }
                                sx={{
                                  height: 20,
                                  "& .MuiChip-label": {
                                    px: 1,
                                    fontSize: "0.7rem",
                                  },
                                  "& .MuiChip-icon": { fontSize: "0.9rem" },
                                }}
                              />
                            </Tooltip>
                          )}
                        </Box>
                      </Box>
                    </Box>
                  </ListItem>
                );
              })}
            </List>
          )}
        </CardContent>

        <Divider />

        <Pagination
          page={page + 1}
          count={Math.ceil(totalCount / pageSize)}
          onChange={(_, p) => onPageChange(p - 1)}
          color="primary"
          size={isMobile ? "small" : "medium"}
          shape="rounded"
          disabled={loading}
          sx={{
            display: "flex",
            justifyContent: "center",
            py: 2,
            bgcolor: "background.paper",
          }}
        />
      </Card>

      <ConfirmDialog
        open={Boolean(itemToDelete)}
        title="Удаление обзвона"
        description={
          <>
            Вы уверены, что хотите удалить <strong>{itemToDelete?.name}</strong>
            ? Это действие необратимо.
          </>
        }
        confirmText="Удалить"
        confirmColor="error"
        loading={Boolean(deletingId)}
        onClose={cancelDelete}
        onConfirm={handleConfirmDelete}
      />
    </>
  );
};

export default CallList;
