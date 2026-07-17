import {
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  Edit as EditIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import React from "react";
import type { Call } from "../../../types/Call";

interface CallListEditingProps {
  isEditing: boolean;
  editValue: string;
  setEditValue: (value: string) => void;
  isSaving: boolean;
  startEdit: (e: React.MouseEvent<Element, MouseEvent>, item: Call) => void;
  cancelEdit: () => void;
  handleSave: (
    e: React.MouseEvent<Element, MouseEvent> | React.KeyboardEvent<Element>,
    item: Call,
  ) => Promise<void>;
  handleDelete: (e: React.MouseEvent<Element, MouseEvent>, item: Call) => void;
  item: Call;
  isDeleting: boolean;
  isMobile: boolean;
}

function CallListEditing({
  isEditing,
  editValue,
  setEditValue,
  isSaving,
  startEdit,
  cancelEdit,
  handleSave,
  handleDelete,
  item,
  isDeleting,
  isMobile,
}: CallListEditingProps) {
  return (
    <>
      {isEditing ? (
        <>
          <TextField
            autoFocus
            size="small"
            fullWidth
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave(e, item);
              if (e.key === "Escape") cancelEdit();
            }}
            onClick={(e) => e.stopPropagation()}
            disabled={isSaving}
            sx={{ bgcolor: "white" }}
          />
          <Stack direction="row" spacing={0.5}>
            <IconButton
              size="small"
              color="success"
              onClick={(e) => handleSave(e, item)}
              disabled={isSaving}
            >
              <CheckIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                cancelEdit();
              }}
              disabled={isSaving}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Stack>
        </>
      ) : (
        <>
          <Typography
            variant="subtitle2"
            noWrap
            sx={{ fontWeight: 600, flex: 1 }}
          >
            {item.name}
          </Typography>
          <Stack
            className="hover-actions"
            direction="row"
            spacing={0.5}
            sx={{
              opacity: 1,
              transition: "opacity 0.2s",
              ml: 1,
            }}
          >
            <Tooltip title="Переименовать">
              <IconButton size="small" onClick={(e) => startEdit(e, item)}>
                <EditIcon fontSize="inherit" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Удалить">
              <IconButton
                size="small"
                color="error"
                onClick={(e) => handleDelete(e, item)}
                disabled={isDeleting}
              >
                <DeleteIcon fontSize="inherit" />
              </IconButton>
            </Tooltip>
          </Stack>
        </>
      )}
    </>
  );
}

export default CallListEditing;
