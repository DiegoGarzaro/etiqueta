// A single item: its location tag, path, categories, and edit/delete actions.

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Item } from "../api/types";
import { CategoryChip } from "../components/CategoryChip";
import { ItemFormModal } from "../components/ItemFormModal";
import { PathTrail } from "../components/PathTrail";
import { PhotoManager } from "../components/PhotoManager";
import { Tag } from "../components/Tag";

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<Item | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      setItem(await api.getItem(id));
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNotFound(true);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async () => {
    if (!item) return;
    if (!window.confirm(`Excluir "${item.name}"?`)) return;
    await api.deleteItem(item.id);
    navigate(`/locais/${item.location.id}`);
  };

  if (notFound) {
    return (
      <div className="empty">
        <h3>Item não encontrado</h3>
        <p>
          <Link to="/buscar">Voltar para Buscar</Link>
        </p>
      </div>
    );
  }

  if (!item) return <p className="spinner">Carregando…</p>;

  return (
    <>
      <Link to={`/locais/${item.location.id}`} className="muted">
        ← {item.location.name}
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", marginTop: 10 }}>
        <h1 className="page-title" style={{ margin: 0 }}>
          {item.name}
        </h1>
        {item.quantity !== 1 && <span className="qty">×{item.quantity}</span>}
      </div>

      <div style={{ margin: "12px 0" }}>
        <Link to={`/locais/${item.location.id}`}>
          <Tag code={item.location.full_code} large />
        </Link>
        <div style={{ marginTop: 8 }}>
          <PathTrail segments={item.location.path} />
        </div>
      </div>

      {item.categories.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "12px 0" }}>
          {item.categories.map((category) => (
            <CategoryChip key={category.id} category={category} />
          ))}
        </div>
      )}

      {item.description && <p>{item.description}</p>}
      {item.notes && <p className="muted">{item.notes}</p>}

      <div style={{ marginTop: 20 }}>
        <PhotoManager
          photos={item.photos}
          onAdd={async (file) => {
            await api.uploadItemPhoto(item.id, file);
            setItem(await api.getItem(item.id));
          }}
          onDelete={async (photoId) => {
            await api.deletePhoto(photoId);
            setItem(await api.getItem(item.id));
          }}
        />
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 28 }}>
        <button type="button" className="btn primary" onClick={() => setEditOpen(true)}>
          Editar
        </button>
        <button type="button" className="btn danger" onClick={remove}>
          Excluir
        </button>
      </div>

      {editOpen && (
        <ItemFormModal
          item={item}
          onClose={() => setEditOpen(false)}
          onSaved={(saved) => {
            setEditOpen(false);
            setItem(saved);
          }}
        />
      )}
    </>
  );
}
