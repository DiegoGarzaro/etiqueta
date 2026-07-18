// Browse the storage tree by location.

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { LocationTreeNode } from "../api/types";
import { LocationTypeIcon } from "../components/Icons";
import { LocationFormModal } from "../components/LocationFormModal";

function TreeRows({ nodes, depth }: { nodes: LocationTreeNode[]; depth: number }) {
  return (
    <>
      {nodes.map((node) => (
        <div key={node.id}>
          <Link
            to={`/locais/${node.id}`}
            className="tree-node"
            style={{ paddingLeft: 10 + depth * 20 }}
          >
            <span className="ico">
              <LocationTypeIcon type={node.type} />
            </span>
            <span>{node.name}</span>
            <span className="count">{node.total_item_count} itens</span>
          </Link>
          {node.children.length > 0 && <TreeRows nodes={node.children} depth={depth + 1} />}
        </div>
      ))}
    </>
  );
}

export default function LocationsPage() {
  const [tree, setTree] = useState<LocationTreeNode[] | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  const load = useCallback(() => {
    api.getTree().then(setTree);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h1 className="page-title">Locais</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to="/etiquetas" className="btn secondary">
            Etiquetas
          </Link>
          <button type="button" className="btn secondary" onClick={() => setAddOpen(true)}>
            + Local
          </button>
        </div>
      </div>

      {tree === null && <p className="spinner">Carregando…</p>}
      {tree !== null && tree.length === 0 && (
        <div className="empty">
          <h3>Comece pela estrutura</h3>
          <p>Crie um cômodo, depois armários, gavetas e caixas dentro dele.</p>
          <button type="button" className="btn primary" onClick={() => setAddOpen(true)}>
            + Local
          </button>
        </div>
      )}
      {tree && tree.length > 0 && (
        <div className="stack" style={{ gap: 2 }}>
          <TreeRows nodes={tree} depth={0} />
        </div>
      )}

      {addOpen && (
        <LocationFormModal
          onClose={() => setAddOpen(false)}
          onSaved={() => {
            setAddOpen(false);
            load();
          }}
        />
      )}
    </>
  );
}
