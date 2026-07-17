import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "../../store";
import { fetchUsers, updateUser } from "../../store/api/usersSlice";
import type { User } from "../../store/api/userSlice";

interface useUsersProps {
  debouncedSearch: string;
  currentUser: User | null;
}

export const useUsers = ({
  debouncedSearch,
  currentUser,
}: useUsersProps) => {
  const dispatch = useDispatch<AppDispatch>();
  const { items, total, isLoading } = useSelector(
    (state: RootState) => state.users,
  );

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [roleFilter, setRoleFilter] = useState("all");

  useEffect(() => {
    dispatch(
      fetchUsers({
        offset: page * rowsPerPage,
        limit: rowsPerPage,
        username: debouncedSearch || undefined,
        role: roleFilter === "all" ? undefined : roleFilter,
      }),
    );
  }, [page, rowsPerPage, debouncedSearch, roleFilter, dispatch]);

  const sortedItems = useMemo(() => {
    if (!currentUser) return items;

    const otherUsers = items.filter((u) => u.id !== currentUser.id);
    const me = items.find((u) => u.id === currentUser.id);

    return me ? [me, ...otherUsers] : items;
  }, [items, currentUser]);

  const handleRoleChange = async (userId: string, role: string) => {
    await dispatch(updateUser({ id: userId, data: { role } }));
  };

  return {
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
  };
};
