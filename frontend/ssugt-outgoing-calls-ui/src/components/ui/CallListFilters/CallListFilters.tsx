import {
  Box,
  Chip,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
} from "@mui/material";
import React, { useEffect, useState } from "react";

import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Person as PersonIcon,
  FilterList as FilterIcon,
} from "@mui/icons-material";
import { useDebouncedValue } from "../../../hooks/useDebouncedValue/useDebouncedValue";
import { useAuth } from "../../../hooks/useAuth/useAuth";

interface CallListFiltersProps {
  onFiltersChange: (filters: {
    call_name?: string | undefined;
    role?: string | undefined;
    username?: string | undefined;
  }) => void;
}

function CallListFilters({ onFiltersChange }: CallListFiltersProps) {
  const { isAdmin, user: currentUser, isOwner } = useAuth();

  const [searchTerm, setSearchTerm] = useState("");
  const [userSearchTerm, setUserSearchTerm] = useState("");
  const [activeRole, setActiveRole] = useState<string>("all");

  const [debouncedSearch] = useDebouncedValue(searchTerm, 500);
  const [debouncedUserSearch] = useDebouncedValue(userSearchTerm, 500);

  useEffect(() => {
    onFiltersChange({
      call_name: debouncedSearch || undefined,
      role:
        activeRole === "all" || activeRole === "mine" ? undefined : activeRole,
      username:
        activeRole === "mine"
          ? currentUser?.username
          : debouncedUserSearch || undefined,
    });
  }, [debouncedSearch, debouncedUserSearch, activeRole]);
  return (
    <Box
      sx={{
        px: 2,
        pb: 2,
        pt: 2,
        mt: 1,
        borderTop: "1px solid rgba(0, 0, 0, 0.12)",
      }}
    >
      <Stack spacing={1.5}>
        <TextField
          fullWidth
          size="small"
          placeholder="Поиск по названию..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" color="action" />
              </InputAdornment>
            ),
            endAdornment: searchTerm && (
              <InputAdornment position="end">
                <IconButton
                  size="small"
                  onClick={() => {
                    setSearchTerm("");
                  }}
                >
                  <ClearIcon fontSize="inherit" />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        {(isAdmin || isOwner) && (
          <>
            <TextField
              fullWidth
              size="small"
              placeholder="Поиск по создателю..."
              value={userSearchTerm}
              onChange={(e) => {
                setUserSearchTerm(e.target.value);
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonIcon fontSize="small" color="action" />
                  </InputAdornment>
                ),
                endAdornment: userSearchTerm && (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setUserSearchTerm("");
                      }}
                    >
                      <ClearIcon fontSize="inherit" />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              useFlexGap
              sx={{ flexWrap: "wrap", rowGap: 1 }}
            >
              <FilterIcon fontSize="small" color="disabled" />
              {["all", "mine", "owner", "admin", "user"].map((role) => (
                <Chip
                  key={role}
                  label={
                    role === "all"
                      ? "Все"
                      : role === "mine"
                        ? "Мои"
                        : role === "admin"
                          ? "Админы"
                          : role === "owner"
                            ? "Гл. админ"
                            : "Пользователи"
                  }
                  size="small"
                  clickable
                  color={
                    activeRole === role
                      ? role === "admin"
                        ? "error"
                        : role === "owner"
                          ? "secondary"
                          : "info"
                      : "default"
                  }
                  onClick={() => {
                    setActiveRole(role);
                  }}
                  sx={{ height: 24 }}
                />
              ))}
            </Stack>
          </>
        )}
      </Stack>
    </Box>
  );
}

export default CallListFilters;
