import { lazy, StrictMode, Suspense, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import Layout from "./components/Layout";
import { PinGate } from "./components/PinGate";
import BackupPage from "./pages/BackupPage";
import CategoriesPage from "./pages/CategoriesPage";
import ItemDetailPage from "./pages/ItemDetailPage";
import LocationDetailPage from "./pages/LocationDetailPage";
import LocationsPage from "./pages/LocationsPage";
import SearchPage from "./pages/SearchPage";
import "./styles/app.css";
import "./styles/layout.css";
import "./styles/print.css";

// Heavy pages (QR generation / camera decoding) load on demand.
const LabelsPage = lazy(() => import("./pages/LabelsPage"));
const ScanPage = lazy(() => import("./pages/ScanPage"));
const PrintPage = lazy(() => import("./pages/PrintPage"));

const lazyPage = (node: ReactNode): ReactNode => (
  <Suspense fallback={<p className="spinner">Carregando…</p>}>{node}</Suspense>
);

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/buscar" replace /> },
      { path: "buscar", element: <SearchPage /> },
      { path: "locais", element: <LocationsPage /> },
      { path: "locais/:id", element: <LocationDetailPage /> },
      { path: "itens/:id", element: <ItemDetailPage /> },
      { path: "etiquetas", element: lazyPage(<LabelsPage />) },
      { path: "impressora", element: lazyPage(<PrintPage />) },
      { path: "categorias", element: <CategoriesPage /> },
      { path: "escanear", element: lazyPage(<ScanPage />) },
      { path: "ajustes", element: <BackupPage /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PinGate>
      <RouterProvider router={router} />
    </PinGate>
  </StrictMode>,
);
