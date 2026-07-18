// Create or edit an item: name, quantity, location (move), and categories.

import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Category, Item, LocationTreeNode } from "../api/types";
import { flattenTree } from "../utils/tree";
import { Modal } from "./Modal";

interface Props {
  onClose: () => void;
  onSaved: (item: Item) => void;
  defaultLocationId?: string;
  item?: Item;
}

export function ItemFormModal({ onClose, onSaved, defaultLocationId, item }: Props) {
  const isEdit = Boolean(item);
  const [tree, setTree] = useState<LocationTreeNode[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState(item?.name ?? "");
  const [quantity, setQuantity] = useState(item?.quantity ?? 1);
  const [description, setDescription] = useState(item?.description ?? "");
  const [notes, setNotes] = useState(item?.notes ?? "");
  const [locationId, setLocationId] = useState(item?.location.id ?? defaultLocationId ?? "");
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(
    new Set(item?.categories.map((category) => category.id) ?? []),
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getTree().then(setTree).catch(() => setTree([]));
    api.listCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  const options = flattenTree(tree);

  const toggleCategory = (id: string) => {
    setSelectedCategories((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const submit = async () => {
    setSaving(true);
    setError(null);
    const payload = {
      name: name.trim(),
      quantity,
      description: description.trim() || null,
      notes: notes.trim() || null,
      location_id: locationId,
      category_ids: [...selectedCategories],
    };
    try {
      const saved = item
        ? await api.updateItem(item.id, payload)
        : await api.createItem(payload);
      onSaved(saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível salvar o item.");
      setSaving(false);
    }
  };

  const canSave = name.trim().length > 0 && locationId.length > 0 && !saving;

  return (
    <Modal title={isEdit ? "Editar item" : "Novo item"} onClose={onClose}>
      <div className="stack">
        <label className="field">
          <span>Nome do item</span>
          <input
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Carregador USB-C"
          />
        </label>
        <div style={{ display: "flex", gap: 12 }}>
          <label className="field" style={{ width: 110 }}>
            <span>Quantidade</span>
            <input
              type="number"
              min={0}
              value={quantity}
              onChange={(event) => setQuantity(Number(event.target.value))}
            />
          </label>
          <label className="field" style={{ flex: 1 }}>
            <span>Local</span>
            <select value={locationId} onChange={(event) => setLocationId(event.target.value)}>
              <option value="">— Escolha um local —</option>
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {"  ".repeat(option.depth)}
                  {option.name} ({option.full_code})
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="field">
          <span>Descrição (opcional)</span>
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Ex.: cabo trançado, 65W"
          />
        </label>
        {categories.length > 0 && (
          <div className="field">
            <span>Categorias</span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {categories.map((category) => (
                <button
                  key={category.id}
                  type="button"
                  className={selectedCategories.has(category.id) ? "catchip active" : "catchip"}
                  onClick={() => toggleCategory(category.id)}
                >
                  <span className="dot" style={{ background: category.color }} />
                  {category.name}
                </button>
              ))}
            </div>
          </div>
        )}
        <label className="field">
          <span>Notas (opcional)</span>
          <textarea
            rows={2}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Qualquer detalhe útil"
          />
        </label>
        {options.length === 0 && (
          <p className="muted">Cadastre um local primeiro para guardar itens nele.</p>
        )}
        {error && <p className="error">{error}</p>}
      </div>
      <div className="row">
        <button type="button" className="btn secondary" onClick={onClose}>
          Cancelar
        </button>
        <button type="button" className="btn primary" disabled={!canSave} onClick={submit}>
          Salvar
        </button>
      </div>
    </Modal>
  );
}
