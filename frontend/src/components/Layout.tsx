// App shell: navigation, page outlet, and the global "add item" FAB.

import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { ScanIcon, SearchIcon, SettingsIcon, TagsIcon, TreeIcon } from "./Icons";
import { ItemFormModal } from "./ItemFormModal";

const NAV = [
  { to: "/buscar", label: "Buscar", icon: <SearchIcon /> },
  { to: "/locais", label: "Locais", icon: <TreeIcon /> },
  { to: "/categorias", label: "Categorias", icon: <TagsIcon /> },
  { to: "/escanear", label: "Escanear", icon: <ScanIcon /> },
  { to: "/ajustes", label: "Ajustes", icon: <SettingsIcon /> },
];

export default function Layout() {
  const [addOpen, setAddOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="shell">
      <nav className="nav">
        <span className="brand">
          Etiqueta<span className="dot">.</span>
        </span>
        {NAV.map((entry) => (
          <NavLink
            key={entry.to}
            to={entry.to}
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            {entry.icon}
            {entry.label}
          </NavLink>
        ))}
      </nav>

      <main className="content">
        <Outlet />
      </main>

      <button
        type="button"
        className="fab"
        aria-label="Adicionar item"
        onClick={() => setAddOpen(true)}
      >
        +
      </button>

      {addOpen && (
        <ItemFormModal
          onClose={() => setAddOpen(false)}
          onSaved={(item) => {
            setAddOpen(false);
            navigate(`/itens/${item.id}`);
          }}
        />
      )}
    </div>
  );
}
