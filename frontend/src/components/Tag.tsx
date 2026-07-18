// The Etiqueta — a location code rendered as a physical-looking tag.

export function Tag({ code, large = false }: { code: string; large?: boolean }) {
  return <span className={large ? "tag lg" : "tag"}>{code}</span>;
}
