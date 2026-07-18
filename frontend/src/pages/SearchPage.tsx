// Global search over items by name, description, or location.

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Item } from "../api/types";
import { ItemCard } from "../components/ItemCard";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Item[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length === 0) {
      setItems(null);
      return;
    }
    setLoading(true);
    const handle = setTimeout(() => {
      api
        .search(trimmed)
        .then((results) => setItems(results.items))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(handle);
  }, [query]);

  return (
    <>
      <h1 className="page-title">Buscar</h1>
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="O que você procura? Ex.: carregador"
        aria-label="Buscar itens"
      />
      <div style={{ marginTop: 18 }}>
        {loading && <p className="spinner">Buscando…</p>}
        {!loading && items === null && (
          <div className="empty">
            <h3>Encontre qualquer coisa</h3>
            <p>Digite o nome de um item para descobrir onde ele está guardado.</p>
          </div>
        )}
        {!loading && items !== null && items.length === 0 && (
          <div className="empty">
            <h3>Nenhum item encontrado</h3>
            <p>Tente outro termo ou verifique a grafia.</p>
          </div>
        )}
        {!loading && items && items.length > 0 && (
          <div className="stack">
            {items.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
