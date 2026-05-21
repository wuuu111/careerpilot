import { useEffect } from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { AppShell } from "@/components/app-shell";
import { AuthPage } from "@/pages/auth-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { GeneratedPage } from "@/pages/generated-page";
import { JobAnalysisPage } from "@/pages/job-analysis-page";
import { MatchingPage } from "@/pages/matching-page";
import { ResumesPage } from "@/pages/resumes-page";
import { TracePage } from "@/pages/trace-page";

export function ProtectedOutlet() {
  const token = useAuthStore((state) => state.token);
  const hydrated = useAuthStore((state) => state.hydrated);
  const restoreSession = useAuthStore((state) => state.restoreSession);

  useEffect(() => {
    if (!hydrated) {
      void restoreSession();
    }
  }, [hydrated, restoreSession]);

  if (!hydrated) {
    return null;
  }
  if (!token) {
    return <Navigate replace to="/login" />;
  }
  return <AppShell />;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <AuthPage mode="login" />,
  },
  {
    path: "/register",
    element: <AuthPage mode="register" />,
  },
  {
    path: "/",
    element: <ProtectedOutlet />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "resumes", element: <ResumesPage /> },
      { path: "job-analysis", element: <JobAnalysisPage /> },
      { path: "matching", element: <MatchingPage /> },
      { path: "generated", element: <GeneratedPage /> },
      { path: "trace", element: <TracePage /> },
    ],
  },
]);
