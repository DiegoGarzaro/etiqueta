// Ajustes: backup/restore, printer status, and the access PIN.

import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, exportUrls } from "../api/client";
import type { AuthStatus, ImportResult, PrinterStatus } from "../api/types";

export default function BackupPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);

  const [printer, setPrinter] = useState<PrinterStatus | null>(null);
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [currentPin, setCurrentPin] = useState("");
  const [newPin, setNewPin] = useState("");
  const [pinFeedback, setPinFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [savingPin, setSavingPin] = useState(false);

  useEffect(() => {
    api.printerStatus().then(setPrinter).catch(() => setPrinter(null));
    api.authStatus().then(setAuth).catch(() => setAuth(null));
  }, []);

  const handlePinSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSavingPin(true);
    setPinFeedback(null);
    try {
      await api.changePin({
        current_pin: auth?.auth_required ? currentPin : undefined,
        new_pin: newPin,
      });
      setCurrentPin("");
      setNewPin("");
      setAuth({ auth_required: true, authenticated: true });
      setPinFeedback({ ok: true, text: "PIN salvo. Os outros dispositivos precisarão entrar de novo." });
    } catch (err) {
      setPinFeedback({
        ok: false,
        text: err instanceof ApiError ? err.message : "Não foi possível salvar o PIN.",
      });
    } finally {
      setSavingPin(false);
    }
  };

  const handleLogout = async () => {
    await api.logout();
    window.location.reload();
  };

  const handleImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (
      !window.confirm(
        "Importar substitui TODO o inventário atual pelos dados do arquivo. Continuar?",
      )
    ) {
      return;
    }
    setImporting(true);
    setError(null);
    setResult(null);
    try {
      const data = JSON.parse(await file.text());
      setResult(await api.importInventory(data));
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else if (err instanceof SyntaxError) setError("Arquivo JSON inválido.");
      else setError("Não foi possível importar o arquivo.");
    } finally {
      setImporting(false);
    }
  };

  const today = new Date().toISOString().slice(0, 10);

  return (
    <>
      <h1 className="page-title">Ajustes</h1>

      <section style={{ marginBottom: 32 }}>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          Backup
        </h2>
        <p className="muted" style={{ marginTop: -6 }}>
          Baixe uma cópia de todo o inventário. O JSON pode ser reimportado; o CSV é uma
          lista de itens para abrir em planilhas.
        </p>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
          <a className="btn primary" href={exportUrls.json} download={`inventario-${today}.json`}>
            Exportar JSON
          </a>
          <a className="btn secondary" href={exportUrls.csv}>
            Exportar CSV (itens)
          </a>
        </div>
        <p className="muted" style={{ marginTop: 10 }}>
          As fotos são guardadas como arquivos em <code>backend/media/</code> — copie essa
          pasta junto com o JSON para um backup completo.
        </p>
      </section>

      <section>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          Restaurar
        </h2>
        <p className="muted" style={{ marginTop: -6 }}>
          Importar um arquivo JSON <strong>substitui todo o inventário atual</strong>.
        </p>
        <input ref={fileRef} type="file" accept="application/json,.json" hidden onChange={handleImport} />
        <button
          type="button"
          className="btn secondary"
          disabled={importing}
          onClick={() => fileRef.current?.click()}
          style={{ marginTop: 12 }}
        >
          {importing ? "Importando…" : "Importar JSON"}
        </button>

        {result && (
          <p className="error" style={{ marginTop: 14, background: "var(--pine-tint)", color: "var(--graphite)" }}>
            Restaurado: {result.locations} locais, {result.items} itens,{" "}
            {result.categories} categorias, {result.photos} fotos.
          </p>
        )}
        {error && (
          <p className="error" style={{ marginTop: 14 }}>
            {error}
          </p>
        )}
      </section>

      <section style={{ marginTop: 32 }}>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          Impressora térmica
        </h2>
        {printer === null ? (
          <p className="muted" style={{ marginTop: -6 }}>
            Não foi possível consultar o estado da impressora.
          </p>
        ) : (
          <p className="muted" style={{ marginTop: -6 }}>
            Servidor: <code>{printer.base_url}</code> · Chave de API:{" "}
            {printer.key_configured ? "configurada" : "não configurada"} ·{" "}
            {printer.ok === true
              ? "✓ impressora pronta"
              : printer.ok === false
                ? "✗ impressora não responde"
                : `✗ ${printer.error}`}
          </p>
        )}
        <p className="muted">
          Endereço e chave são definidos no arquivo <code>.env</code> do servidor
          (<code>SLP650_BASE_URL</code> / <code>SLP650_API_KEY</code>) — a chave nunca
          aparece aqui. Imprimir: <Link to="/impressora">Impressora térmica</Link>.
        </p>
      </section>

      <section style={{ marginTop: 32 }}>
        <h2 className="page-title" style={{ fontSize: "1.15rem" }}>
          PIN de acesso
        </h2>
        <p className="muted" style={{ marginTop: -6 }}>
          {auth?.auth_required
            ? "O app exige PIN. Alterar o PIN desconecta todos os outros dispositivos."
            : "Sem PIN o app fica aberto para qualquer pessoa na rede. Defina um PIN de 4 a 8 dígitos."}
        </p>
        <form onSubmit={handlePinSubmit} style={{ display: "grid", gap: 10, maxWidth: 280 }}>
          {auth?.auth_required && (
            <input
              type="password"
              inputMode="numeric"
              placeholder="PIN atual"
              minLength={4}
              maxLength={8}
              required
              value={currentPin}
              onChange={(event) => setCurrentPin(event.target.value.replace(/\D/g, ""))}
            />
          )}
          <input
            type="password"
            inputMode="numeric"
            placeholder="Novo PIN (4-8 dígitos)"
            minLength={4}
            maxLength={8}
            required
            value={newPin}
            onChange={(event) => setNewPin(event.target.value.replace(/\D/g, ""))}
          />
          <div style={{ display: "flex", gap: 10 }}>
            <button type="submit" className="btn primary" disabled={savingPin || newPin.length < 4}>
              {savingPin ? "Salvando…" : auth?.auth_required ? "Alterar PIN" : "Definir PIN"}
            </button>
            {auth?.auth_required && (
              <button type="button" className="btn secondary" onClick={handleLogout}>
                Sair
              </button>
            )}
          </div>
        </form>
        {pinFeedback && (
          <p
            className="error"
            style={
              pinFeedback.ok
                ? { marginTop: 14, background: "var(--pine-tint)", color: "var(--graphite)" }
                : { marginTop: 14 }
            }
          >
            {pinFeedback.text}
          </p>
        )}
      </section>
    </>
  );
}
