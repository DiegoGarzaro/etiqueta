// Thermal printing on the SLP650: location labels, visitor badges, and images.

import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, labelPreviewUrl } from "../api/client";
import type { LocationTreeNode, PrinterHealth } from "../api/types";
import { flattenTree, type FlatLocation } from "../utils/tree";

/** Human message for a print call that failed. */
function printErrorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  return "Não foi possível falar com o servidor de impressão.";
}

export default function PrintPage() {
  const [health, setHealth] = useState<PrinterHealth | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [tree, setTree] = useState<LocationTreeNode[] | null>(null);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  // Location label section.
  const [locationId, setLocationId] = useState("");
  const [locationCopies, setLocationCopies] = useState(1);

  // Visitor badge section.
  const [badgeName, setBadgeName] = useState("");
  const [badgeCompany, setBadgeCompany] = useState("");
  const [badgeQr, setBadgeQr] = useState("");
  const [badgeCopies, setBadgeCopies] = useState(1);

  // Image section.
  const fileRef = useRef<HTMLInputElement>(null);
  const [imageCopies, setImageCopies] = useState(1);

  useEffect(() => {
    api
      .printerHealth()
      .then((data) => setHealth(data))
      .catch((err) => setHealthError(printErrorMessage(err)));
    api.getTree().then(setTree);
  }, []);

  const flat = useMemo<FlatLocation[]>(() => (tree ? flattenTree(tree) : []), [tree]);

  useEffect(() => {
    if (!locationId && flat.length > 0) setLocationId(flat[0].id);
  }, [flat, locationId]);

  const runPrint = async (confirmText: string, action: () => Promise<unknown>) => {
    if (!window.confirm(confirmText)) return;
    setBusy(true);
    setFeedback(null);
    try {
      await action();
      setFeedback({ ok: true, text: "Enviado para a impressora." });
    } catch (err) {
      setFeedback({ ok: false, text: printErrorMessage(err) });
    } finally {
      setBusy(false);
    }
  };

  const handleBadge = (event: FormEvent) => {
    event.preventDefault();
    void runPrint(`Imprimir ${badgeCopies}x crachá para "${badgeName}"?`, () =>
      api.printBadge({
        name: badgeName,
        company: badgeCompany || undefined,
        qr_data: badgeQr || undefined,
        copies: badgeCopies,
      }),
    );
  };

  const handleImage = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    void runPrint(`Imprimir ${imageCopies}x a imagem "${file.name}"?`, () =>
      api.printImage(file, imageCopies),
    );
  };

  const selected = flat.find((location) => location.id === locationId);

  return (
    <>
      <Link to="/etiquetas" className="muted">
        ← Etiquetas
      </Link>
      <h1 className="page-title">Impressora térmica</h1>
      <p className="muted" style={{ marginTop: -6, marginBottom: 14 }}>
        Etiquetas em crachá SLP-NWB (70×54 mm) na Seiko SLP650.
      </p>

      {health === null && healthError === null && <p className="spinner">Verificando impressora…</p>}
      {health && (
        <p className="muted" style={{ marginBottom: 18 }}>
          {health.ok ? "✓ Impressora pronta." : "✗ Servidor ativo, mas a impressora não responde."}
        </p>
      )}
      {healthError && (
        <p className="error" style={{ marginBottom: 18 }}>
          {healthError}
        </p>
      )}

      {feedback && (
        <p
          className="error"
          style={
            feedback.ok
              ? { background: "var(--pine-tint)", color: "var(--graphite)", marginBottom: 18 }
              : { marginBottom: 18 }
          }
        >
          {feedback.text}
        </p>
      )}

      <section style={{ marginBottom: 32 }}>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          Etiqueta de local
        </h2>
        <p className="muted" style={{ marginTop: -6 }}>
          A etiqueta é gerada pelo app (código, nome e QR) e impressa exatamente como na
          pré-visualização.
        </p>
        {flat.length === 0 ? (
          <p className="muted">
            Nenhum local cadastrado. Crie locais em <Link to="/locais">Locais</Link>.
          </p>
        ) : (
          <>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
              <select
                value={locationId}
                onChange={(event) => setLocationId(event.target.value)}
                style={{ maxWidth: 420 }}
              >
                {flat.map((location) => (
                  <option key={location.id} value={location.id}>
                    {" ".repeat(location.depth * 2)}
                    {location.full_code} — {location.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min={1}
                max={100}
                value={locationCopies}
                onChange={(event) => setLocationCopies(Number(event.target.value) || 1)}
                style={{ width: 80 }}
                aria-label="Cópias"
              />
              <button
                type="button"
                className="btn primary"
                disabled={busy || !locationId}
                onClick={() =>
                  void runPrint(
                    `Imprimir ${locationCopies}x etiqueta de "${selected?.full_code}"?`,
                    () => api.printLocationLabel(locationId, locationCopies),
                  )
                }
              >
                Imprimir etiqueta
              </button>
            </div>
            {locationId && (
              <img
                key={locationId}
                src={labelPreviewUrl(locationId)}
                alt={`Pré-visualização da etiqueta de ${selected?.name ?? "local"}`}
                style={{
                  display: "block",
                  marginTop: 14,
                  width: 375,
                  maxWidth: "100%",
                  border: "1px solid var(--line, #ccc)",
                }}
              />
            )}
          </>
        )}
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          Crachá de visitante
        </h2>
        <form onSubmit={handleBadge} style={{ display: "grid", gap: 10, maxWidth: 420 }}>
          <input
            required
            maxLength={80}
            placeholder="Nome"
            value={badgeName}
            onChange={(event) => setBadgeName(event.target.value)}
          />
          <input
            placeholder="Empresa (opcional)"
            value={badgeCompany}
            onChange={(event) => setBadgeCompany(event.target.value)}
          />
          <input
            type="url"
            placeholder="URL do QR (opcional)"
            value={badgeQr}
            onChange={(event) => setBadgeQr(event.target.value)}
          />
          <div style={{ display: "flex", gap: 10 }}>
            <input
              type="number"
              min={1}
              max={100}
              value={badgeCopies}
              onChange={(event) => setBadgeCopies(Number(event.target.value) || 1)}
              style={{ width: 80 }}
              aria-label="Cópias"
            />
            <button type="submit" className="btn primary" disabled={busy || !badgeName}>
              Imprimir crachá
            </button>
          </div>
        </form>
      </section>

      <section>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          Imagem
        </h2>
        <p className="muted" style={{ marginTop: -6 }}>
          PNG ou JPEG (máx. 20 MiB), ajustada automaticamente ao crachá. Prefira preto puro
          sobre branco — traços finos e cinzas imprimem mal.
        </p>
        <input ref={fileRef} type="file" accept="image/png,image/jpeg" hidden onChange={handleImage} />
        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <input
            type="number"
            min={1}
            max={100}
            value={imageCopies}
            onChange={(event) => setImageCopies(Number(event.target.value) || 1)}
            style={{ width: 80 }}
            aria-label="Cópias"
          />
          <button
            type="button"
            className="btn secondary"
            disabled={busy}
            onClick={() => fileRef.current?.click()}
          >
            Escolher imagem e imprimir
          </button>
        </div>
      </section>
    </>
  );
}
