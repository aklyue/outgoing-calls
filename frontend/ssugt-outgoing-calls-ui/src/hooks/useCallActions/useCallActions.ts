import { useState } from "react";
import type { Call } from "../../types/Call";
import type { Category } from "../../api/api";

interface UseCallActionsProps {
  patchCall: (
    id: string,
    data: {
      is_paused?: boolean | undefined;
      name?: string | undefined;
      retry_limit?: number | undefined;
      schedule?: any[] | undefined;
      tts_type?: string | null | undefined;
      categories?: Category[] | undefined;
    },
  ) => Promise<any>;
  deleteCall: (id: string) => Promise<any>;
  onDeleted: (payload: { id: string; call: Call }) => void;
  onUpdated: (updated: Call) => void;
}

export const useCallActions = ({
  patchCall,
  onDeleted,
  deleteCall,
  onUpdated,
}: UseCallActionsProps) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [itemToDelete, setItemToDelete] = useState<Call | null>(null);

  const startEdit = (e: React.MouseEvent, item: Call) => {
    e.stopPropagation();
    setEditingId(item.id);
    setEditValue(item.name || "");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const handleSave = async (
    e: React.MouseEvent | React.KeyboardEvent,
    item: Call,
  ) => {
    e.stopPropagation();
    const name = editValue.trim();
    if (!name || name === item.name || savingId || deletingId) {
      cancelEdit();
      return;
    }

    setSavingId(item.id);
    try {
      const updatedCall = await patchCall(item.id, { name });
      item.name = name;
      onUpdated(updatedCall);
      cancelEdit();
    } finally {
      setSavingId(null);
    }
  };

  const handleDeleteTrigger = (e: React.MouseEvent, item: Call) => {
    e.stopPropagation();
    setItemToDelete(item);
  };

  const cancelDelete = () => {
    setItemToDelete(null);
  };

  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;

    const item = itemToDelete;
    setItemToDelete(null);
    setDeletingId(item.id);

    try {
      await deleteCall(item.id);
      onDeleted({ id: item.id, call: item });
    } catch (err) {
      console.error("Ошибка при удалении:", err);
    } finally {
      setDeletingId(null);
    }
  };

  return {
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
  };
};
