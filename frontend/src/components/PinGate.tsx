// Lock screen: blocks the app until the access PIN is entered.
// The backend enforces the PIN on every /api and /media request; this
// component is just the door. The current URL is kept, so scanning a
// location QR lands on that location right after unlocking.

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError, setUnauthorizedHandler } from "../api/client";

type GateState = "loading" | "locked" | "open";

export function PinGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GateState>("loading");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    api
      .authStatus()
      .then((status) =>
        setState(!status.auth_required || status.authenticated ? "open" : "locked"),
      )
      .catch(() => setState("open")); // Backend down: let the app show its own errors.
    setUnauthorizedHandler(() => setState("locked"));
    return () => setUnauthorizedHandler(null);
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setChecking(true);
    setError(null);
    try {
      await api.login(pin);
      setPin("");
      setState("open");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível verificar o PIN.");
    } finally {
      setChecking(false);
    }
  };

  if (state === "loading") return <p className="spinner">Carregando…</p>;

  if (state === "locked") {
    return (
      <div
        style={{
          minHeight: "100dvh",
          display: "grid",
          placeItems: "center",
          padding: 24,
        }}
      >
        <form onSubmit={handleSubmit} style={{ textAlign: "center", maxWidth: 280 }}>
          <span className="brand" style={{ fontSize: "1.6rem" }}>
            Etiqueta<span className="dot">.</span>
          </span>
          <p className="muted" style={{ margin: "10px 0 18px" }}>
            Digite o PIN para acessar o inventário.
          </p>
          <input
            type="password"
            inputMode="numeric"
            pattern="\d{4,8}"
            minLength={4}
            maxLength={8}
            autoFocus
            required
            value={pin}
            onChange={(event) => setPin(event.target.value.replace(/\D/g, ""))}
            aria-label="PIN"
            style={{
              textAlign: "center",
              fontSize: "1.5rem",
              letterSpacing: "0.5em",
              width: "100%",
            }}
          />
          {error && (
            <p className="error" style={{ marginTop: 12 }}>
              {error}
            </p>
          )}
          <button
            type="submit"
            className="btn primary"
            disabled={checking || pin.length < 4}
            style={{ marginTop: 14, width: "100%" }}
          >
            {checking ? "Verificando…" : "Entrar"}
          </button>
        </form>
      </div>
    );
  }

  return <>{children}</>;
}
