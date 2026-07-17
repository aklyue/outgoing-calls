import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MainPage } from "./pages/MainPage";
import { LoginPage } from "./pages/LoginPage";
import { useAuth } from "./hooks/useAuth/useAuth";
import { useEffect, type JSX } from "react";
import { useSelector } from "react-redux";
import { type RootState } from "./store";

const AdminRoute = ({ children }: { children: JSX.Element }) => {
  const { user, isAuthenticated } = useSelector(
    (state: RootState) => state.user,
  );

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== "admin" && user?.role !== "owner") {
    return <Navigate to="/" replace />;
  }

  return children;
};

const App: React.FC = () => {
  const { refreshUser, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      refreshUser();
    }
  }, [isAuthenticated, refreshUser]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            isAuthenticated ? <MainPage /> : <Navigate to="/login" replace />
          }
        />

        <Route
          path="/users"
          element={
            <AdminRoute>
              <div>Страница пользователей</div>
            </AdminRoute>
          }
        />
        <Route
          path="/logs"
          element={
            <AdminRoute>
              <div>Страница журнала</div>
            </AdminRoute>
          }
        />

        <Route path="*" element={<div>404 - Страница не найдена</div>} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
