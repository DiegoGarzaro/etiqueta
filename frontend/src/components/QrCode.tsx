// Renders a QR code (always dark-on-white for reliable scanning).

import QRCode from "qrcode";
import { useEffect, useState } from "react";

interface Props {
  text: string;
  size?: number;
}

export function QrCode({ text, size = 120 }: Props) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    let active = true;
    QRCode.toDataURL(text, {
      margin: 1,
      width: size * 2,
      color: { dark: "#1F2421", light: "#FFFFFF" },
    })
      .then((url) => {
        if (active) setSrc(url);
      })
      .catch(() => {
        if (active) setSrc("");
      });
    return () => {
      active = false;
    };
  }, [text, size]);

  return (
    <img
      src={src}
      width={size}
      height={size}
      alt=""
      style={{ display: "block", width: size, height: size, background: "#fff", borderRadius: 4 }}
    />
  );
}
