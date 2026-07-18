// Select locations and print QR labels: on the SLP650 thermal printer
// (individual stickers, default) or as a sheet on a network printer.

import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { LOCATION_TYPE_LABELS, type LocationTreeNode } from "../api/types";
import { QrCode } from "../components/QrCode";
import { flattenTree, type FlatLocation } from "../utils/tree";

/** The URL a printed QR points to; scanning it opens the location.
 * INV_PUBLIC_BASE_URL (when configured) wins over the browser's origin so
 * labels are identical no matter which address they were printed from. */
function locationUrl(id: string, publicBase: string | null): string {
  return `${publicBase ?? window.location.origin}/locais/${id}`;
}

export default function LabelsPage() {
  const [params] = useSearchParams();
  const preselect = params.get("location");
  const [tree, setTree] = useState<LocationTreeNode[] | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [printer, setPrinter] = useState<"thermal" | "network">("thermal");
  const [printing, setPrinting] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [publicBase, setPublicBase] = useState<string | null>(null);

  useEffect(() => {
    api.getConfig().then((config) => setPublicBase(config.public_base_url)).catch(() => {});
  }, []);

  useEffect(() => {
    api.getTree().then((data) => {
      setTree(data);
      const all = flattenTree(data);
      setSelected(new Set(preselect ? [preselect] : all.map((location) => location.id)));
    });
  }, [preselect]);

  const flat = useMemo<FlatLocation[]>(() => (tree ? flattenTree(tree) : []), [tree]);
  const chosen = flat.filter((location) => selected.has(location.id));

  const toggle = (id: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handlePrint = async () => {
    if (printer === "network") {
      window.print();
      return;
    }
    const total = chosen.length;
    if (!window.confirm(`Imprimir ${total} etiqueta(s) na impressora térmica?`)) return;
    setPrinting(true);
    setFeedback(null);
    let done = 0;
    try {
      for (const location of chosen) {
        await api.printLocationLabel(location.id);
        done += 1;
      }
      setFeedback({ ok: true, text: `${done} etiqueta(s) enviada(s) para a impressora.` });
    } catch (err) {
      const detail =
        err instanceof ApiError ? err.message : "Falha ao falar com o servidor de impressão.";
      setFeedback({
        ok: false,
        text: `Impressas ${done} de ${total}. Falhou em "${chosen[done].full_code}": ${detail}`,
      });
    } finally {
      setPrinting(false);
    }
  };

  if (tree === null) return <p className="spinner">Carregando…</p>;

  if (flat.length === 0) {
    return (
      <div className="empty">
        <h3>Nenhum local para etiquetar</h3>
        <p>
          Crie locais em <Link to="/locais">Locais</Link> para gerar etiquetas.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="noprint">
        <Link to="/locais" className="muted">
          ← Locais
        </Link>
        <h1 className="page-title">Etiquetas</h1>
        <p className="muted" style={{ marginTop: -6, marginBottom: 14 }}>
          Escolha os locais, imprima e cole cada etiqueta no móvel. Escanear o QR abre o
          conteúdo do local. A térmica imprime uma etiqueta adesiva por local (
          <Link to="/impressora">pré-visualização</Link>); a impressora de rede imprime a
          folha abaixo pelo navegador.
        </p>
        {feedback && (
          <p
            className="error"
            style={
              feedback.ok
                ? { marginBottom: 14, background: "var(--pine-tint)", color: "var(--graphite)" }
                : { marginBottom: 14 }
            }
          >
            {feedback.text}
          </p>
        )}

        <div
          style={{
            display: "flex",
            gap: 10,
            marginBottom: 16,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            className="btn secondary"
            onClick={() => setSelected(new Set(flat.map((location) => location.id)))}
          >
            Selecionar tudo
          </button>
          <button type="button" className="btn secondary" onClick={() => setSelected(new Set())}>
            Limpar
          </button>
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginLeft: "auto" }}>
            <select
              value={printer}
              onChange={(event) => setPrinter(event.target.value as "thermal" | "network")}
              aria-label="Impressora"
              style={{ width: "auto", padding: "10px 13px" }}
            >
              <option value="thermal">Térmica (SLP650)</option>
              <option value="network">Impressora de rede</option>
            </select>
            <button
              type="button"
              className="btn primary"
              disabled={chosen.length === 0 || printing}
              onClick={() => void handlePrint()}
              style={{ whiteSpace: "nowrap" }}
            >
              {printing ? "Imprimindo…" : `Imprimir (${chosen.length})`}
            </button>
          </div>
        </div>

        <div className="stack" style={{ gap: 2 }}>
          {flat.map((location) => (
            <label
              key={location.id}
              className="tree-node"
              style={{ paddingLeft: 10 + location.depth * 20, cursor: "pointer" }}
            >
              <input
                type="checkbox"
                checked={selected.has(location.id)}
                onChange={() => toggle(location.id)}
                style={{ width: "auto" }}
              />
              <span>{location.name}</span>
              <span className="count">{location.full_code}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="labels-sheet">
        {chosen.map((location) => (
          <div key={location.id} className="label">
            <QrCode text={locationUrl(location.id, publicBase)} size={92} />
            <div className="label-body">
              <div className="label-code">{location.full_code}</div>
              <div className="label-name">{location.name}</div>
              <div className="label-type">{LOCATION_TYPE_LABELS[location.type]}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
