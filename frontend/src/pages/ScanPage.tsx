// Scan a location's QR label with the camera and open it.

import { BrowserQRCodeReader, type IScannerControls } from "@zxing/browser";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ScanIcon } from "../components/Icons";

/** Pull a location id out of a scanned URL or raw UUID. */
function extractLocationId(text: string): string | null {
  try {
    const url = new URL(text);
    const match = url.pathname.match(/locais\/([^/]+)/);
    if (match) return match[1];
  } catch {
    // not a URL; fall through to a bare UUID check.
  }
  const uuid = text.match(/[0-9a-fA-F-]{36}/);
  return uuid ? uuid[0] : null;
}

export default function ScanPage() {
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanning) return;
    // Browsers only expose the camera on secure contexts (https or localhost);
    // opening the app via http://<ip> makes navigator.mediaDevices undefined.
    if (!window.isSecureContext || !navigator.mediaDevices) {
      setError(
        "O navegador bloqueia a câmera em páginas sem HTTPS. Abra o app por um " +
          "endereço https para escanear aqui — ou escaneie a etiqueta com o app de " +
          "Câmera do celular, que abre o local direto no navegador.",
      );
      setScanning(false);
      return;
    }
    const reader = new BrowserQRCodeReader();
    let controls: IScannerControls | undefined;
    let stopped = false;

    reader
      .decodeFromVideoDevice(undefined, videoRef.current ?? undefined, (result, _err, ctrl) => {
        controls = ctrl;
        if (stopped || !result) return;
        stopped = true;
        ctrl.stop();
        const id = extractLocationId(result.getText());
        if (id) navigate(`/locais/${id}`);
        else setError("QR não reconhecido. Tente outro código.");
      })
      .catch(() => setError("Não foi possível acessar a câmera. Verifique as permissões."));

    return () => {
      stopped = true;
      controls?.stop();
    };
  }, [scanning, navigate]);

  return (
    <>
      <h1 className="page-title">Escanear</h1>

      {!scanning && (
        <div className="empty">
          <div style={{ color: "var(--pine)", marginBottom: 12 }}>
            <ScanIcon size={40} />
          </div>
          <h3>Aponte para a etiqueta</h3>
          <p>Escaneie o QR de um armário, gaveta ou caixa para abrir o que há dentro.</p>
          <button type="button" className="btn primary" onClick={() => setScanning(true)}>
            Ativar câmera
          </button>
        </div>
      )}

      {scanning && (
        <div style={{ maxWidth: 420, margin: "0 auto" }}>
          <div
            style={{
              position: "relative",
              aspectRatio: "1",
              borderRadius: "var(--r-lg)",
              overflow: "hidden",
              background: "#000",
            }}
          >
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <video
              ref={videoRef}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              muted
              playsInline
            />
            <div
              style={{
                position: "absolute",
                inset: "18%",
                border: "3px solid rgba(255,255,255,0.85)",
                borderRadius: "var(--r-md)",
              }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "center", marginTop: 14 }}>
            <button type="button" className="btn secondary" onClick={() => setScanning(false)}>
              Parar
            </button>
          </div>
        </div>
      )}

      {error && (
        <p className="error" style={{ marginTop: 16 }}>
          {error} Ou navegue pela aba <Link to="/locais">Locais</Link>.
        </p>
      )}
    </>
  );
}
