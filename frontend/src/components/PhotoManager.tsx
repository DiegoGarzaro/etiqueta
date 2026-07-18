// Shows a photo grid with add (camera/upload) and delete controls.

import { useState, type ChangeEvent } from "react";
import { ApiError } from "../api/client";
import type { Photo } from "../api/types";

interface Props {
  photos: Photo[];
  onAdd: (file: File) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function PhotoManager({ photos, onAdd, onDelete }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await onAdd(file);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível enviar a foto.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="photo-grid">
        {photos.map((photo) => (
          <div key={photo.id} className="photo-thumb">
            <a href={photo.url} target="_blank" rel="noreferrer">
              <img src={photo.thumb_url} alt="" loading="lazy" />
            </a>
            <button
              type="button"
              className="photo-remove"
              aria-label="Remover foto"
              onClick={() => onDelete(photo.id)}
            >
              ×
            </button>
          </div>
        ))}
        <label className="photo-add" aria-label="Adicionar foto">
          +
          <input
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={handleFile}
          />
        </label>
      </div>
      {busy && <p className="muted">Enviando foto…</p>}
      {error && <p className="error" style={{ marginTop: 8 }}>{error}</p>}
    </div>
  );
}
