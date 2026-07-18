// A single location: its tag, path, child locations, and items.

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { LOCATION_TYPE_LABELS, type Item, type LocationTreeNode } from "../api/types";
import { LocationTypeIcon } from "../components/Icons";
import { ItemCard } from "../components/ItemCard";
import { ItemFormModal } from "../components/ItemFormModal";
import { LocationFormModal } from "../components/LocationFormModal";
import { PathTrail } from "../components/PathTrail";
import { PhotoManager } from "../components/PhotoManager";
import { Tag } from "../components/Tag";
import { findNode } from "../utils/tree";

export default function LocationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [node, setNode] = useState<LocationTreeNode | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    const [tree, locationItems] = await Promise.all([
      api.getTree(),
      api.listItems({ locationId: id }),
    ]);
    const found = findNode(tree, id);
    setNode(found);
    setNotFound(found === null);
    setItems(locationItems);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async () => {
    if (!id || !node) return;
    const confirmed = window.confirm(
      `Excluir "${node.name}" e todo o seu conteúdo? Esta ação não pode ser desfeita.`,
    );
    if (!confirmed) return;
    try {
      await api.deleteLocation(id, true);
      navigate("/locais");
    } catch (err) {
      window.alert(err instanceof ApiError ? err.message : "Não foi possível excluir.");
    }
  };

  if (notFound) {
    return (
      <div className="empty">
        <h3>Local não encontrado</h3>
        <p>
          <Link to="/locais">Voltar para Locais</Link>
        </p>
      </div>
    );
  }

  if (!node) return <p className="spinner">Carregando…</p>;

  return (
    <>
      <Link to="/locais" className="muted">
        ← Locais
      </Link>
      <div style={{ margin: "10px 0 6px" }}>
        <PathTrail segments={node.path} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <h1 className="page-title" style={{ margin: 0 }}>
          {node.name}
        </h1>
        <Tag code={node.full_code} large />
      </div>
      <p className="muted" style={{ marginTop: 6 }}>
        {LOCATION_TYPE_LABELS[node.type]} · {node.total_item_count} itens no total
      </p>
      {node.notes && <p style={{ marginTop: 8 }}>{node.notes}</p>}
      <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
        <button type="button" className="btn secondary" onClick={() => setEditOpen(true)}>
          Editar local
        </button>
        <Link to={`/etiquetas?location=${node.id}`} className="btn secondary">
          Imprimir etiqueta
        </Link>
      </div>

      <div style={{ marginTop: 18 }}>
        <PhotoManager
          photos={node.photos}
          onAdd={async (file) => {
            await api.uploadLocationPhoto(node.id, file);
            await load();
          }}
          onDelete={async (photoId) => {
            await api.deletePhoto(photoId);
            await load();
          }}
        />
      </div>

      {node.children.length > 0 && (
        <>
          <h2 className="page-title" style={{ fontSize: "1.15rem", marginTop: 26 }}>
            Locais aqui
          </h2>
          <div className="stack" style={{ gap: 2 }}>
            {node.children.map((child) => (
              <Link key={child.id} to={`/locais/${child.id}`} className="tree-node">
                <span className="ico">
                  <LocationTypeIcon type={child.type} />
                </span>
                <span>{child.name}</span>
                <span className="count">{child.total_item_count} itens</span>
              </Link>
            ))}
          </div>
        </>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 26,
        }}
      >
        <h2 className="page-title" style={{ fontSize: "1.15rem", margin: 0 }}>
          Itens
        </h2>
        <button type="button" className="btn secondary" onClick={() => setAddOpen(true)}>
          + Item
        </button>
      </div>

      {items.length === 0 ? (
        <div className="empty">
          <h3>Nada por aqui ainda</h3>
          <p>Cadastre o primeiro item deste local.</p>
          <button type="button" className="btn primary" onClick={() => setAddOpen(true)}>
            + Item
          </button>
        </div>
      ) : (
        <div className="stack" style={{ marginTop: 12 }}>
          {items.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      )}

      <div style={{ marginTop: 32 }}>
        <button type="button" className="btn danger" onClick={remove}>
          Excluir local
        </button>
      </div>

      {addOpen && (
        <ItemFormModal
          defaultLocationId={id}
          onClose={() => setAddOpen(false)}
          onSaved={() => {
            setAddOpen(false);
            load();
          }}
        />
      )}

      {editOpen && (
        <LocationFormModal
          location={node}
          onClose={() => setEditOpen(false)}
          onSaved={() => {
            setEditOpen(false);
            load();
          }}
        />
      )}
    </>
  );
}
