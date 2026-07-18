// Create or edit a location, including moving it under a different parent.

import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import {
  LOCATION_TYPE_LABELS,
  type LocationRead,
  type LocationTreeNode,
  type LocationType,
} from "../api/types";
import { findNode, flattenTree, subtreeIds } from "../utils/tree";
import { Modal } from "./Modal";

interface Props {
  onClose: () => void;
  onSaved: (location: LocationRead) => void;
  location?: LocationRead;
  defaultParentId?: string | null;
}

const TYPES = Object.keys(LOCATION_TYPE_LABELS) as LocationType[];

export function LocationFormModal({ onClose, onSaved, location, defaultParentId = null }: Props) {
  const isEdit = Boolean(location);
  const [tree, setTree] = useState<LocationTreeNode[]>([]);
  const [name, setName] = useState(location?.name ?? "");
  const [type, setType] = useState<LocationType>(location?.type ?? "comodo");
  const [parentId, setParentId] = useState<string>(location?.parent_id ?? defaultParentId ?? "");
  const [notes, setNotes] = useState(location?.notes ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getTree().then(setTree).catch(() => setTree([]));
  }, []);

  // When editing, a location cannot move into itself or its own descendants.
  const excludedIds = (() => {
    if (!isEdit || !location) return new Set<string>();
    const node = findNode(tree, location.id);
    return node ? subtreeIds(node) : new Set<string>([location.id]);
  })();
  const options = flattenTree(tree).filter((option) => !excludedIds.has(option.id));

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const saved = location
        ? await api.updateLocation(location.id, {
            name: name.trim(),
            notes: notes.trim() || null,
            parent_id: parentId || null,
          })
        : await api.createLocation({
            name: name.trim(),
            type,
            parent_id: parentId || null,
            notes: notes.trim() || null,
          });
      onSaved(saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível salvar o local.");
      setSaving(false);
    }
  };

  return (
    <Modal title={isEdit ? "Editar local" : "Novo local"} onClose={onClose}>
      <div className="stack">
        <label className="field">
          <span>Nome</span>
          <input
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Armário A"
          />
        </label>
        <label className="field">
          <span>Tipo</span>
          <select
            value={type}
            disabled={isEdit}
            onChange={(event) => setType(event.target.value as LocationType)}
          >
            {TYPES.map((value) => (
              <option key={value} value={value}>
                {LOCATION_TYPE_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Dentro de (opcional)</span>
          <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
            <option value="">— Nível principal (cômodo) —</option>
            {options.map((option) => (
              <option key={option.id} value={option.id}>
                {"  ".repeat(option.depth)}
                {option.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Notas (opcional)</span>
          <textarea
            rows={2}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Qualquer detalhe útil"
          />
        </label>
        {error && <p className="error">{error}</p>}
      </div>
      <div className="row">
        <button type="button" className="btn secondary" onClick={onClose}>
          Cancelar
        </button>
        <button
          type="button"
          className="btn primary"
          disabled={saving || name.trim().length === 0}
          onClick={submit}
        >
          Salvar
        </button>
      </div>
    </Modal>
  );
}
