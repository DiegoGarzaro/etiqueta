// Browse items by category and manage the category list.

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Category, Item } from "../api/types";
import { CategoryChip } from "../components/CategoryChip";
import { ItemCard } from "../components/ItemCard";

const PRESET_COLORS = [
  "#2F6B4F",
  "#3E7CA6",
  "#B27B2E",
  "#7A5AA0",
  "#A6484B",
  "#4E7A4A",
  "#8A6D3B",
  "#5B6670",
];

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [selected, setSelected] = useState<Category | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState(PRESET_COLORS[0]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api.listCategories().then(setCategories);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const selectCategory = async (category: Category) => {
    setSelected(category);
    setItems(await api.listItems({ categoryId: category.id }));
  };

  const createCategory = async () => {
    setError(null);
    try {
      await api.createCategory({ name: newName.trim(), color: newColor });
      setNewName("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível criar a categoria.");
    }
  };

  return (
    <>
      <h1 className="page-title">Categorias</h1>

      <div className="field" style={{ marginBottom: 20 }}>
        <span>Nova categoria</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <input
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            placeholder="Ex.: Ferramentas"
            style={{ flex: 1, minWidth: 160 }}
          />
          <div style={{ display: "flex", gap: 6 }}>
            {PRESET_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                aria-label={`Cor ${color}`}
                onClick={() => setNewColor(color)}
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: color,
                  border: newColor === color ? "2px solid var(--graphite)" : "1px solid var(--line)",
                  cursor: "pointer",
                }}
              />
            ))}
          </div>
          <button
            type="button"
            className="btn primary"
            disabled={newName.trim().length === 0}
            onClick={createCategory}
          >
            Criar
          </button>
        </div>
        {error && <p className="error" style={{ marginTop: 8 }}>{error}</p>}
      </div>

      {categories.length === 0 ? (
        <div className="empty">
          <h3>Nenhuma categoria ainda</h3>
          <p>Crie categorias para agrupar itens que se espalham pela casa.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {categories.map((category) => (
            <CategoryChip
              key={category.id}
              category={category}
              active={selected?.id === category.id}
              showCount
              onClick={() => selectCategory(category)}
            />
          ))}
        </div>
      )}

      {selected && (
        <div style={{ marginTop: 24 }}>
          <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
            {selected.name}
          </h2>
          {items.length === 0 ? (
            <p className="muted">Nenhum item nesta categoria ainda.</p>
          ) : (
            <div className="stack">
              {items.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
