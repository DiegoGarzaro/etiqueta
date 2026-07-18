// Location path shown as "Escritório › Armário A › Gaveta 2".

import { Fragment } from "react";
import type { PathSegment } from "../api/types";

export function PathTrail({ segments }: { segments: PathSegment[] }) {
  return (
    <span className="path">
      {segments.map((segment, index) => (
        <Fragment key={segment.id}>
          {index > 0 && <span className="sep">›</span>}
          <span className={index === segments.length - 1 ? "last" : undefined}>
            {segment.name}
          </span>
        </Fragment>
      ))}
    </span>
  );
}
