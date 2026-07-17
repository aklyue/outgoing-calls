import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
} from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  useMediaQuery,
  useTheme,
} from "@mui/material";

import { Empty } from "../../components/Empty";

import { useApi } from "../../hooks/useApi/useApi";
import { CreateCallModal } from "../../components/CreateCallModal";
import { CallList } from "../../components/CallList";
import { CallDetails } from "../../components/CallDetails";
import { useBalance } from "../../hooks/useBalance/useBalance";

import type { View } from "../../types/View";
import { useCalls } from "../../hooks/useCalls/useCalls";
import { usePhoneCalls } from "../../hooks/usePhoneCalls/usePhoneCalls";
import { useAppPollers } from "../../hooks/useAppPollers/useAppPollers";
import { Footer } from "../../components/ui/Footer";
import { RegisterView } from "../../components/RegisterView";
import { AuditLogView } from "../../components/AuditLogView";
import { UsersView } from "../../components/UsersView";

interface Props {}

function MainPage(props: Props) {
  const { getBalance, getCalls, getPhoneCalls, patchCall, downloadXlsx } =
    useApi();

  const isMobile = useMediaQuery(useTheme().breakpoints.down("md"));

  const [activeView, setActiveView] = useState<View>(
    isMobile ? "users" : "calls",
  );
  const [modalOpen, setModalOpen] = useState(false);

  const activeViewRef = useRef(activeView);

  const { loadBalance, balanceText } = useBalance({ getBalance });

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const handleBackToUsers = () => {
    setActiveView("calls");
  };

  const {
    calls,
    setCalls,
    totalCount,
    callsLoading,
    callsHasMore,
    loadCalls,
    refreshCallsSnapshot,
    setFilters,
    filters,
    callsOffset,
    callsOffsetRef,
  } = useCalls({
    getCalls,
    activeViewRef,
  });

  const {
    currentCall,
    currentCallRef,
    phoneCalls,
    phoneCallsLoading,
    phoneCallsHasMore,
    loadPhoneCalls,
    refreshPhoneCallsSnapshot,
    phoneCallsOffsetRef,
    phoneCallsOffset,
    // togglePaused,
    onCallDeleted,
    selectCall,
  } = usePhoneCalls({
    getPhoneCalls,
    activeViewRef,
    patchCall,
    setCalls,
  });

  useEffect(() => {
    activeViewRef.current = activeView;
    callsOffsetRef.current = callsOffset;
    phoneCallsOffsetRef.current = phoneCallsOffset;
    currentCallRef.current = currentCall;
  });

  const handleFiltersChange = useCallback(
    (newFilters: any) => {
      setPage(0);
      setFilters(newFilters);

      loadCalls(true, {
        offset: 0,
        limit: pageSize,
        ...newFilters,
      });
    },
    [pageSize, loadCalls],
  );

  useEffect(() => {
    if (activeView === "calls") {
      const offset = page * pageSize;
      loadCalls(true, { offset, limit: pageSize });
    }
  }, [page, pageSize, activeView]);

  const memoizedFilters = useMemo(
    () => ({
      ...filters,
      page,
      pageSize,
    }),
    [filters, page, pageSize],
  );

  useAppPollers({
    loadBalance,
    loadCalls,
    refreshCallsSnapshot: () =>
      refreshCallsSnapshot({
        offset: page * pageSize,
        limit: pageSize,
        ...filters,
      }),
    refreshPhoneCallsSnapshot,
    filters: memoizedFilters,
  });

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        bgcolor: "#f5f7fa",
      }}
    >
      <Box
        component="main"
        sx={{
          flex: 1,
          display: "flex",
          overflow: "hidden",
          p: 2,
          gap: 2,
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        {activeView === "calls" ? (
          <>
            <Box
              sx={{
                flex: { xs: "none", md: 3 },
                width: { xs: "100%", md: "auto" },
                display: "flex",
                flexDirection: "column",
                minWidth: { md: "300px" },
                height: { md: "calc(100vh - 120px)" },
                // position: { md: "sticky" },
                minHeight: 0,
              }}
            >
              <CallList
                calls={calls}
                loading={callsLoading}
                totalCount={totalCount}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={(newSize) => {
                  setPageSize(newSize);
                  setPage(0);
                }}
                onFiltersChange={handleFiltersChange}
                onSelect={selectCall}
                onCreate={() => setModalOpen(true)}
                onDeleted={onCallDeleted}
                selectedId={currentCall?.id}
                onUpdated={(updated) => {
                  setCalls((prev) =>
                    prev.map((c) => (c.id === updated.id ? updated : c)),
                  );
                  if (currentCall?.id === updated.id) {
                    selectCall(updated);
                  }
                }}
              />
            </Box>

            <Box
              sx={{
                flex: { xs: "none", md: 9 },
                display: { xs: currentCall ? "flex" : "none", md: "flex" },
                flexDirection: "column",
                minWidth: 0,
                height: { md: "calc(100vh - 120px)" },
                minHeight: 0,
                borderRadius: 4,
              }}
            >
              <CallDetails
                key={currentCall?.id}
                currentCall={currentCall}
                phoneCalls={phoneCalls}
                loadingMore={phoneCallsLoading}
                hasMore={phoneCallsHasMore}
                // onTogglePaused={togglePaused}
                onExport={() =>
                  downloadXlsx(currentCall.id, `${currentCall.name}.xlsx`)
                }
                onLoadMore={() => loadPhoneCalls(false)}
                onUpdateCall={(updated) => {
                  selectCall(updated);
                  setCalls((prev) =>
                    prev.map((c) => (c.id === updated.id ? updated : c)),
                  );
                }}
              />
            </Box>
          </>
        ) : activeView === "register" ? (
          <RegisterView />
        ) : activeView === "journal" ? (
          <Box
            sx={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              height: "calc(100vh - 115px)",
            }}
          >
            <AuditLogView />
          </Box>
        ) : (
          activeView === "users" && (
            <Box
              sx={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                height: "calc(100vh - 115px)",
              }}
            >
              <UsersView />
            </Box>
          )
        )}
      </Box>

      <Footer
        activeView={activeView}
        balanceText={balanceText}
        setActiveView={setActiveView}
      />

      <CreateCallModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => {
          setModalOpen(false);
          loadCalls(true);
        }}
      />
    </Box>
  );
}

export default MainPage;
