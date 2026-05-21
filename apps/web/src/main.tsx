import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { router } from "@/app/router";
import "@/index.css";

void useAuthStore.getState().restoreSession();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
